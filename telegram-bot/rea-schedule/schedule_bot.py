#!/usr/bin/env python3
"""Ежевечерняя рассылка расписания РЭУ им. Плеханова в Telegram.

Задача общего бота (~/bot). Токен и прокси — из ~/bot/config.json: Telegram идёт через
туннель AmneziaWG, а rasp.rea.ru открывается напрямую (с зарубежных адресов он не отвечает).
Группа и получатели — в settings.json рядом со скриптом.
Только стандартная библиотека Python 3 (подходит для Synology DSM 7 без pip).

Запуск:
  python3 schedule_bot.py              # обычный режим: расписание на завтра -> Telegram
  python3 schedule_bot.py --dry-run    # показать сообщение в консоли, ничего не отправлять
  python3 schedule_bot.py --dump       # сохранить сырой ответ сайта в dump.html (для отладки)
  python3 schedule_bot.py --date 2026-11-21   # расписание на конкретную дату
  python3 schedule_bot.py --from-file dump.html --dry-run   # разобрать сохранённый файл
  python3 schedule_bot.py --ping       # проверить связь с Telegram (пробное сообщение)
"""

import argparse
import datetime as dt
import html
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from html.parser import HTMLParser

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from common import tg  # noqa: E402

SETTINGS_PATH = os.path.join(HERE, "settings.json")
STATE_PATH = os.path.join(HERE, "state.json")
DUMP_PATH = os.path.join(HERE, "dump.html")

SITE = "https://rasp.rea.ru"
USER_AGENT = "Mozilla/5.0 (compatible; family-schedule-bot/1.0)"
MSK = dt.timezone(dt.timedelta(hours=3))

WEEKDAYS = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]
DAY_HEADER_RE = re.compile(
    r"^(понедельник|вторник|среда|четверг|пятница|суббота|воскресенье)\s*,\s*(\d{2})\.(\d{2})\.(\d{4})$",
    re.IGNORECASE,
)
PAIR_RE = re.compile(r"^(\d{1,2})\s*пара$", re.IGNORECASE)
TIME_RE = re.compile(r"^(\d{1,2}):(\d{2})$")
LESSON_TYPES = (
    "лекция", "практическое занятие", "лабораторная работа", "семинар",
    "консультация", "экзамен", "зачет", "зачёт", "дифференцированный зачет",
    "дифференцированный зачёт", "курсовая работа", "контрольная работа",
)


# ---------------------------------------------------------------- загрузка

def load_settings():
    with open(SETTINGS_PATH, encoding="utf-8") as f:
        return json.load(f)


def http_get(path, params):
    url = SITE + path + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT,
        "X-Requested-With": "XMLHttpRequest",
        "Referer": SITE + "/?q=" + urllib.parse.quote(params.get("selection", "")),
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")


def fetch_week(group, week_num=-1):
    return http_get("/Schedule/ScheduleCard", {"selection": group, "weekNum": week_num, "catfilter": 0})


def week_number_of(card_html):
    m = re.search(r'id="weekNum"[^>]*value="(-?\d+)"', card_html) or \
        re.search(r'value="(-?\d+)"[^>]*id="weekNum"', card_html)
    return int(m.group(1)) if m else None


# ---------------------------------------------------------------- разбор

class _TextLines(HTMLParser):
    """Превращает HTML в список текстовых строк (каждый текстовый узел — строка)."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.lines = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self._skip += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self._skip:
            self._skip -= 1

    def handle_data(self, data):
        if self._skip:
            return
        for part in data.splitlines():
            s = " ".join(part.split())
            if s:
                self.lines.append(s)


def _split_pair_line(line):
    """'1 пара 08:30 10:00' может прийти одной строкой — разбиваем на токены."""
    out = []
    m = re.match(r"^(\d{1,2}\s*пара)\s+(.*)$", line, re.IGNORECASE)
    if m:
        out.append(m.group(1))
        line = m.group(2)
    for tok in re.split(r"\s+(?=\d{1,2}:\d{2}\b)|(?<=\d{2}:\d{2})\s+", line):
        if tok:
            out.append(tok)
    return out


def parse_schedule(card_html):
    """Возвращает {date: [ {num, start, end, subject, kind}, ... ]}.

    Пустой список — занятий нет. Разбор по тексту, как он виден на странице:
      ДЕНЬ, ДД.ММ.ГГГГ
      N пара / ЧЧ:ММ / ЧЧ:ММ / Предмет / Тип / Корпус - ауд., пл. Основная
    """
    p = _TextLines()
    p.feed(card_html)
    lines = []
    for ln in p.lines:
        lines.extend(_split_pair_line(ln))

    days = {}
    cur_date = None
    cur = None  # текущая пара

    def close_pair():
        nonlocal cur
        if cur and cur_date and cur.get("start") and cur["rest"]:
            subject_parts, kind = [], ""
            for t in cur["rest"]:
                low = t.lower().strip(" .")
                if "корпус" in low or low.startswith("пл.") or low in ("основная",) or low.startswith("ауд"):
                    break
                if not kind and low in LESSON_TYPES:
                    kind = t
                    continue
                if kind:
                    break
                subject_parts.append(t)
            subject = " ".join(subject_parts).strip()
            if subject:
                days[cur_date].append({
                    "num": cur["num"], "start": cur["start"], "end": cur.get("end", ""),
                    "subject": subject, "kind": kind,
                })
        cur = None

    for ln in lines:
        m = DAY_HEADER_RE.match(ln.strip())
        if m:
            close_pair()
            cur_date = dt.date(int(m.group(4)), int(m.group(3)), int(m.group(2)))
            days.setdefault(cur_date, [])
            continue
        if cur_date is None:
            continue
        m = PAIR_RE.match(ln)
        if m:
            close_pair()
            cur = {"num": int(m.group(1)), "rest": []}
            continue
        if cur is None:
            continue
        m = TIME_RE.match(ln)
        if m and not cur["rest"]:
            t = f"{int(m.group(1))}:{m.group(2)}"
            if "start" not in cur:
                cur["start"] = t
            else:
                cur["end"] = t
            continue
        cur["rest"].append(ln)
    close_pair()

    for d in days:
        days[d].sort(key=lambda x: x["num"])
    return days


# ---------------------------------------------------------------- сообщение

def format_message(date, lessons):
    day = WEEKDAYS[date.weekday()]
    dm = date.strftime("%d.%m")
    if not lessons:
        return f"<b>Расписание на завтра, {day} {dm} — занятий нет</b>"
    out = [f"<b>Расписание на завтра, {day} {dm}, начало {lessons[0]['start']}</b>", ""]
    for i, l in enumerate(lessons):
        tm = f"{l['start']}–{l['end']}" if l["end"] else l["start"]
        out.append(f"<b>{tm}</b> {html.escape(l['subject'])}")
        if l["kind"]:
            out.append(f"<i>{html.escape(l['kind'])}</i>")
        if i != len(lessons) - 1:
            out.append("")
    return "\n".join(out)


def describe_changes(old, new):
    """Сравнивает прошлый снимок дня с текущим; возвращает строки-пояснения или []."""
    if old is None or old == new:
        return []
    key = lambda l: (l["start"], l["subject"], l["kind"])
    old_set, new_set = {key(l) for l in old}, {key(l) for l in new}
    notes = []
    for l in new:
        if key(l) not in old_set:
            notes.append(f"➕ {l['start']} {l['subject']}")
    for l in old:
        if key(l) not in new_set:
            notes.append(f"➖ {l['start']} {l['subject']}")
    return notes


# ---------------------------------------------------------------- Telegram

def send_all(bot, recipients, text):
    for chat_id in recipients:
        bot.send(text, chat_id=chat_id)


# ---------------------------------------------------------------- состояние

def load_state():
    try:
        with open(STATE_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_state(state):
    tmp = STATE_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=1)
    os.replace(tmp, STATE_PATH)


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="не отправлять, только напечатать")
    ap.add_argument("--dump", action="store_true", help="сохранить сырой ответ сайта в dump.html")
    ap.add_argument("--date", help="дата ГГГГ-ММ-ДД вместо «завтра»")
    ap.add_argument("--from-file", help="разобрать сохранённый HTML вместо запроса к сайту")
    ap.add_argument("--ping", action="store_true", help="отправить пробное сообщение в Telegram")
    args = ap.parse_args()

    settings = load_settings()
    group = settings["group"]
    bot = tg.Bot.from_config()
    recipients = settings.get("recipients") or [bot.owner]

    if args.ping:
        send_all(bot, recipients, "✅ Бот расписания на связи.")
        print("Отправлено.")
        return

    target = dt.date.fromisoformat(args.date) if args.date else (dt.datetime.now(MSK).date() + dt.timedelta(days=1))

    try:
        if args.from_file:
            with open(args.from_file, encoding="utf-8") as f:
                pages = [f.read()]
        else:
            pages = [fetch_week(group)]
            days = parse_schedule(pages[0])
            if target not in days:
                # завтра — уже следующая неделя (например, вечер воскресенья)
                wn = week_number_of(pages[0])
                if wn is not None:
                    pages.append(fetch_week(group, wn + 1))
    except Exception as e:  # сайт недоступен и т.п. — сообщаем, а не молчим
        msg = f"⚠️ Не удалось получить расписание с rasp.rea.ru: {e}"
        print(msg, file=sys.stderr)
        if not args.dry_run:
            send_all(bot, recipients, html.escape(msg))
        sys.exit(1)

    if args.dump:
        with open(DUMP_PATH, "w", encoding="utf-8") as f:
            f.write("\n<!-- ===== next page ===== -->\n".join(pages))
        print(f"Сохранено в {DUMP_PATH}")

    days = {}
    for pg in pages:
        days.update(parse_schedule(pg))

    if target not in days:
        msg = (f"⚠️ Не нашёл в расписании дату {target.strftime('%d.%m.%Y')}. "
               f"Возможно, изменился формат сайта — нужна проверка.")
        print(msg, file=sys.stderr)
        if not args.dry_run:
            send_all(bot, recipients, html.escape(msg))
        sys.exit(2)

    lessons = days[target]
    text = format_message(target, lessons)

    # изменения относительно прошлой проверки
    state = load_state()
    snaps = state.setdefault("snapshots", {})
    changes = describe_changes(snaps.get(target.isoformat()), lessons)
    if changes:
        text += "\n\n⚠️ <b>Изменения с прошлой проверки:</b>\n" + "\n".join(html.escape(c) for c in changes)
    for d, ls in days.items():
        snaps[d.isoformat()] = ls
    # старые даты не храним
    cutoff = (target - dt.timedelta(days=14)).isoformat()
    state["snapshots"] = {k: v for k, v in snaps.items() if k >= cutoff}

    if args.dry_run:
        print(text)
        return
    send_all(bot, recipients, text)
    save_state(state)
    print("Отправлено:\n" + text)


if __name__ == "__main__":
    # Любая непредвиденная ошибка — предупреждение владельцу, а не тишина.
    tg.run_task("расписание РЭУ", lambda bot: main())
