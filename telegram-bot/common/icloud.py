"""Запись событий в iCloud Calendar по CalDAV."""

import base64
import datetime as dt
import hashlib
import http.client
import re
import unicodedata
import urllib.parse
from xml.etree import ElementTree

DAV = "DAV:"
CALDAV = "urn:ietf:params:xml:ns:caldav"
ROOT = "https://caldav.icloud.com/"
HOST = re.compile(r"(?:p\d+-)?caldav\.icloud\.com")


class CalendarError(Exception):
    pass


def _name(namespace, name):
    return "{{{}}}{}".format(namespace, name)


def _utc(value):
    return value.astimezone(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _text(value):
    value = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", value)
    return (value.replace("\\", "\\\\").replace("\r\n", "\n").replace("\r", "\n")
            .replace("\n", "\\n").replace(";", "\\;").replace(",", "\\,"))


def _fold(line):
    # RFC 5545 ограничивает строку в байтах, а не в символах.
    result = []
    current = bytearray()
    for char in line:
        chunk = char.encode("utf-8")
        if len(current) + len(chunk) > 75:
            result.append(bytes(current))
            current = bytearray(b" ")
        current.extend(chunk)
    result.append(bytes(current))
    return b"\r\n".join(result)


def event_uid(title, start):
    normalized = " ".join(unicodedata.normalize("NFKC", title).casefold().split())
    value = "{}\n{}".format(normalized, _utc(start)).encode("utf-8")
    return hashlib.sha256(value).hexdigest() + "@nas-telegram-calendar"


def _event(uid, title, start, end, location, description):
    lines = [
        "BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Synology Telegram Bot//Calendar//RU",
        "BEGIN:VEVENT", "UID:" + uid, "DTSTAMP:" + _utc(dt.datetime.now(dt.timezone.utc)),
        "DTSTART:" + _utc(start), "DTEND:" + _utc(end), "SUMMARY:" + _text(title),
    ]
    if location:
        lines.append("LOCATION:" + _text(location))
    if description:
        lines.append("DESCRIPTION:" + _text(description))
    lines.extend(("END:VEVENT", "END:VCALENDAR"))
    return b"\r\n".join(map(_fold, lines)) + b"\r\n"


class ICloudCalendar:
    def __init__(self, account, password, name):
        credentials = "{}:{}".format(account, password).encode("utf-8")
        self._authorization = "Basic " + base64.b64encode(credentials).decode("ascii")
        self.name = name
        self._collection = None

    def _request(self, method, url, body, headers):
        headers = dict(headers, Authorization=self._authorization)
        headers["User-Agent"] = "SynologyTelegramCalendar/1"
        for _ in range(4):
            parts = urllib.parse.urlsplit(url)
            if (parts.scheme != "https" or not HOST.fullmatch(parts.hostname or "")
                    or parts.username is not None or parts.port not in (None, 443)):
                raise CalendarError("iCloud вернул неожиданный адрес календаря")
            target = urllib.parse.urlunsplit(("", "", parts.path or "/", parts.query, ""))
            conn = http.client.HTTPSConnection(parts.hostname, timeout=12)
            try:
                conn.request(method, target, body=body, headers=headers)
                response = conn.getresponse()
                status, location = response.status, response.getheader("Location")
                if status in (301, 302, 307, 308) and location:
                    url = urllib.parse.urljoin(url, location)
                    continue
                return url, status, response.read(2 * 1024 * 1024 + 1)
            except (OSError, http.client.HTTPException):
                raise CalendarError("сетевая ошибка при обращении к iCloud") from None
            finally:
                conn.close()
        raise CalendarError("iCloud вернул слишком много перенаправлений")

    def _properties(self, url, depth, *properties):
        request = ElementTree.Element(_name(DAV, "propfind"))
        prop = ElementTree.SubElement(request, _name(DAV, "prop"))
        for name in properties:
            ElementTree.SubElement(prop, name)
        url, status, body = self._request(
            "PROPFIND", url, ElementTree.tostring(request),
            {"Content-Type": "application/xml; charset=utf-8", "Depth": str(depth)},
        )
        if status != 207:
            raise CalendarError("iCloud вернул HTTP {}".format(status))
        if len(body) > 2 * 1024 * 1024:
            raise CalendarError("ответ iCloud слишком большой")
        try:
            return url, ElementTree.fromstring(body)
        except ElementTree.ParseError:
            raise CalendarError("iCloud вернул некорректный список календарей") from None

    def _discover_link(self, url, name):
        url, properties = self._properties(url, 0, name)
        href = properties.findtext(".//{}/{}".format(name, _name(DAV, "href")))
        if not href:
            raise CalendarError("iCloud не вернул ссылку на календарь")
        return urllib.parse.urljoin(url, href)

    def collection(self):
        if self._collection:
            return self._collection
        principal = self._discover_link(ROOT, _name(DAV, "current-user-principal"))
        home = self._discover_link(principal, _name(CALDAV, "calendar-home-set"))
        display, resource = _name(DAV, "displayname"), _name(DAV, "resourcetype")
        url, results = self._properties(home, 1, display, resource)
        matches = set()
        for response in results.findall(_name(DAV, "response")):
            href = response.findtext(_name(DAV, "href"))
            if (href and response.findtext(".//" + display) == self.name
                    and response.find(".//{}/{}".format(resource, _name(CALDAV, "calendar"))) is not None):
                matches.add(urllib.parse.urljoin(url, href).rstrip("/") + "/")
        if len(matches) != 1:
            raise CalendarError("iCloud не нашёл единственный календарь с указанным именем")
        self._collection = matches.pop()
        return self._collection

    def add(self, title, start, end, location, description):
        uid = event_uid(title, start)
        url = urllib.parse.urljoin(self.collection(), uid + ".ics")
        _, status, _ = self._request(
            "PUT", url, _event(uid, title, start, end, location, description),
            {"Content-Type": "text/calendar; charset=utf-8", "If-None-Match": "*"},
        )
        if status == 412:
            return False
        if status not in (200, 201, 204):
            raise CalendarError("iCloud не сохранил событие (HTTP {})".format(status))
        return True
