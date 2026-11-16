#!/usr/bin/env python3
"""Проверка бота и разведка: кто пишет боту, какие у чатов chat_id.

    python3 tools/tg_check.py            # имя бота + список чатов из последних входящих
    python3 tools/tg_check.py --ping     # пробное сообщение владельцу
    python3 tools/tg_check.py --raw      # сырые входящие (JSON), если нужно разобраться

Ничего не «подтверждает»: входящие остаются у Telegram и достанутся приёмнику.
Пока работает приёмник (listener), Telegram отдаёт входящие только ему (ошибка 409) —
тогда chat_id удобнее узнавать командой /id или из уведомлений приёмника.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from common import tg  # noqa: E402


def describe_chat(chat):
    name = chat.get("title") or " ".join(x for x in (chat.get("first_name"), chat.get("last_name")) if x)
    if chat.get("username"):
        name += " (@{})".format(chat["username"])
    return name.strip() or "—"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ping", action="store_true", help="отправить пробное сообщение владельцу")
    ap.add_argument("--raw", action="store_true", help="напечатать входящие как JSON")
    args = ap.parse_args()

    cfg = tg.load_config()
    bot = tg.Bot.from_config(cfg)

    print("Прокси: {}".format(cfg.get("proxy") or "нет (прямое подключение)"))
    try:
        me = bot.me(retries=0)
    except tg.TelegramError as e:
        if e.code is None:
            sys.exit("Нет связи с Telegram: {}\n"
                     "В России api.telegram.org заблокирован — нужен прокси (\"proxy\" в config.json).".format(e))
        raise
    print("Бот: @{} ({}), id {}".format(me.get("username"), me.get("first_name"), me.get("id")))
    print("Владелец (owner_chat_id): {}".format(cfg.get("owner_chat_id")))

    hook = bot.call("getWebhookInfo")
    if hook.get("url"):
        print("ВНИМАНИЕ: у бота включён вебхук ({}). getUpdates и приёмник работать не будут.\n"
              "Отключить: bot.call('deleteWebhook')".format(hook["url"]))
        return

    if args.ping:
        bot.send("✅ <b>Связь есть.</b> Бот @{} работает с NAS.".format(tg.esc(me.get("username"))))
        print("Пробное сообщение отправлено.")
        return

    try:
        updates = bot.get_updates(timeout=0)
    except tg.TelegramError as e:
        if e.code == 409:
            print("Входящие сейчас забирает приёмник (listener) — это нормально.\n"
                  "chat_id: попросите человека написать боту /id, либо смотрите уведомления приёмника.")
            return
        raise

    if args.raw:
        print(json.dumps(updates, ensure_ascii=False, indent=2))
        return

    chats = {}
    for u in updates:
        msg = u.get("message") or u.get("edited_message") or u.get("channel_post") or {}
        chat = msg.get("chat")
        if chat:
            chats[chat["id"]] = (chat, msg.get("text") or msg.get("caption") or "[без текста]")
        for key in ("my_chat_member", "chat_member"):
            if key in u:
                chats.setdefault(u[key]["chat"]["id"], (u[key]["chat"], "[бота добавили/удалили]"))

    if not chats:
        print("Новых входящих нет. Telegram хранит их ~24 часа; напишите боту и запустите снова.")
        return
    print("\nЧаты из последних входящих ({} шт.):".format(len(chats)))
    for cid, (chat, last) in chats.items():
        print("  {:>15}  {:<10}  {}  — «{}»".format(cid, chat.get("type"), describe_chat(chat), last[:60]))


if __name__ == "__main__":
    try:
        main()
    except tg.TelegramError as e:
        sys.exit("Ошибка Telegram: {} (код {})".format(e, e.code))
