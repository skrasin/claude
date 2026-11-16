#!/usr/bin/env python3
"""Приёмник: постоянно слушает бота (long polling) и обрабатывает входящие.

  * команды (/help, /id, /status …) — см. commands.py;
  * от владельца: любой текст, пересланное сообщение или файл сохраняется на NAS
    в data/inbox.jsonl (файлы — в data/files/ГГГГ-ММ/), в ответ ставится 👍;
  * от незнакомых: им ничего не отвечается, владельцу приходит уведомление с их chat_id.

Запуск:
  python3 listener/listener.py          # работать постоянно (для Планировщика)
  python3 listener/listener.py --once   # обработать накопившееся и выйти (проверка)
  python3 listener/listener.py --stop   # остановить работающий приёмник

Второй экземпляр сразу выходит (блокировка listener.lock), поэтому задачу в
Планировщике можно запускать хоть каждые 10 минут: это заодно и «перезапуск, если упал».
Входящие порты и вебхуки не нужны: NAS сам ходит к api.telegram.org.
"""

import argparse
import datetime as dt
import fcntl
import json
import logging
import logging.handlers
import os
import re
import signal
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from common import tg  # noqa: E402
from listener import commands, reminders  # noqa: E402

STATE_PATH = os.path.join(HERE, "state.json")
LOCK_PATH = os.path.join(HERE, "listener.lock")
LOG_PATH = os.path.join(HERE, "listener.log")
INBOX_PATH = os.path.join(tg.DATA_DIR, "inbox.jsonl")
FILES_DIR = os.path.join(tg.DATA_DIR, "files")
POLL_TIMEOUT = 50
ALLOWED_UPDATES = ["message", "edited_message", "channel_post"]
MAX_DOWNLOAD = 20 * 1024 * 1024  # предел Bot API для скачивания

log = logging.getLogger("listener")
_stop = False


def _on_signal(signum, frame):
    global _stop
    _stop = True
    log.info("получен сигнал %s, завершаюсь", signum)


def setup_logging(verbose):
    log.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    fh = logging.handlers.RotatingFileHandler(LOG_PATH, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    fh.setFormatter(fmt)
    log.addHandler(fh)
    if verbose:
        sh = logging.StreamHandler()
        sh.setFormatter(fmt)
        log.addHandler(sh)


def load_state():
    try:
        with open(STATE_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_state(state):
    tmp = STATE_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False)
    os.replace(tmp, STATE_PATH)


# ---------------------------------------------------------------- сохранение входящих

def _safe_name(name):
    name = re.sub(r"[^\w.\-() ]+", "_", name, flags=re.UNICODE).strip(" .") or "file"
    return name[:120]


def _attachments(msg):
    """[(file_id, имя, размер)] для вложений сообщения."""
    out = []
    mid = msg["message_id"]
    if msg.get("photo"):
        p = msg["photo"][-1]  # самое большое
        out.append((p["file_id"], "photo_{}.jpg".format(mid), p.get("file_size")))
    for kind, ext in (("document", ""), ("video", ".mp4"), ("audio", ".mp3"),
                      ("voice", ".ogg"), ("video_note", ".mp4"), ("animation", ".mp4")):
        obj = msg.get(kind)
        if obj:
            name = obj.get("file_name") or "{}_{}{}".format(kind, mid, ext)
            out.append((obj["file_id"], name, obj.get("file_size")))
    return out


def _forward_label(msg):
    fo = msg.get("forward_origin")
    if not fo:
        return None
    t = fo.get("type")
    if t == "channel":
        c = fo["chat"]
        return c.get("title") or c.get("username") or str(c["id"])
    if t == "chat":
        return fo["sender_chat"].get("title") or str(fo["sender_chat"]["id"])
    if t == "user":
        u = fo["sender_user"]
        return " ".join(x for x in (u.get("first_name"), u.get("last_name")) if x)
    if t == "hidden_user":
        return fo.get("sender_user_name")
    return t


def save_to_inbox(bot, msg):
    """Сохранить сообщение владельца (и его файлы). Возвращает запись."""
    date = msg.get("date") or int(time.time())
    month = dt.datetime.fromtimestamp(date, commands.MSK).strftime("%Y-%m")
    files, skipped = [], []
    for file_id, name, size in _attachments(msg):
        if size and size > MAX_DOWNLOAD:
            skipped.append("{} ({:.0f} МБ — больше 20 МБ, Bot API не отдаёт)".format(name, size / 1e6))
            continue
        dest = os.path.join(FILES_DIR, month, "{}_{}".format(msg["message_id"], _safe_name(name)))
        try:
            bot.download(file_id, dest)
            files.append(os.path.relpath(dest, tg.BOT_DIR))
        except tg.TelegramError as e:
            skipped.append("{} ({})".format(name, e))
    entry = {
        "date": date,
        "message_id": msg["message_id"],
        "chat_id": msg["chat"]["id"],
        "text": msg.get("text") or msg.get("caption") or "",
        "forward_from": _forward_label(msg),
        "forward_date": (msg.get("forward_origin") or {}).get("date"),
        "files": files,
    }
    if msg.get("entities") or msg.get("caption_entities"):
        links = [e["url"] for e in (msg.get("entities") or msg.get("caption_entities")) if e.get("url")]
        if links:
            entry["links"] = links
    os.makedirs(tg.DATA_DIR, exist_ok=True)
    with open(INBOX_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry, skipped


# ---------------------------------------------------------------- обработка

class Listener:
    def __init__(self, bot, cfg):
        self.bot = bot
        self.cfg = cfg
        self.owner = cfg.get("owner_chat_id")
        self.allowed = set(cfg.get("allowed_chat_ids") or []) | ({self.owner} if self.owner else set())
        self.started_at = time.time()
        self.state = load_state()
        self.notified_strangers = set(self.state.get("notified_strangers", []))

    def handle_update(self, upd):
        msg = upd.get("message") or upd.get("edited_message") or upd.get("channel_post")
        if not msg or "chat" not in msg:
            return
        chat_id = msg["chat"]["id"]
        if chat_id not in self.allowed:
            self.on_stranger(msg)
            return
        if upd.get("edited_message"):
            return  # правки не обрабатываем повторно
        text = (msg.get("text") or "").strip()
        if text.startswith("/"):
            self.on_command(msg, text)
        elif chat_id == self.owner:
            entry, skipped = save_to_inbox(self.bot, msg)
            log.info("сохранено: msg %s, файлов %d", msg["message_id"], len(entry["files"]))
            if skipped:
                self.bot.send("Не сохранил: " + tg.esc("; ".join(skipped)), chat_id=chat_id,
                              reply_to=msg["message_id"])
            else:
                self.bot.react(chat_id, msg["message_id"])
        # Сообщения прочих разрешённых чатов без команды молча игнорируются.

    def on_command(self, msg, text):
        chat_id = msg["chat"]["id"]
        head, _, args = text.partition(" ")
        name = head[1:].split("@", 1)[0].lower()
        is_owner = chat_id == self.owner
        cmd = commands.COMMANDS.get(name)
        if not cmd or (cmd[2] and not is_owner):
            self.bot.send("Не знаю такой команды. /help", chat_id=chat_id)
            return
        ctx = {"bot": self.bot, "cfg": self.cfg, "msg": msg, "chat_id": chat_id, "is_owner": is_owner,
               "started_at": self.started_at, "inbox_path": INBOX_PATH}
        try:
            reply = cmd[0](ctx, args)
        except Exception as e:
            log.exception("команда /%s упала", name)
            reply = "⚠️ /{} не сработала: <code>{}</code>".format(tg.esc(name), tg.esc(e))
        if reply:
            self.bot.send(reply, chat_id=chat_id)

    def on_stranger(self, msg):
        chat = msg["chat"]
        cid = chat["id"]
        text = (msg.get("text") or "").strip()
        if text.split("@")[0] == "/id":  # пусть человек сам узнает свой chat_id
            self.bot.send("Ваш chat_id: <code>{}</code>".format(cid), chat_id=cid)
        if cid in self.notified_strangers or not self.owner:
            return
        self.notified_strangers.add(cid)
        self.state["notified_strangers"] = sorted(self.notified_strangers)
        save_state(self.state)
        who = chat.get("title") or " ".join(x for x in (chat.get("first_name"), chat.get("last_name")) if x)
        if chat.get("username"):
            who += " @" + chat["username"]
        self.bot.send(
            "👤 Боту написал(и) не из списка: <b>{}</b> ({})\nchat_id: <code>{}</code>\n«{}»\n\n"
            "Чтобы разрешить, добавьте chat_id в <code>allowed_chat_ids</code> в config.json "
            "и перезапустите приёмник.".format(
                tg.esc(who.strip() or "без имени"), tg.esc(chat.get("type")), cid,
                tg.esc((text or msg.get("caption") or "[без текста]")[:200])))
        log.info("незнакомый чат %s", cid)

    def check_reminders(self):
        try:
            if reminders.check(self.bot, self.state):
                save_state(self.state)
        except Exception:
            log.exception("ошибка напоминаний")

    def poll_once(self, timeout):
        offset = self.state.get("offset")
        updates = self.bot.get_updates(offset=offset, timeout=timeout, allowed_updates=ALLOWED_UPDATES)
        for upd in updates:
            try:
                self.handle_update(upd)
            except Exception:
                log.exception("ошибка при обработке update %s", upd.get("update_id"))
            # Сдвигаем offset даже после ошибки, чтобы одно «плохое» сообщение не зациклило бота.
            self.state["offset"] = upd["update_id"] + 1
            save_state(self.state)
        return len(updates)

    def register_menu(self):
        """Список команд в Telegram (появляется при вводе «/»). Ошибка не критична."""
        try:
            cmds = [{"command": n, "description": commands.COMMANDS[n][1]}
                    for n in commands.MENU_ORDER if n in commands.COMMANDS]
            self.bot.call("setMyCommands", {"commands": cmds}, retries=1)
        except Exception as e:
            log.warning("не удалось зарегистрировать меню команд: %s", e)

    def run_forever(self):
        log.info("приёмник запущен, pid %s", os.getpid())
        self.register_menu()
        delay = 5
        while not _stop:
            try:
                self.check_reminders()
                self.poll_once(POLL_TIMEOUT)
                delay = 5
            except tg.TelegramError as e:
                if e.code == 409:
                    log.warning("409: входящие забирает кто-то ещё (второй приёмник или вебхук)")
                    time.sleep(60)
                elif e.code == 401:
                    log.error("401: неверный токен — останавливаюсь")
                    return 1
                else:
                    log.warning("ошибка Telegram: %s; пауза %s с", e, delay)
                    time.sleep(delay)
                    delay = min(delay * 2, 300)
            except Exception:
                log.exception("непредвиденная ошибка; пауза %s с", delay)
                time.sleep(delay)
                delay = min(delay * 2, 300)
        log.info("приёмник остановлен")
        return 0


def find_running():
    """pid процессов приёмника: python, первый аргумент которого — …/listener/listener.py.

    Сверяется именно список аргументов, а не строка целиком: так не находятся оболочки
    (например, задача Планировщика DSM, в тексте которой есть строка запуска бота).
    """
    me = os.getpid()
    found = []
    for name in os.listdir("/proc"):
        if not name.isdigit() or int(name) == me:
            continue
        try:
            with open("/proc/{}/cmdline".format(name), "rb") as f:
                argv = f.read().split(b"\0")
        except OSError:
            continue
        if (len(argv) >= 2 and b"python" in os.path.basename(argv[0])
                and argv[1].endswith(b"listener/listener.py")):
            found.append(int(name))
    return found


def stop_running():
    pids = find_running()
    if not pids:
        print("бот не был запущен")
        return 0
    for pid in pids:
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            pass
    for _ in range(20):  # до 10 с на аккуратное завершение
        time.sleep(0.5)
        if not any(os.path.exists("/proc/{}".format(p)) for p in pids):
            break
    else:
        for pid in pids:
            try:
                os.kill(pid, signal.SIGKILL)
            except OSError:
                pass
        time.sleep(1)
    print("остановлен (pid {})".format(", ".join(map(str, pids))))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true", help="обработать накопившееся и выйти")
    ap.add_argument("--stop", action="store_true", help="остановить работающий приёмник и выйти")
    ap.add_argument("-v", "--verbose", action="store_true", help="дублировать журнал в консоль")
    args = ap.parse_args()
    if args.stop:
        return stop_running()
    setup_logging(args.verbose or args.once)

    # "a+", а не "w": открытие не должно стирать pid работающего экземпляра.
    lock = open(LOCK_PATH, "a+")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        if args.once:
            print("Приёмник уже работает в фоне — --once не нужен.")
        return 0  # уже запущен: тихо выходим
    lock.seek(0)
    lock.truncate()
    lock.write(str(os.getpid()))
    lock.flush()

    signal.signal(signal.SIGTERM, _on_signal)
    signal.signal(signal.SIGINT, _on_signal)

    cfg = tg.load_config()
    listener = Listener(tg.Bot.from_config(cfg), cfg)
    if args.once:
        n = listener.poll_once(timeout=0)
        print("Обработано входящих: {}".format(n))
        return 0
    return listener.run_forever()


if __name__ == "__main__":
    sys.exit(main())
