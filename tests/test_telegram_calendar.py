import datetime as dt
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "telegram-bot"))

from common import icloud, invitation_ai
from listener import calendar_invites, listener


FUTURE_EVENT = {
    "kind": "event",
    "title": "Открытие выставки",
    "start": "2098-12-01T19:00+03:00",
    "end": None,
    "location": "Новый зал",
}


def inbox_entry(message_id, text="", files=None):
    return {"chat_id": 5, "message_id": message_id, "date": 1795557000,
            "text": text, "files": files or []}


class ExtractionTests(unittest.TestCase):
    def test_forwarded_photo_and_caption_have_original_date(self):
        with tempfile.TemporaryDirectory() as root:
            photo = Path(root) / "data" / "files" / "photo.jpg"
            photo.parent.mkdir(parents=True)
            photo.write_bytes(b"jpeg fixture")
            extracted = invitation_ai.InvitationExtractor("test-key", "test-model", root)
            result = {"status": "completed", "output": [
                {"type": "message", "content": [
                    {"type": "output_text", "text": json.dumps(FUTURE_EVENT)},
                ]},
            ]}
            entry = inbox_entry(7, "Завтра открытие", ["data/files/photo.jpg"])
            sent_at = dt.datetime(2026, 11, 23, 12, tzinfo=invitation_ai.MSK)
            entry["forward_date"] = int(sent_at.timestamp())
            with patch.object(extracted, "_post", return_value=result) as request:
                self.assertEqual(extracted.extract([entry]), FUTURE_EVENT)
            payload = json.loads(request.call_args.args[1])
            self.assertFalse(payload["store"])
            content = payload["input"][0]["content"]
            self.assertIn("2026-11-23", content[0]["text"])
            self.assertEqual(content[-1]["type"], "input_image")

    def test_only_saved_attachments_are_read(self):
        with tempfile.TemporaryDirectory() as root:
            extractor = invitation_ai.InvitationExtractor("test-key", "test-model", root)
            self.assertEqual(extractor._attachment("/outside/credentials.txt", 1024), (None, 0))


class CalendarTests(unittest.TestCase):
    def test_calendar_discovery_and_conditional_event_creation(self):
        calendar = icloud.ICloudCalendar("account@example.org", "fake-password", "Calendar")
        principal = b'''<D:multistatus xmlns:D="DAV:"><D:response><D:propstat><D:prop>
          <D:current-user-principal><D:href>/principal/</D:href></D:current-user-principal>
        </D:prop></D:propstat></D:response></D:multistatus>'''
        home = b'''<D:multistatus xmlns:D="DAV:" xmlns:C="urn:ietf:params:xml:ns:caldav">
          <D:response><D:propstat><D:prop><C:calendar-home-set>
            <D:href>/calendars/</D:href></C:calendar-home-set>
          </D:prop></D:propstat></D:response></D:multistatus>'''
        collections = b'''<D:multistatus xmlns:D="DAV:" xmlns:C="urn:ietf:params:xml:ns:caldav">
          <D:response><D:href>/calendars/default/</D:href><D:propstat><D:prop>
            <D:displayname>Calendar</D:displayname>
            <D:resourcetype><D:collection/><C:calendar/></D:resourcetype>
          </D:prop></D:propstat></D:response></D:multistatus>'''
        backend = "https://p02-caldav.icloud.com"
        start = invitation_ai.parse_time(FUTURE_EVENT["start"])
        end = start + dt.timedelta(hours=1)
        with patch.object(calendar, "_request", side_effect=[
            (backend + "/", 207, principal), (backend + "/principal/", 207, home),
            (backend + "/calendars/", 207, collections), ("", 201, b""), ("", 412, b""),
        ]) as request:
            self.assertTrue(calendar.add("Выставка", start, end, "Зал", "Детали\nвторая строка"))
            self.assertFalse(calendar.add("выставка", start, end, "Зал", ""))
        first_put, second_put = (c.args for c in request.call_args_list[-2:])
        self.assertEqual(first_put[1], second_put[1])
        self.assertEqual(first_put[-1]["If-None-Match"], "*")
        self.assertIn(b"DTSTART:20981201T160000Z\r\n", first_put[2])
        self.assertNotIn(b"ATTENDEE", first_put[2])

    def test_caldav_credentials_stay_on_icloud_hosts(self):
        calendar = icloud.ICloudCalendar("account@example.org", "fake-password", "Calendar")
        with patch("http.client.HTTPSConnection") as connection:
            with self.assertRaises(icloud.CalendarError):
                calendar._request("PROPFIND", "https://icloud.com.example.org/", b"", {})
            connection.assert_not_called()


class ListenerTests(unittest.TestCase):
    def test_only_owner_private_messages_reach_calendar(self):
        bot = MagicMock()
        with patch.object(listener, "load_state", return_value={}):
            receiver = listener.Listener(bot, {"owner_chat_id": 5, "allowed_chat_ids": [6]})
        receiver.calendar = MagicMock()
        with patch.object(listener, "save_to_inbox", return_value=(inbox_entry(11, "Выставка"), [])):
            for chat_id, chat_type in ((6, "private"), (5, "group"), (5, "private")):
                receiver.handle_update({"message": {
                    "chat": {"id": chat_id, "type": chat_type}, "message_id": 11, "text": "Выставка",
                }})
        receiver.calendar.handle.assert_called_once()

    def test_clarification_uses_original_invitation_and_clears_draft(self):
        bot = MagicMock()
        bot.send.return_value = {"message_id": 100}
        extractor, calendar = MagicMock(), MagicMock()
        extractor.extract.side_effect = [
            {"kind": "unclear", "missing": "time"}, FUTURE_EVENT,
        ]
        calendar.add.return_value = True
        state = {}
        handler = calendar_invites.CalendarInvitations(bot, state)
        original, reply = inbox_entry(7, "Выставка 1 декабря"), inbox_entry(8, "19:00")
        with patch.object(handler, "_clients", return_value=(extractor, calendar)):
            handler.handle(original, {}, [])
            handler.handle(reply, {"reply_to_message": {"message_id": 100}}, [])
        self.assertEqual(extractor.extract.call_args.args[0], [original, reply])
        self.assertEqual(state["calendar_drafts"], {})
        args = calendar.add.call_args.args
        self.assertEqual(args[2] - args[1], dt.timedelta(hours=1))
        self.assertIn("Записал", bot.send.call_args.args[0])

    def test_non_event_does_not_touch_calendar(self):
        bot, extractor, calendar = MagicMock(), MagicMock(), MagicMock()
        extractor.extract.return_value = {"kind": "other"}
        handler = calendar_invites.CalendarInvitations(bot, {})
        with patch.object(handler, "_clients", return_value=(extractor, calendar)):
            handler.handle(inbox_entry(7, "Обычная заметка"), {}, [])
        calendar.add.assert_not_called()
        bot.send.assert_not_called()


if __name__ == "__main__":
    unittest.main()
