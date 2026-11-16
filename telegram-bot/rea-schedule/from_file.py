#!/usr/bin/env python3
"""Расписание на завтра из файла timetable/*.json (собирается вручную по скриншотам rasp.rea.ru).

Вызывается приёмником по напоминанию с "builder": "rea_timetable" (listener/reminders.json).
Сайт не опрашивается: он запрещает автоматический доступ.

    python3 rea-schedule/from_file.py                  # показать сообщение на завтра
    python3 rea-schedule/from_file.py --date 2026-11-17
    python3 rea-schedule/from_file.py --exams [2026-11-19]   # напоминание о зачётах + список
"""

import datetime as dt
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import schedule_bot as sb  # noqa: E402  (формат сообщения — общий, утверждённый)

MSK = dt.timezone(dt.timedelta(hours=3))
WARN_DAYS = 3  # за сколько дней до конца данных просить новые скриншоты
EXAM_NOTICE_DAYS = (7, 3)  # за сколько дней напоминать о зачётах (накануне — в вечернем расписании)
EXAM_WORDS = ("зачет", "зачёт", "экзамен")


def load_days():
    """Все дни из всех файлов timetable/*.json; более свежий файл перекрывает старый."""
    days, last = {}, None
    for path in sorted(glob.glob(os.path.join(HERE, "timetable", "*.json")), key=os.path.getmtime):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        lo, hi = data.get("covered") or [min(data["days"]), max(data["days"])]
        lo, hi = dt.date.fromisoformat(lo), dt.date.fromisoformat(hi)
        d = lo
        while d <= hi:  # дни внутри охвата, которых нет в файле (воскресенья) — без занятий
            days[d] = []
            d += dt.timedelta(days=1)
        for k, v in data["days"].items():
            days[dt.date.fromisoformat(k)] = [
                {"num": l.get("pair", 0), "start": _hm(l["start"]), "end": _hm(l.get("end", "")),
                 "subject": l["subject"], "kind": l.get("kind", "")}
                for l in sorted(v.get("lessons") or [], key=lambda x: x.get("pair", 0))]
        last = hi if last is None or hi > last else last
    return days, last


def is_exam(lesson):
    return any(w in lesson.get("kind", "").lower() for w in EXAM_WORDS)


def _hm(t):
    return t.lstrip("0") if t and t[0] == "0" and t[1] != ":" else t


def build(now=None):
    now = now or dt.datetime.now(MSK)
    target = now.date() + dt.timedelta(days=1)
    return build_for(target, today=now.date())


def build_for(target, today):
    days, last = load_days()
    if target not in days:
        return ("📅 <b>Нет расписания на завтра ({} {})</b>\nВ файле данные только до {}. "
                "Пришлите новые скриншоты rasp.rea.ru.".format(
                    sb.WEEKDAYS[target.weekday()], target.strftime("%d.%m"),
                    last.strftime("%d.%m") if last else "—"))
    lessons = [dict(l, kind="🎓 " + l["kind"]) if is_exam(l) else l for l in days[target]]
    text = sb.format_message(target, lessons)
    if last and (last - today).days <= WARN_DAYS:
        text += "\n\n⏳ Расписание в файле заканчивается {} — пришлите новые скриншоты.".format(
            last.strftime("%d.%m"))
    return text


def _when(d):
    return "{} {}".format(sb.WEEKDAYS[d.weekday()], d.strftime("%d.%m"))


def upcoming_exams(today):
    days, _ = load_days()
    return [(d, l) for d in sorted(days) if d >= today for l in days[d] if is_exam(l)]


def build_exams(now=None):
    """Напоминание о зачётах через 7 и 3 дня. None — сегодня напоминать не о чем."""
    today = (now or dt.datetime.now(MSK)).date()
    blocks = []
    for n in EXAM_NOTICE_DAYS:
        d = today + dt.timedelta(days=n)
        items = [l for (dd, l) in upcoming_exams(d) if dd == d]
        if items:
            word = "зачёты" if len(items) > 1 else "зачёт"
            lines = ["🎓 <b>Через {} дн. {}</b> — {}".format(n, word, _when(d))]
            for l in items:
                lines.append("• {} {} <i>({})</i>".format(l["start"], sb.html.escape(l["subject"]),
                                                          sb.html.escape(l["kind"])))
            blocks.append("\n".join(lines))
    return "\n\n".join(blocks) or None


def list_exams(today=None):
    today = today or dt.datetime.now(MSK).date()
    items = upcoming_exams(today)
    if not items:
        return "Предстоящих зачётов в файле нет."
    out = ["🎓 <b>Предстоящие зачёты</b>"]
    for d, l in items:
        left = (d - today).days
        out.append("<b>{}</b> {} {} <i>({})</i> — {}".format(
            _when(d), l["start"], sb.html.escape(l["subject"]), sb.html.escape(l["kind"]),
            "сегодня" if left == 0 else "через {} дн.".format(left)))
    return "\n".join(out)


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "--exams":
        day = dt.date.fromisoformat(sys.argv[2]) if len(sys.argv) == 3 else dt.datetime.now(MSK).date()
        print(build_exams(dt.datetime(day.year, day.month, day.day, 10, tzinfo=MSK)) or "(сегодня напоминаний нет)")
        print()
        print(list_exams(day))
    elif len(sys.argv) == 3 and sys.argv[1] == "--date":
        t = dt.date.fromisoformat(sys.argv[2])
        print(build_for(t, today=t - dt.timedelta(days=1)))
    else:
        print(build())
