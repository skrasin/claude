#!/usr/bin/env python3
"""Автообновление бота из GitHub. Запускается задачей Планировщика bot-run раз в 10 минут.

    python3 tools/autoupdate.py            # проверить и, если есть изменения, обновить
    python3 tools/autoupdate.py --force    # скопировать всё заново и перезапустить бота

Как работает:
  1. ~/bot-repo (клон skrasin/claude, ключ только для чтения) — git fetch + reset на origin/main;
  2. если коммит новее развёрнутого — копирует в ~/bot ТОЛЬКО файлы из telegram-bot/,
     которые есть в git. Ничего не удаляет: config.json, vpn/amnezia.conf, data/, логи — не трогаются;
  3. если поменялся код (*.py, listener/reminders.json, settings.json) — перезапускает приёмник;
     если только данные (расписание) или документы — без перезапуска;
  4. пишет в Telegram «🔄 Бот обновлён…»; при ошибке — «⚠️» (одну и ту же ошибку — один раз).
"""

import json
import os
import shutil
import subprocess
import sys
import time

TOOLS = os.path.dirname(os.path.abspath(__file__))
BOT_DIR = os.path.dirname(TOOLS)
sys.path.insert(0, BOT_DIR)

SUBDIR = "telegram-bot"
STATE_PATH = os.path.join(TOOLS, "autoupdate.state.json")
GIT = shutil.which("git") or "/usr/bin/git"
RESTART_IF = (".py",)
RESTART_FILES = ("listener/reminders.json", "rea-schedule/settings.json")


def log(msg):
    print("{} {}".format(time.strftime("%Y-%m-%d %H:%M:%S"), msg), flush=True)


def git(repo, *args, timeout=120):
    r = subprocess.run([GIT, "-C", repo] + list(args), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       universal_newlines=True, timeout=timeout)
    if r.returncode != 0:
        raise RuntimeError("git {}: {}".format(" ".join(args[:2]), r.stdout.strip()[-400:]))
    return r.stdout.strip()


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


def repo_dir():
    try:
        with open(os.path.join(BOT_DIR, "config.json"), encoding="utf-8") as f:
            cfg = json.load(f)
    except (OSError, ValueError):
        cfg = {}
    return os.path.expanduser(cfg.get("repo_dir") or "~/bot-repo")


def changed_files(repo, old, new):
    """Изменённые файлы внутри telegram-bot/ (пути относительно неё); None — неизвестно."""
    if not old:
        return None
    try:
        out = git(repo, "diff", "--name-only", old, new, "--", SUBDIR)
    except RuntimeError:
        return None  # старого коммита нет в истории — считаем, что изменилось всё
    return [p[len(SUBDIR) + 1:] for p in out.splitlines() if p.startswith(SUBDIR + "/")]


def deploy(repo):
    """Копирует все отслеживаемые файлы telegram-bot/ в ~/bot. Возвращает их число."""
    files = git(repo, "ls-files", "--", SUBDIR).splitlines()
    n = 0
    for path in files:
        rel = path[len(SUBDIR) + 1:]
        src, dst = os.path.join(repo, path), os.path.join(BOT_DIR, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        tmp = dst + ".upd"
        shutil.copyfile(src, tmp)
        shutil.copymode(src, tmp)
        os.replace(tmp, dst)  # атомарно: бот никогда не видит полузаписанный файл
        n += 1
    return n


def needs_restart(changed):
    if changed is None:
        return True
    return any(p.endswith(RESTART_IF) or p in RESTART_FILES for p in changed)


def restart_listener():
    py = sys.executable or "python3"
    subprocess.run([py, os.path.join("listener", "listener.py"), "--stop"], cwd=BOT_DIR,
                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=60)
    with open(os.devnull, "wb") as devnull:
        subprocess.Popen([py, os.path.join("listener", "listener.py")], cwd=BOT_DIR, stdin=devnull,
                         stdout=devnull, stderr=devnull, start_new_session=True)


def notify(text):
    try:
        from common import tg
        tg.Bot.from_config().send(text)
    except Exception as e:  # без связи с Telegram — хотя бы в журнал
        log("не удалось отправить в Telegram: {}".format(e))


def main():
    force = "--force" in sys.argv
    state = load_state()
    repo = repo_dir()
    try:
        if not os.path.isdir(os.path.join(repo, ".git")):
            raise RuntimeError("нет клона репозитория в {}".format(repo))
        git(repo, "fetch", "--quiet", "origin", "main")
        new = git(repo, "rev-parse", "FETCH_HEAD")
        old = state.get("deployed")
        if new == old and not force:
            if state.pop("last_error", None):
                save_state(state)
            return 0
        git(repo, "reset", "--quiet", "--hard", new)
        changed = None if force else changed_files(repo, old, new)
        if changed == [] and not force:  # коммит не про бота (например, оглавление репозитория)
            state["deployed"] = new
            state.pop("last_error", None)
            save_state(state)
            log("{}: изменений в {} нет".format(new[:7], SUBDIR))
            return 0
        n = deploy(repo)
        restart = needs_restart(changed)
        if restart:
            restart_listener()
        subject = git(repo, "log", "-1", "--format=%s", new)
        state["deployed"] = new
        state.pop("last_error", None)
        save_state(state)
        what = ("{} файл(ов)".format(len(changed)) if changed is not None else "все файлы ({})".format(n))
        log("обновлено до {} ({}), перезапуск: {}".format(new[:7], what, "да" if restart else "нет"))
        from common import tg
        lines = ["🔄 <b>Бот обновлён</b>: {}".format(tg.esc(subject)),
                 "Изменено: {}{}".format(what, ", бот перезапущен" if restart else "")]
        if changed:
            lines.append(tg.esc(", ".join(changed[:8]) + (" …" if len(changed) > 8 else "")))
        notify("\n".join(lines))
        return 0
    except Exception as e:
        err = "{}: {}".format(type(e).__name__, e)
        log("ОШИБКА " + err)
        if state.get("last_error") != err:  # одну и ту же ошибку не повторяем каждые 10 минут
            state["last_error"] = err
            save_state(state)
            try:
                from common import tg
                notify("⚠️ <b>Автообновление не удалось</b>\n<code>{}</code>".format(tg.esc(err)[:1500]))
            except Exception:
                pass
        return 1


if __name__ == "__main__":
    sys.exit(main())
