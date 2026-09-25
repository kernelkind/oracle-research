"""Exercise title navigation and durable decisions through the actual terminal CLI."""

import fcntl
import json
import os
from pathlib import Path
import pty
import select
import signal
import struct
import subprocess
import tempfile
import termios
import time
import unittest


ROOT = Path(__file__).resolve().parents[1]
BINARY = Path(os.environ.get("TITLE_REVIEW_BINARY", ROOT / "target/release/sse-mask-review"))


class TitleReviewNavigationTests(unittest.TestCase):
    def setUp(self):
        if not BINARY.is_file():
            self.skipTest("build sse-mask-review first")
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.session = self.root / "session.json"
        self.captured = b""

    def start(self, assessed=True):
        items = [dict(item_id=str(i), candidate_title=letter * 8,
                      baseline_title="Baseline", instances=[dict(instance=str(i), fragments=[letter])])
                 for i, letter in enumerate("ABC")]
        if assessed:
            for item in items:
                item["assessment"] = "Review this title."
        batch = self.root / "batch.json"
        batch.write_text(json.dumps(dict(schema_version=1, batch_id="navigation", candidate_version="T1",
                                        baseline_version="T0", items=items)))
        self.master, slave = pty.openpty()
        fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", 30, 100, 0, 0))
        self.process = subprocess.Popen([str(BINARY), "review-titles", str(batch), str(self.session)],
                                        stdin=slave, stdout=slave, stderr=slave,
                                        env={**os.environ, "TERM": "xterm"}, start_new_session=True)
        os.close(slave)
        self.addCleanup(self.close)
        self.wait_for(b"AAAAAAAA")

    def close(self):
        if self.process.poll() is None:
            os.killpg(self.process.pid, signal.SIGKILL)
            self.process.wait()
        os.close(self.master)

    def wait_for(self, text):
        deadline = time.monotonic() + 12
        self.captured = b""
        while time.monotonic() < deadline and self.process.poll() is None:
            if select.select([self.master], [], [], .1)[0]:
                try:
                    self.captured += os.read(self.master, 65536)
                except OSError:
                    break
                if text in self.captured:
                    return
        self.fail(f"Missing {text!r}: {self.captured!r}")

    def send(self, keys):
        os.write(self.master, keys)

    def stop(self):
        self.send(b"\x03")
        self.process.wait(timeout=12)
        self.assertEqual(self.process.returncode, 0)
        return json.loads(self.session.read_text())["session"]

    def test_rapid_arrows_reach_each_card_without_deciding(self):
        self.start()
        self.send(b"\x1b[C\x1b[C")
        self.wait_for(b"CCCCCCCC")
        state = self.stop()
        self.assertEqual(state["current_item"], "2")
        self.assertTrue(all(record["outcome"] is None for record in state["decisions"].values()))

    def test_navigation_does_not_write_until_exit(self):
        self.start()
        original = self.session.read_bytes()
        original_stat = self.session.stat()
        self.send(b"\x1b[C")
        self.wait_for(b"BBBBBBBB")
        self.assertEqual(self.session.read_bytes(), original)
        self.assertEqual(self.session.stat().st_ino, original_stat.st_ino)
        self.assertEqual(self.session.stat().st_mtime_ns, original_stat.st_mtime_ns)
        self.assertEqual(self.stop()["current_item"], "1")

    def test_legacy_titles_preserve_arrows_but_not_queued_approvals(self):
        self.start(assessed=False)
        self.send(b"\x1b[C\x1b[Caa")
        self.wait_for(b"CCCCCCCC")
        self.send(b"\x03")
        self.process.wait(timeout=12)
        self.assertEqual(self.process.returncode, 0)
        state = json.loads(self.session.read_text())["session"]
        self.assertTrue(all(record["outcome"] is None for record in state["decisions"].values()))


if __name__ == "__main__":
    unittest.main()
