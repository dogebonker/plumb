import json
import threading
import unittest
from urllib.request import Request, urlopen

from app import make_server
from store import Store


class AppTests(unittest.TestCase):
    def setUp(self):
        self.server = make_server(Store(), 0)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()

    def call(self, method, path, body=None):
        data = json.dumps(body).encode() if body is not None else None
        with urlopen(Request(self.url + path, data=data, method=method)) as response:
            return response.status, json.load(response)

    def test_post_creates_note(self):
        self.assertEqual(self.call("POST", "/notes", {"title": "milk"}),
                         (201, {"id": 1, "title": "milk", "archived": False}))

    def test_archive_marks_note(self):
        self.call("POST", "/notes", {"title": "milk"})
        self.assertEqual(self.call("POST", "/notes/1/archive"), (200, {"id": 1, "title": "milk", "archived": True}))

    def test_list_archived_returns_notes(self):
        self.call("POST", "/notes", {"title": "milk"})
        status, notes = self.call("GET", "/notes?archived=true")
        self.assertEqual((status, type(notes)), (200, list))
