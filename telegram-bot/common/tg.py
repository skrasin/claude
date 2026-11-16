"""Общая библиотека для всех задач бота: Telegram Bot API на стандартной библиотеке.

Работает на Python 3.8+ (встроенный python3 в Synology DSM 7, без pip).

    import os, sys
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    from common import tg

    bot = tg.Bot.from_config()
    bot.send("<b>Привет</b>")              # владельцу из config.json
    bot.send("текст", chat_id=12345)       # кому-то ещё

    tg.run_task("моя-задача", main)        # при исключении владелец получит предупреждение
"""

import html
import json
import os
import socket
import sys
import time
import traceback
import urllib.error
import urllib.parse
import urllib.request

BOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.environ.get("BOT_CONFIG") or os.path.join(BOT_DIR, "config.json")
DATA_DIR = os.path.join(BOT_DIR, "data")
API_BASE = "https://api.telegram.org"
MAX_LEN = 4096  # предел длины одного сообщения в Telegram


class TelegramError(Exception):
    def __init__(self, description, code=None, retry_after=None):
        super().__init__(description)
        self.code = code
        self.retry_after = retry_after


def load_config(path=None):
    path = path or CONFIG_PATH
    if not os.path.exists(path):
        sys.exit("Нет файла настроек {}. Скопируйте config.example.json в config.json "
                 "и впишите токен (chmod 600 config.json).".format(path))
    with open(path, encoding="utf-8") as f:
        cfg = json.load(f)
    if "owner_chat_id" not in cfg and "chat_id" in cfg:  # совместимость со старым форматом
        cfg["owner_chat_id"] = cfg["chat_id"]
    return cfg


def esc(s):
    """Экранирование для parse_mode=HTML: & < >."""
    return html.escape(str(s), quote=False)


def split_text(text, limit=MAX_LEN):
    """Режет длинный текст по абзацам/строкам, чтобы не превысить предел Telegram.

    Теги HTML в наших сообщениях не переходят через строку, поэтому резать по \\n безопасно.
    """
    if len(text) <= limit:
        return [text]
    parts, cur = [], ""
    for line in text.split("\n"):
        while len(line) > limit:  # одна гигантская строка
            if cur:
                parts.append(cur)
                cur = ""
            parts.append(line[:limit])
            line = line[limit:]
        candidate = line if not cur else cur + "\n" + line
        if len(candidate) > limit:
            parts.append(cur)
            cur = line
        else:
            cur = candidate
    if cur:
        parts.append(cur)
    return [p for p in parts if p.strip()]


class Bot:
    def __init__(self, token, owner_chat_id=None, api_base=None):
        self.token = token
        self.owner = owner_chat_id
        self.api_base = (api_base or API_BASE).rstrip("/")

    @classmethod
    def from_config(cls, cfg=None):
        cfg = cfg or load_config()
        return cls(cfg["token"], cfg.get("owner_chat_id"), cfg.get("api_base"))

    # ------------------------------------------------------------ базовый вызов

    def call(self, method, params=None, timeout=30, retries=3):
        """Вызов метода Bot API. Повторяет при сетевых сбоях, 429 и 5xx.

        Токен в тексте ошибок не появляется: исключения формируются здесь.
        """
        url = "{}/bot{}/{}".format(self.api_base, self.token, method)
        body = json.dumps(params or {}).encode("utf-8")
        last = None
        for attempt in range(retries + 1):
            req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=timeout) as r:
                    data = json.loads(r.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                try:
                    data = json.loads(e.read().decode("utf-8"))
                except Exception:
                    data = {"ok": False, "error_code": e.code, "description": "HTTP {}".format(e.code)}
            except (urllib.error.URLError, socket.timeout, ConnectionError, OSError) as e:
                reason = getattr(e, "reason", e)
                last = TelegramError("сеть: {}".format(reason))
                if attempt < retries:
                    time.sleep(min(2 ** attempt * 2, 30))
                    continue
                raise last
            if data.get("ok"):
                return data.get("result")
            code = data.get("error_code")
            retry_after = (data.get("parameters") or {}).get("retry_after")
            last = TelegramError(data.get("description", "ошибка Telegram"), code, retry_after)
            if attempt < retries and (code == 429 or (code or 0) >= 500):
                time.sleep(retry_after or min(2 ** attempt * 2, 30))
                continue
            raise last
        raise last

    # ------------------------------------------------------------ удобные методы

    def me(self):
        return self.call("getMe")

    def send(self, text, chat_id=None, parse_mode="HTML", silent=False, preview=False, reply_to=None):
        """Отправить текст (длинный режется на части). Возвращает последнее сообщение."""
        chat_id = chat_id or self.owner
        if not chat_id:
            raise TelegramError("не указан chat_id и нет owner_chat_id в config.json")
        result = None
        for i, part in enumerate(split_text(text)):
            params = {
                "chat_id": chat_id,
                "text": part,
                "disable_notification": silent,
                "link_preview_options": {"is_disabled": not preview},
            }
            if parse_mode:
                params["parse_mode"] = parse_mode
            if reply_to and i == 0:
                params["reply_parameters"] = {"message_id": reply_to, "allow_sending_without_reply": True}
            try:
                result = self.call("sendMessage", params)
            except TelegramError as e:
                # Сломанная разметка не должна глушить сообщение: шлём как обычный текст.
                if parse_mode and e.code == 400 and "parse" in str(e).lower():
                    params.pop("parse_mode")
                    result = self.call("sendMessage", params)
                else:
                    raise
        return result

    def react(self, chat_id, message_id, emoji="👍"):
        """Поставить реакцию на сообщение (тихое «принято»). Ошибки не критичны."""
        try:
            self.call("setMessageReaction", {
                "chat_id": chat_id, "message_id": message_id,
                "reaction": [{"type": "emoji", "emoji": emoji}],
            }, retries=0)
        except TelegramError:
            pass

    def get_updates(self, offset=None, timeout=0, allowed_updates=None):
        params = {"timeout": timeout}
        if offset is not None:
            params["offset"] = offset
        if allowed_updates is not None:
            params["allowed_updates"] = allowed_updates
        # Сетевой таймаут должен быть больше, чем long polling у Telegram.
        return self.call("getUpdates", params, timeout=timeout + 15, retries=0)

    def download(self, file_id, dest_path):
        """Скачать файл, присланный боту (Bot API отдаёт до 20 МБ). Возвращает путь."""
        info = self.call("getFile", {"file_id": file_id})
        url = "{}/file/bot{}/{}".format(self.api_base, self.token, info["file_path"])
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        tmp = dest_path + ".part"
        try:
            with urllib.request.urlopen(url, timeout=120) as r, open(tmp, "wb") as f:
                while True:
                    chunk = r.read(64 * 1024)
                    if not chunk:
                        break
                    f.write(chunk)
        except urllib.error.HTTPError as e:
            raise TelegramError("не удалось скачать файл: HTTP {}".format(e.code), e.code)
        os.replace(tmp, dest_path)
        return dest_path


# ---------------------------------------------------------------- обёртка задачи

def run_task(name, fn, bot=None):
    """Запустить задачу; при исключении — предупреждение владельцу, код выхода 1.

    fn получает объект Bot. Так ни одна задача не «падает молча».
    """
    bot = bot or Bot.from_config()
    try:
        return fn(bot)
    except KeyboardInterrupt:
        raise
    except Exception as e:
        tb = traceback.format_exc()
        sys.stderr.write(tb)
        try:
            bot.send("⚠️ <b>{}</b>: ошибка\n<code>{}</code>".format(
                esc(name), esc("{}: {}".format(type(e).__name__, e))[:1500]))
        except Exception:
            sys.stderr.write("…и не удалось отправить предупреждение в Telegram\n")
        sys.exit(1)
