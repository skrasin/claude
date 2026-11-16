#!/usr/bin/env python3
"""VPN для бота на NAS: AmneziaWG (.conf из Amnezia) → локальный HTTP-прокси через awg-wireproxy.

Зачем: из России api.telegram.org заблокирован. awg-wireproxy подключается к вашему
серверу Amnezia полностью в пользовательском режиме: без root, без нового сетевого
интерфейса, без изменения маршрутов NAS. Он открывает прокси только на самом NAS
(127.0.0.1:10809), через него ходит только бот.

    python3 vpn/awg_setup.py install     # скачать awg-wireproxy (ARM64) с GitHub, проверить SHA-256
    python3 vpn/awg_setup.py configure   # из vpn/amnezia.conf собрать wireproxy.conf, проверить Telegram
    python3 vpn/awg_setup.py start       # запустить, если не запущен (для Планировщика)
    python3 vpn/awg_setup.py stop
    python3 vpn/awg_setup.py status      # работает ли прокси и виден ли через него Telegram

Программа: https://github.com/bropines/awg-wireproxy (ISC). Ключи из .conf скрипт не печатает.
"""

import hashlib
import io
import os
import re
import signal
import subprocess
import sys
import tarfile
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
BIN = os.path.join(HERE, "wireproxy")
SRC_CONF = os.path.join(HERE, "amnezia.conf")
CONF = os.path.join(HERE, "wireproxy.conf")
PID_FILE = os.path.join(HERE, "wireproxy.pid")
LOG_FILE = os.path.join(HERE, "wireproxy.log")
REPO = "https://github.com/bropines/awg-wireproxy"
HTTP_PORT = 10809
TEST_URL = "https://api.telegram.org/"
MEM_LIMIT = "120MiB"  # у DS218 всего 2 ГБ на всё

# Ключи wg-quick, которые нужны только системному клиенту; wireproxy их не понимает.
DROP_KEYS = {"postup", "postdown", "preup", "predown", "table", "saveconfig", "fwmark"}


def die(msg):
    sys.exit("ОШИБКА: " + msg)


def fetch(url, timeout=60, proxy=None):
    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({"http": proxy, "https": proxy} if proxy else {}))
    req = urllib.request.Request(url, headers={"User-Agent": "nas-bot-installer"})
    r = opener.open(req, timeout=timeout)
    return r.geturl(), r.read()


# ---------------------------------------------------------------- install

def _local_archive():
    for name in sorted(os.listdir(HERE)):
        if name.startswith("awg-wireproxy") and "linux_arm64" in name and name.endswith(".tar.gz"):
            return os.path.join(HERE, name)
    return None


def cmd_install():
    local = _local_archive()
    if local:
        print("Беру архив, загруженный вручную: " + os.path.basename(local))
        data, expected = open(local, "rb").read(), None
    else:
        try:
            final_url, _ = fetch(REPO + "/releases/latest")
            tag = final_url.rstrip("/").rsplit("/", 1)[-1]
            if not tag or tag == "latest":
                raise RuntimeError("не удалось узнать последнюю версию")
            base = "{}/releases/download/{}/".format(REPO, tag)
            _, sums = fetch(base + "checksums.txt")
            asset, expected = None, None
            for line in sums.decode("utf-8", "replace").splitlines():
                parts = line.split()
                if len(parts) == 2 and "linux_arm64" in parts[1] and parts[1].endswith(".tar.gz"):
                    expected, asset = parts[0].lower(), parts[1]
            if not asset:
                raise RuntimeError("в checksums.txt нет сборки linux_arm64")
            print("Версия {}, скачиваю {}".format(tag, asset))
            _, data = fetch(base + asset, timeout=300)
        except Exception as e:
            die("не удалось скачать с GitHub ({}).\nСкачайте на компьютере архив *_linux_arm64.tar.gz "
                "со страницы {}/releases/latest и загрузите его в папку bot/vpn/ через File Station, "
                "затем повторите.".format(e, REPO))
    got = hashlib.sha256(data).hexdigest()
    if expected and got != expected:
        die("контрольная сумма не совпала: файл повреждён или подменён")
    print("SHA-256: {} {}".format(got, "(совпадает с официальной)" if expected else "(ручная загрузка)"))
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tar:
        member = next((m for m in tar.getmembers() if m.isfile() and os.path.basename(m.name) == "wireproxy"), None)
        if not member:
            die("в архиве нет файла wireproxy")
        with tar.extractfile(member) as src, open(BIN + ".new", "wb") as dst:
            dst.write(src.read())
    os.chmod(BIN + ".new", 0o755)
    os.replace(BIN + ".new", BIN)
    out = subprocess.run([BIN, "--version"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         universal_newlines=True, timeout=30).stdout.strip()
    print("Установлено: " + (out.splitlines()[0] if out else "?"))


# ---------------------------------------------------------------- configure

def build_conf(src_text):
    """Чистит .conf от системных ключей wg-quick и добавляет секцию [http]."""
    out, section, seen = [], None, set()
    for raw in src_text.splitlines():
        line = raw.strip()
        if not line or line.startswith(("#", ";")):
            continue
        m = re.match(r"^\[(\w+)\]$", line)
        if m:
            section = m.group(1).lower()
            if section not in ("interface", "peer"):
                section = "skip"  # чужие секции (например, наш прежний [http]) не тащим
                continue
            seen.add(section)
            out.append("")
            out.append(line)
            continue
        if section == "skip" or "=" not in line:
            continue
        key = line.split("=", 1)[0].strip().lower()
        if key in DROP_KEYS:
            continue
        out.append(line)
    if "interface" not in seen or "peer" not in seen:
        die("в amnezia.conf нет секций [Interface] и [Peer] — это не конфигурация AmneziaWG/WireGuard. "
            "В приложении Amnezia нужен экспорт «в формате AmneziaWG» (.conf), а не ключ vpn://")
    out += ["", "[http]", "BindAddress = 127.0.0.1:{}".format(HTTP_PORT), ""]
    return "\n".join(out).lstrip("\n")


def check_telegram(timeout=20):
    try:
        fetch(TEST_URL, timeout=timeout, proxy="http://127.0.0.1:{}".format(HTTP_PORT))
    except urllib.error.HTTPError:
        pass  # любой HTTP-ответ от Telegram — значит, достучались
    return True


def cmd_configure():
    if not os.path.exists(BIN):
        die("awg-wireproxy не установлен — сначала: python3 vpn/awg_setup.py install")
    if not os.path.exists(SRC_CONF):
        die("нет файла {} — загрузите туда .conf из Amnezia".format(SRC_CONF))
    os.chmod(SRC_CONF, 0o600)
    text = open(SRC_CONF, encoding="utf-8-sig").read()
    if text.strip().startswith("vpn://"):
        die("в amnezia.conf ключ vpn://, а нужен файл .conf (в Amnezia: Поделиться → формат AmneziaWG)")
    conf = build_conf(text)
    with open(CONF + ".tmp", "w", encoding="utf-8") as f:
        f.write(conf)
    os.chmod(CONF + ".tmp", 0o600)
    os.replace(CONF + ".tmp", CONF)
    awg = [k for k in ("Jc", "Jmin", "Jmax", "S1", "S2", "S3", "S4", "H1", "H2", "H3", "H4", "I1")
           if re.search(r"^\s*{}\s*=".format(k), conf, re.M | re.I)]
    print("Настройки собраны: {} (параметры AmneziaWG: {})".format(CONF, ", ".join(awg) or "нет — обычный WireGuard"))
    res = subprocess.run([BIN, "-n", "-c", CONF], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         universal_newlines=True, timeout=30)
    if res.returncode != 0:
        die("wireproxy не принял настройки:\n" + res.stdout.strip()[-800:])
    print("Проверка настроек: OK")
    cmd_stop(quiet=True)
    cmd_start()
    print("Проверяю Telegram через туннель…")
    for attempt in range(3):
        try:
            t = time.time()
            check_telegram()
            print("Telegram через туннель: доступен ({:.1f} с)".format(time.time() - t))
            return
        except Exception as e:
            err = getattr(e, "reason", e)
            time.sleep(3)
    die("Telegram через туннель недоступен ({}). Последние строки журнала:\n{}".format(err, _log_tail()))


# ---------------------------------------------------------------- запуск / статус

def _log_tail(n=15):
    try:
        with open(LOG_FILE, encoding="utf-8", errors="replace") as f:
            return "".join(f.readlines()[-n:])
    except OSError:
        return "(журнала нет)"


def _running_pid():
    try:
        pid = int(open(PID_FILE).read().strip())
        os.kill(pid, 0)
        with open("/proc/{}/cmdline".format(pid), "rb") as f:
            if b"wireproxy" in f.read():
                return pid
    except (OSError, ValueError):
        pass
    return None


def cmd_start():
    pid = _running_pid()
    if pid:
        print("wireproxy уже работает (pid {})".format(pid))
        return
    if not os.path.exists(CONF):
        die("нет wireproxy.conf — сначала: python3 vpn/awg_setup.py configure")
    if os.path.exists(LOG_FILE) and os.path.getsize(LOG_FILE) > 1_000_000:
        os.replace(LOG_FILE, LOG_FILE + ".old")
    env = dict(os.environ, GOMEMLIMIT=MEM_LIMIT)
    log = open(LOG_FILE, "a")
    p = subprocess.Popen([BIN, "-c", CONF], stdout=log, stderr=log, stdin=subprocess.DEVNULL,
                         env=env, start_new_session=True)
    with open(PID_FILE, "w") as f:
        f.write(str(p.pid))
    time.sleep(3)
    if p.poll() is not None:
        die("wireproxy сразу завершился. Журнал:\n" + _log_tail())
    print("wireproxy запущен (pid {}), прокси http://127.0.0.1:{}".format(p.pid, HTTP_PORT))


def cmd_stop(quiet=False):
    pid = _running_pid()
    if pid:
        os.kill(pid, signal.SIGTERM)
        time.sleep(1)
        print("wireproxy остановлен")
    elif not quiet:
        print("wireproxy не запущен")


def cmd_status():
    pid = _running_pid()
    print("wireproxy: " + ("работает, pid {}".format(pid) if pid else "НЕ работает"))
    if not pid:
        return
    try:
        check_telegram()
        print("Telegram через туннель: доступен")
    except Exception as e:
        print("Telegram через туннель: НЕДОСТУПЕН ({})\n{}".format(getattr(e, "reason", e), _log_tail()))


def main():
    cmds = {"install": cmd_install, "configure": cmd_configure, "start": cmd_start,
            "stop": cmd_stop, "status": cmd_status}
    if len(sys.argv) != 2 or sys.argv[1] not in cmds:
        sys.exit(__doc__)
    cmds[sys.argv[1]]()


if __name__ == "__main__":
    main()
