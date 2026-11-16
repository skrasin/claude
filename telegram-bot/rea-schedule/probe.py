#!/usr/bin/env python3
"""Диагностика 403 от rasp.rea.ru: что именно отвечает сайт и кто блокирует.

Ничего не обходит: те же запросы, что делает schedule_bot.py, плюс главная страница
и robots.txt. Печатает код ответа, служебные заголовки и начало текста страницы.

    python3 rea-schedule/probe.py > rea-schedule/probe.log 2>&1
"""

import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import schedule_bot as sb  # noqa: E402

INTERESTING = ("server", "content-type", "via", "x-cache", "cf-ray", "x-qrator", "retry-after",
               "x-frame-options", "location")


def show(title, url, headers):
    print("=== {}\n{}".format(title, url))
    req = urllib.request.Request(url, headers=headers)
    try:
        r = urllib.request.urlopen(req, timeout=30)
        code, hdrs, body = r.status, r.headers, r.read()
    except urllib.error.HTTPError as e:
        code, hdrs, body = e.code, e.headers, e.read()
    except Exception as e:
        print("сеть: {}\n".format(getattr(e, "reason", e)))
        return
    print("HTTP {}".format(code))
    for k in INTERESTING:
        if hdrs.get(k):
            print("  {}: {}".format(k, hdrs.get(k)))
    cookies = [c.split("=", 1)[0] for c in hdrs.get_all("set-cookie") or []]
    if cookies:
        print("  set-cookie (имена): " + ", ".join(cookies))
    text = body.decode("utf-8", "replace")
    m = re.search(r"<title>(.*?)</title>", text, re.S | re.I)
    if m:
        print("  title: " + " ".join(m.group(1).split()))
    plain = " ".join(re.sub(r"<script.*?</script>|<style.*?</style>|<[^>]+>", " ", text, flags=re.S | re.I).split())
    print("  размер {} байт; текст: {}\n".format(len(body), plain[:400]))


def main():
    group = json.load(open(os.path.join(HERE, "settings.json"), encoding="utf-8"))["group"]
    ua = {"User-Agent": sb.USER_AGENT}
    show("robots.txt", sb.SITE + "/robots.txt", ua)
    show("главная", sb.SITE + "/", ua)
    show("главная с группой", sb.SITE + "/?q=" + urllib.parse.quote(group), ua)
    card = sb.SITE + "/Schedule/ScheduleCard?" + urllib.parse.urlencode(
        {"selection": group, "weekNum": -1, "catfilter": 0})
    show("карточка расписания (как в schedule_bot.py)", card, {
        "User-Agent": sb.USER_AGENT, "X-Requested-With": "XMLHttpRequest",
        "Referer": sb.SITE + "/?q=" + urllib.parse.quote(group)})


if __name__ == "__main__":
    main()
