"""Напоминания по расписанию. Проверяются приёмником примерно раз в минуту.

Список — в listener/reminders.json:
    {
      "id": "rea",                      уникальное имя (по нему помнится, что уже отправлено)
      "time": "20:00",                  время по Москве
      "days": ["вс","пн","вт","ср","чт","пт"],   дни недели (пусто/нет = каждый день)
      "text": "…",                      текст, HTML
      "builder": "rea_timetable",       или: текст собирает функция (см. BUILDERS), text не нужен
      "to": [349362961],                кому (нет = владельцу)
      "enabled": true
    }
Если приёмник был выключен в нужное время, напоминание придёт после запуска,
но не позже чем через 2 часа: старые напоминания не догоняют.
После правки файла нужно перезапустить приёмник: pkill -f listener/listener.py.
"""

import datetime as dt
import importlib.util
import json
import os

from common import tg

HERE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(HERE, "reminders.json")
MSK = dt.timezone(dt.timedelta(hours=3))
DAYS = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"]
LATE_LIMIT = dt.timedelta(hours=2)
BOT_DIR = os.path.dirname(HERE)

# Сборщики текста: имя -> (файл относительно ~/bot, функция(now) -> str)
BUILDERS = {
    "rea_timetable": ("rea-schedule/from_file.py", "build"),
    "rea_exams": ("rea-schedule/from_file.py", "build_exams"),  # может вернуть None — тогда молчим
}


def load_module(rel):
    """Загрузить файл задачи (папки вида rea-schedule — не пакеты Python)."""
    name = "task_" + rel.replace("/", "_").replace("-", "_").replace(".py", "")
    spec = importlib.util.spec_from_file_location(name, os.path.join(BOT_DIR, rel))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _build(name, now):
    rel, func = BUILDERS[name]
    return getattr(load_module(rel), func)(now)


def load():
    try:
        with open(PATH, encoding="utf-8") as f:
            items = json.load(f)
    except FileNotFoundError:
        return []
    return [r for r in items if r.get("enabled", True)]


def _due_at(rem, now):
    hh, mm = (int(x) for x in rem["time"].split(":"))
    days = [d.lower()[:2] for d in rem.get("days") or DAYS]
    if DAYS[now.weekday()] not in days:
        return None
    return now.replace(hour=hh, minute=mm, second=0, microsecond=0)


def check(bot, state, now=None):
    """Отправляет те напоминания, время которых наступило. Возвращает True, если state изменился."""
    now = now or dt.datetime.now(MSK)
    sent = state.setdefault("reminders_sent", {})
    changed = False
    for rem in load():
        due = _due_at(rem, now)
        today = now.date().isoformat()
        if not due or now < due or sent.get(rem["id"]) == today:
            continue
        sent[rem["id"]] = today  # отмечаем сразу, чтобы при сбое не слать каждую минуту
        changed = True
        if now - due > LATE_LIMIT:
            continue
        try:
            text = _build(rem["builder"], now) if rem.get("builder") else rem["text"]
        except Exception as e:
            text = "⚠️ Напоминание «{}» не собралось: <code>{}</code>".format(
                tg.esc(rem["id"]), tg.esc("{}: {}".format(type(e).__name__, e)))
        if not text:
            continue
        for chat_id in rem.get("to") or [bot.owner]:
            bot.send(text, chat_id=chat_id)
    return changed


def describe():
    items = load()
    if not items:
        return "Напоминаний нет."
    out = ["<b>Напоминания</b>"]
    for r in items:
        days = ", ".join(r.get("days") or ["каждый день"])
        names = {"rea_timetable": "расписание на завтра из файла",
                 "rea_exams": "зачёты через 7 и 3 дня (если есть)"}
        first = (tg.esc(names.get(r["builder"], r["builder"]))
                 if r.get("builder") else r["text"].split("\n")[0])
        out.append("{} ({}): {}".format(tg.esc(r["time"]), tg.esc(days), first))
    return "\n".join(out)
