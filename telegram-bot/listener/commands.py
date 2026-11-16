"""Команды бота. Новая команда = функция + строка в COMMANDS.

Функция получает (ctx, args) и возвращает текст ответа (HTML) или None.
ctx: bot, cfg, msg, chat_id, is_owner, started_at, inbox_path.
"""

import datetime as dt
import json
import os
import shutil
import time

from common import tg

MSK = dt.timezone(dt.timedelta(hours=3))


def _human_age(seconds):
    seconds = int(seconds)
    d, rem = divmod(seconds, 86400)
    h, rem = divmod(rem, 3600)
    m = rem // 60
    if d:
        return "{} д {} ч".format(d, h)
    if h:
        return "{} ч {} мин".format(h, m)
    return "{} мин".format(m)


def cmd_help(ctx, args):
    lines = ["<b>Что я умею</b>"]
    for name, (_, descr, owner_only) in sorted(COMMANDS.items()):
        if owner_only and not ctx["is_owner"]:
            continue
        lines.append("/{} — {}".format(name, tg.esc(descr)))
    if ctx["is_owner"]:
        lines.append("")
        lines.append("Любой текст, пересланное сообщение или файл я сохраняю на NAS (ставлю 👍).")
    return "\n".join(lines)


def cmd_id(ctx, args):
    msg = ctx["msg"]
    out = "chat_id этого чата: <code>{}</code>".format(ctx["chat_id"])
    user = msg.get("from") or {}
    if user and user.get("id") != ctx["chat_id"]:
        out += "\nваш user_id: <code>{}</code>".format(user["id"])
    fwd = msg.get("forward_origin") or {}
    if fwd.get("type") == "channel":
        out += "\nканал, откуда переслано: <code>{}</code>".format(fwd["chat"]["id"])
    elif fwd.get("type") == "user":
        out += "\nавтор пересланного: <code>{}</code>".format(fwd["sender_user"]["id"])
    return out


def cmd_ping(ctx, args):
    return "🏓 pong. Работаю {}.".format(_human_age(time.time() - ctx["started_at"]))


def cmd_status(ctx, args):
    lines = ["<b>NAS</b>"]
    try:
        with open("/proc/uptime") as f:
            lines.append("Аптайм: {}".format(_human_age(float(f.read().split()[0]))))
    except OSError:
        pass
    try:
        la = os.getloadavg()
        lines.append("Нагрузка: {:.2f} {:.2f} {:.2f}".format(*la))
    except OSError:
        pass
    for vol in ("/volume1", os.path.expanduser("~")):
        if os.path.isdir(vol):
            du = shutil.disk_usage(vol)
            lines.append("Диск {}: свободно {:.0f} из {:.0f} ГБ".format(vol, du.free / 1e9, du.total / 1e9))
            break
    lines.append("Приёмник работает {}.".format(_human_age(time.time() - ctx["started_at"])))
    return "\n".join(lines)


def cmd_inbox(ctx, args):
    """Последние N сохранённых записей."""
    try:
        n = max(1, min(int(args.strip() or 5), 30))
    except ValueError:
        n = 5
    path = ctx["inbox_path"]
    if not os.path.exists(path):
        return "Сохранённого пока нет."
    with open(path, encoding="utf-8") as f:
        rows = [json.loads(line) for line in f if line.strip()][-n:]
    out = ["<b>Последние {}:</b>".format(len(rows))]
    for r in rows:
        when = dt.datetime.fromtimestamp(r["date"], MSK).strftime("%d.%m %H:%M")
        what = r.get("text") or ""
        if r.get("files"):
            what = (what + " " if what else "") + "📎 " + ", ".join(os.path.basename(p) for p in r["files"])
        src = " ← {}".format(r["forward_from"]) if r.get("forward_from") else ""
        out.append("<b>{}</b>{} {}".format(when, tg.esc(src), tg.esc(what[:200] or "[без текста]")))
    return "\n".join(out)


# имя: (функция, описание, только_для_владельца)
COMMANDS = {
    "start": (cmd_help, "список команд", False),
    "help": (cmd_help, "список команд", False),
    "id": (cmd_id, "показать chat_id (и id канала у пересланного)", False),
    "ping": (cmd_ping, "проверка, что бот жив", True),
    "status": (cmd_status, "состояние NAS", True),
    "inbox": (cmd_inbox, "последние сохранённые сообщения: /inbox 10", True),
}
