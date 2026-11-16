#!/usr/bin/env python3
"""Расписание на завтра из файла timetable/*.json (собирается вручную по скриншотам rasp.rea.ru).

Вызывается приёмником по напоминанию с "builder": "rea_timetable" (listener/reminders.json).
Сайт не опрашивается: он запрещает автоматический доступ.

    python3 rea-schedule/from_file.py                  # показать сообщение на завтра
    python3 rea-schedule/from_file.py --date 2026-11-17
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
    text = sb.format_message(target, days[target])
    if last and (last - today).days <= WARN_DAYS:
        text += "\n\n⏳ Расписание в файле заканчивается {} — пришлите новые скриншоты.".format(
            last.strftime("%d.%m"))
    return text


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--date":
        t = dt.date.fromisoformat(sys.argv[2])
        print(build_for(t, today=t - dt.timedelta(days=1)))
    else:
        print(build())
