#!/usr/bin/env python3
"""VPN для бота на NAS: xray-клиент по вашей подписке (Happ и т. п.) → локальный HTTP-прокси.

Зачем: из России api.telegram.org заблокирован. xray подключается к вашему VPN-серверу
и открывает прокси только на самом NAS (127.0.0.1:10809). Через него ходит только бот,
остальной трафик NAS идёт как раньше.

    python3 vpn/xray_setup.py install     # скачать xray (ARM64) с GitHub, проверить контрольную сумму
    python3 vpn/xray_setup.py configure   # прочитать подписку, найти рабочий сервер, записать xray.json
    python3 vpn/xray_setup.py start       # запустить xray, если не запущен (для Планировщика)
    python3 vpn/xray_setup.py status      # работает ли прокси и виден ли через него Telegram

Подписка (ссылка https://… из Happ) лежит в vpn/subscription.txt (chmod 600) и в git не попадает.
Ключи и пароли серверов скрипт не печатает.
"""

import base64
import hashlib
import io
import json
import os
import shutil
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
XRAY = os.path.join(HERE, "xray")
XRAY_JSON = os.path.join(HERE, "xray.json")
SUB_FILE = os.path.join(HERE, "subscription.txt")
PID_FILE = os.path.join(HERE, "xray.pid")
LOG_FILE = os.path.join(HERE, "xray.log")
LOCAL_ZIP = os.path.join(HERE, "Xray-linux-arm64-v8a.zip")
RELEASE = "https://github.com/XTLS/Xray-core/releases/latest/download/"
ASSET = "Xray-linux-arm64-v8a.zip"
HTTP_PORT = 10809
TEST_PORT = 10899
TEST_URL = "https://api.telegram.org/"
UAS = ["v2rayN/7.10.0", "Happ/2.0", "Xray-core"]


def die(msg):
    sys.exit("ОШИБКА: " + msg)


def fetch(url, ua="Mozilla/5.0", timeout=60, proxy=None):
    handlers = [urllib.request.ProxyHandler({"http": proxy, "https": proxy} if proxy else {})]
    opener = urllib.request.build_opener(*handlers)
    req = urllib.request.Request(url, headers={"User-Agent": ua})
    with opener.open(req, timeout=timeout) as r:
        return r.read()


# ---------------------------------------------------------------- install

def cmd_install():
    if os.path.exists(LOCAL_ZIP):
        print("Беру архив, загруженный вручную: " + LOCAL_ZIP)
        data = open(LOCAL_ZIP, "rb").read()
        expected = None
    else:
        print("Скачиваю " + RELEASE + ASSET)
        try:
            data = fetch(RELEASE + ASSET, timeout=300)
            dgst = fetch(RELEASE + ASSET + ".dgst").decode("utf-8", "replace")
        except Exception as e:
            die("не удалось скачать с GitHub ({}).\nСкачайте {} на компьютере со страницы "
                "https://github.com/XTLS/Xray-core/releases/latest и положите в папку bot/vpn/ "
                "через File Station, затем повторите.".format(e, ASSET))
        expected = None
        for line in dgst.splitlines():
            if line.upper().startswith(("SHA2-256", "SHA256")):
                expected = line.split("=", 1)[1].strip().lower()
        if not expected:
            die("в .dgst нет SHA-256 — не рискую ставить непроверенный файл")
    got = hashlib.sha256(data).hexdigest()
    if expected and got != expected:
        die("контрольная сумма не совпала: файл повреждён или подменён")
    print("SHA-256: {} {}".format(got, "(совпадает с официальной)" if expected else "(ручная загрузка)"))
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        with z.open("xray") as src, open(XRAY + ".new", "wb") as dst:
            shutil.copyfileobj(src, dst)
    os.chmod(XRAY + ".new", 0o755)
    os.replace(XRAY + ".new", XRAY)
    out = subprocess.run([XRAY, "version"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         universal_newlines=True, timeout=30).stdout
    print("Установлено: " + (out.splitlines()[0] if out else "?"))


# ---------------------------------------------------------------- разбор подписки

def _b64(s):
    s = s.strip().replace("-", "+").replace("_", "/")
    return base64.b64decode(s + "=" * (-len(s) % 4))


def _q(params, key, default=""):
    return params.get(key, [default])[0]


def _stream(params, host_default):
    net = _q(params, "type", "tcp") or "tcp"
    if net == "raw":
        net = "tcp"
    sec = _q(params, "security", "none") or "none"
    sni = _q(params, "sni") or _q(params, "host") or host_default
    st = {"network": net, "security": sec}
    if sec == "tls":
        tls = {"serverName": sni}
        if _q(params, "fp"):
            tls["fingerprint"] = _q(params, "fp")
        if _q(params, "alpn"):
            tls["alpn"] = _q(params, "alpn").split(",")
        if _q(params, "allowInsecure") in ("1", "true"):
            tls["allowInsecure"] = True
        st["tlsSettings"] = tls
    elif sec == "reality":
        st["realitySettings"] = {
            "serverName": sni,
            "fingerprint": _q(params, "fp", "chrome") or "chrome",
            "publicKey": _q(params, "pbk"),
            "shortId": _q(params, "sid"),
            "spiderX": _q(params, "spx"),
        }
    path, host = _q(params, "path", "/") or "/", _q(params, "host")
    if net == "ws":
        st["wsSettings"] = {"path": path, "host": host} if host else {"path": path}
    elif net == "grpc":
        st["grpcSettings"] = {"serviceName": _q(params, "serviceName"), "multiMode": _q(params, "mode") == "multi"}
    elif net == "xhttp":
        x = {"path": path, "mode": _q(params, "mode", "auto") or "auto"}
        if host:
            x["host"] = host
        if _q(params, "extra"):
            try:
                x["extra"] = json.loads(_q(params, "extra"))
            except ValueError:
                pass
        st["xhttpSettings"] = x
    elif net == "httpupgrade":
        st["httpupgradeSettings"] = {"path": path, "host": host}
    elif net == "tcp" and _q(params, "headerType") == "http":
        st["tcpSettings"] = {"header": {"type": "http", "request": {"path": [path], "headers": {"Host": [host]}}}}
    return st


def parse_link(link):
    """Ссылка vless/vmess/trojan/ss → (имя, outbound xray) или None."""
    link = link.strip()
    scheme = link.split("://", 1)[0].lower()
    if scheme == "vmess":
        j = json.loads(_b64(link[8:]).decode("utf-8"))
        params = {"type": [j.get("net") or "tcp"], "security": [j.get("tls") or "none"],
                  "sni": [j.get("sni") or ""], "host": [j.get("host") or ""], "path": [j.get("path") or "/"],
                  "fp": [j.get("fp") or ""], "alpn": [j.get("alpn") or ""], "headerType": [j.get("type") or ""],
                  "serviceName": [j.get("path") or ""]}
        out = {"protocol": "vmess", "settings": {"vnext": [{"address": j["add"], "port": int(j["port"]),
               "users": [{"id": j["id"], "alterId": int(j.get("aid") or 0), "security": j.get("scy") or "auto"}]}]},
               "streamSettings": _stream(params, j["add"])}
        return j.get("ps") or j["add"], out
    if scheme not in ("vless", "trojan", "ss"):
        return None
    u = urllib.parse.urlsplit(link)
    name = urllib.parse.unquote(u.fragment) or u.hostname
    params = urllib.parse.parse_qs(u.query)
    if scheme == "ss":
        if u.hostname is None or "@" not in u.netloc:  # ss://base64(method:pass@host:port)
            raw = _b64(u.netloc).decode("utf-8")
            cred, hostport = raw.rsplit("@", 1)
            host, port = hostport.rsplit(":", 1)
        else:
            cred = urllib.parse.unquote(u.username or "")
            try:
                cred = _b64(cred).decode("utf-8")
            except Exception:
                pass
            host, port = u.hostname, u.port
        method, password = cred.split(":", 1)
        return name, {"protocol": "shadowsocks", "settings": {"servers": [
            {"address": host, "port": int(port), "method": method, "password": password}]}}
    user = urllib.parse.unquote(u.username or "")
    st = _stream(params, u.hostname)
    if scheme == "vless":
        usr = {"id": user, "encryption": _q(params, "encryption", "none") or "none"}
        if _q(params, "flow"):
            usr["flow"] = _q(params, "flow")
        out = {"protocol": "vless", "settings": {"vnext": [{"address": u.hostname, "port": u.port, "users": [usr]}]},
               "streamSettings": st}
    else:
        if st["security"] == "none":
            st["security"] = "tls"
            st["tlsSettings"] = {"serverName": _q(params, "sni") or u.hostname}
        out = {"protocol": "trojan", "settings": {"servers": [{"address": u.hostname, "port": u.port,
               "password": user}]}, "streamSettings": st}
    return name, out


def parse_subscription(body):
    """Возвращает [(имя, outbound)]."""
    text = body.decode("utf-8", "replace").strip()
    if "happ://crypt" in text:
        die("подписка зашифрована для Happ (happ://crypt…). Попросите у VPN-сервиса обычную ссылку "
            "(vless://… или подписку для v2rayN/Hiddify) — её можно вставить в subscription.txt.")
    # Полный JSON-конфиг xray (часть панелей отдаёт его по User-Agent)
    if text.startswith(("{", "[")):
        try:
            data = json.loads(text)
            configs = data if isinstance(data, list) else [data]
            res = []
            for c in configs:
                for ob in c.get("outbounds", []):
                    if ob.get("protocol") in ("vless", "vmess", "trojan", "shadowsocks"):
                        ob = dict(ob)
                        ob.pop("tag", None)
                        res.append((c.get("remarks") or ob.get("protocol"), ob))
                        break
            return res
        except ValueError:
            pass
    if "://" not in text:
        try:
            text = _b64(text).decode("utf-8", "replace")
        except Exception:
            return []
    res = []
    for line in text.splitlines():
        if "://" in line:
            try:
                r = parse_link(line)
                if r:
                    res.append(r)
            except Exception as e:
                print("  пропускаю ссылку ({}): {}".format(line.split("://")[0], e))
    return res


def read_subscription():
    if not os.path.exists(SUB_FILE):
        die("нет файла {} — вставьте туда ссылку подписки из Happ".format(SUB_FILE))
    os.chmod(SUB_FILE, 0o600)
    src = open(SUB_FILE, encoding="utf-8").read().strip()
    if not src:
        die("файл subscription.txt пустой")
    if not src.startswith(("http://", "https://")):
        return parse_subscription(src.encode("utf-8"))  # вставлены сами ссылки vless://…
    last = None
    for ua in UAS:
        try:
            servers = parse_subscription(fetch(src, ua=ua))
        except SystemExit:
            raise
        except Exception as e:
            last = e
            continue
        if servers:
            print("Подписка прочитана (User-Agent {}): серверов {}".format(ua, len(servers)))
            return servers
    die("не удалось получить серверы из подписки ({})".format(last or "пустой ответ"))


# ---------------------------------------------------------------- конфиг и проверка

def make_config(outbound, port):
    ob = dict(outbound)
    ob["tag"] = "proxy"
    return {
        "log": {"loglevel": "warning"},
        "inbounds": [{"tag": "http-in", "listen": "127.0.0.1", "port": port, "protocol": "http"}],
        "outbounds": [ob, {"tag": "direct", "protocol": "freedom"}],
    }


def try_server(outbound):
    """Запустить временный xray и проверить, открывается ли через него Telegram."""
    tmp = os.path.join(HERE, "xray.test.json")
    with open(tmp, "w") as f:
        json.dump(make_config(outbound, TEST_PORT), f)
    os.chmod(tmp, 0o600)
    p = subprocess.Popen([XRAY, "run", "-c", tmp], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    try:
        time.sleep(2)
        if p.poll() is not None:
            err = p.stderr.read().decode("utf-8", "replace").strip().splitlines()
            return False, "xray не принял настройки: " + (err[-1] if err else "?")
        t = time.time()
        try:
            fetch(TEST_URL, timeout=15, proxy="http://127.0.0.1:{}".format(TEST_PORT))
        except urllib.error.HTTPError:
            pass  # любой HTTP-ответ от Telegram — значит, достучались
        return True, "{:.1f} с".format(time.time() - t)
    except Exception as e:
        return False, str(getattr(e, "reason", e))
    finally:
        p.terminate()
        try:
            p.wait(5)
        except subprocess.TimeoutExpired:
            p.kill()
        os.remove(tmp)


def cmd_configure():
    if not os.path.exists(XRAY):
        die("xray не установлен — сначала: python3 vpn/xray_setup.py install")
    servers = read_subscription()
    for i, (name, ob) in enumerate(servers, 1):
        ss = ob.get("streamSettings", {})
        print("[{}/{}] {} — {} {}/{}: ".format(i, len(servers), name, ob["protocol"],
              ss.get("network", "tcp"), ss.get("security", "none")), end="", flush=True)
        ok, info = try_server(ob)
        print(("OK, Telegram открылся за " if ok else "нет: ") + info)
        if ok:
            with open(XRAY_JSON + ".tmp", "w") as f:
                json.dump(make_config(ob, HTTP_PORT), f, ensure_ascii=False, indent=2)
            os.chmod(XRAY_JSON + ".tmp", 0o600)
            os.replace(XRAY_JSON + ".tmp", XRAY_JSON)
            print("\nВыбран сервер «{}». Настройки: {}".format(name, XRAY_JSON))
            cmd_stop(quiet=True)
            cmd_start()
            return
    die("ни один сервер из подписки не открыл Telegram")


# ---------------------------------------------------------------- запуск / статус

def _running_pid():
    try:
        pid = int(open(PID_FILE).read().strip())
        os.kill(pid, 0)
        with open("/proc/{}/cmdline".format(pid), "rb") as f:
            if b"xray" in f.read():
                return pid
    except (OSError, ValueError):
        pass
    return None


def cmd_start():
    pid = _running_pid()
    if pid:
        print("xray уже работает (pid {})".format(pid))
        return
    if not os.path.exists(XRAY_JSON):
        die("нет xray.json — сначала: python3 vpn/xray_setup.py configure")
    log = open(LOG_FILE, "a")
    p = subprocess.Popen([XRAY, "run", "-c", XRAY_JSON], stdout=log, stderr=log,
                         stdin=subprocess.DEVNULL, start_new_session=True)
    with open(PID_FILE, "w") as f:
        f.write(str(p.pid))
    time.sleep(2)
    if p.poll() is not None:
        die("xray сразу завершился, см. " + LOG_FILE)
    print("xray запущен (pid {}), прокси http://127.0.0.1:{}".format(p.pid, HTTP_PORT))


def cmd_stop(quiet=False):
    pid = _running_pid()
    if pid:
        os.kill(pid, signal.SIGTERM)
        print("xray остановлен")
    elif not quiet:
        print("xray не запущен")


def cmd_status():
    pid = _running_pid()
    print("xray: " + ("работает, pid {}".format(pid) if pid else "НЕ работает"))
    if not pid:
        return
    try:
        try:
            fetch(TEST_URL, timeout=15, proxy="http://127.0.0.1:{}".format(HTTP_PORT))
        except urllib.error.HTTPError:
            pass
        print("Telegram через прокси: доступен")
    except Exception as e:
        print("Telegram через прокси: НЕДОСТУПЕН ({}). Попробуйте configure — подберётся другой сервер."
              .format(getattr(e, "reason", e)))


def main():
    cmds = {"install": cmd_install, "configure": cmd_configure, "start": cmd_start,
            "stop": cmd_stop, "status": cmd_status}
    if len(sys.argv) != 2 or sys.argv[1] not in cmds:
        sys.exit(__doc__)
    cmds[sys.argv[1]]()


if __name__ == "__main__":
    main()
