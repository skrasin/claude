"""Обработка приглашений из личного чата владельца."""

import datetime as dt
import json
import logging
from pathlib import Path
import re

from common import icloud, invitation_ai, tg

CONFIG_PATH = Path(tg.BOT_DIR) / "calendar.local.json"
log = logging.getLogger("listener.calendar")
QUESTIONS = {
    "time": "Уточни дату и время начала.",
    "choice": "Какое из событий записать? Укажи название, дату и время.",
    "content": "Пришли текст или скриншот приглашения.",
}


def _field(value, limit):
    if not isinstance(value, str):
        return ""
    return " ".join(value.split())[:limit]


def _details(event, now):
    title = _field(event.get("title"), 220)
    if not title:
        raise ValueError("missing title")
    start = invitation_ai.parse_time(event.get("start"))
    default_duration = event.get("end") is None
    end = start + dt.timedelta(hours=1) if default_duration else invitation_ai.parse_time(event["end"])
    if start <= now or end <= start:
        raise ValueError("invalid time range")
    return title, start, end, default_duration


class CalendarInvitations:
    def __init__(self, bot, state):
        self.bot = bot
        self.state = state
        self._config = None
        self._services = None
        self._invalid_config_warned = False

    def _clients(self):
        # Новый файл настроек подхватывается при следующем сообщении.
        try:
            with CONFIG_PATH.open(encoding="utf-8") as source:
                config = json.load(source)
            if not isinstance(config, dict):
                raise ValueError
            if config.get("enabled") is not True:
                return None
            names = ("openai_api_key", "icloud_account", "icloud_app_password")
            if any(not isinstance(config.get(name), str) or not config[name].strip() for name in names):
                raise ValueError
        except FileNotFoundError:
            return None
        except (OSError, ValueError):
            if not self._invalid_config_warned:
                log.warning("проверьте формат и обязательные поля calendar.local.json")
                self._invalid_config_warned = True
            return None
        self._invalid_config_warned = False
        if config != self._config:
            self._services = (
                invitation_ai.InvitationExtractor(
                    config["openai_api_key"].strip(), config.get("model") or "gpt-4.1-mini", tg.BOT_DIR,
                ),
                icloud.ICloudCalendar(
                    config["icloud_account"].strip(), config["icloud_app_password"].strip(),
                    config.get("calendar_name") or "Calendar",
                ),
            )
            self._config = config
        return self._services

    def _send(self, text, entry):
        return self.bot.send(text, chat_id=entry["chat_id"], parse_mode=None, reply_to=entry["message_id"])

    def _clarify(self, question, entry, entries, drafts):
        sent = self._send(question + " Ответь на это сообщение.", entry)
        if sent and sent.get("message_id"):
            if len(drafts) >= 8:
                del drafts[next(iter(drafts))]
            drafts[str(sent["message_id"])] = entries

    def handle(self, entry, msg, skipped):
        clients = self._clients()
        if clients is None:
            return
        extractor, calendar = clients
        drafts = self.state.setdefault("calendar_drafts", {})
        reply_id = str((msg.get("reply_to_message") or {}).get("message_id", ""))
        prior = drafts.get(reply_id)
        # Сохраняем исходное приглашение и два последних уточнения.
        entries = [prior[0]] + prior[1:][-2:] + [entry] if prior else [entry]
        if not entry.get("text") and not entry.get("files") and skipped:
            self._clarify("Пришли текст или скриншот приглашения.", entry, entries, drafts)
        else:
            try:
                event = extractor.extract(entries)
                self._handle_result(event, calendar, entry, entries, drafts, prior)
            except (invitation_ai.InvitationError, icloud.CalendarError) as exc:
                log.warning("календарь: %s", exc)
                self._send("Не удалось добавить приглашение в календарь. {}. "
                           "Попробуй переслать его ещё раз.".format(exc), entry)
                return
            except OSError:
                log.warning("календарь: не удалось прочитать вложение")
                self._send("Не удалось прочитать вложение. Пришли его ещё раз или скопируй текст.", entry)
                return
        if prior:
            drafts.pop(reply_id, None)

    def _handle_result(self, event, calendar, entry, entries, drafts, prior):
        if event["kind"] == "other" and not prior:
            return
        if event["kind"] != "event":
            missing = _field(event.get("missing"), 30)
            question = QUESTIONS.get(missing, "Уточни название, дату и время события.")
            self._clarify(question, entry, entries, drafts)
            return
        try:
            title, start, end, default_duration = _details(event, dt.datetime.now(invitation_ai.MSK))
        except ValueError:
            self._clarify("Уточни дату и время предстоящего события.", entry, entries, drafts)
            return
        location = _field(event.get("location"), 380)
        original = entries[0]
        description = original.get("text", "").strip()[:2500]
        for link in original.get("links", [])[:3]:
            if re.match(r"^https?://\S+$", link) and link not in description:
                description = (description + "\n" + link[:700]).strip()
        created = calendar.add(title, start, end, location, description)
        day = start.astimezone(invitation_ai.MSK).strftime("%d.%m.%Y, %H:%M МСК")
        text = "{} «{}» — {}.".format("Записал" if created else "Уже есть в календаре", title, day)
        if location:
            text += "\n" + location
        if created and default_duration:
            text += "\nПоставил на час."
        self._send(text, entry)
