"""Browser integration check for the actual planning page and bundled renderer.

Requires Firefox (FIREFOX or PATH) and the Python websocket-client package.
Uses an isolated profile and a loopback-only server; never edits the real plan.
"""

import functools
import http.server
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
import time
import unittest

import websocket


class PlanningViewerTest(unittest.TestCase):
    def test_read_only_view_and_fresh_source(self):
        source = Path(__file__).resolve().parents[1] / "docs/planning"
        firefox = os.environ.get("FIREFOX") or shutil.which("firefox")
        self.assertTrue(firefox, "Firefox is required for the browser test")
        with tempfile.TemporaryDirectory(prefix="oracle-planning-test-") as tmp:
            tmp = Path(tmp)
            public = tmp / "public"
            shutil.copytree(source, public)
            handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=public)
            server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            # Port 0 lets Firefox choose a free private automation port.
            log = (tmp / "firefox.log").open("w+")
            profile = tmp / "profile"
            profile.mkdir()
            browser = subprocess.Popen(
                [firefox, "--headless", "--no-remote", "--profile", str(profile),
                 "--remote-debugging-port", "0", "about:blank"],
                stdout=log, stderr=log,
            )
            ws = None
            try:
                import re
                endpoint = None
                for _ in range(60):
                    log.seek(0)
                    match = re.search(r"WebDriver BiDi listening on (ws://[^\s]+)", log.read())
                    if match:
                        endpoint = match.group(1).rstrip("/") + "/session"
                        break
                    time.sleep(0.1)
                self.assertIsNotNone(endpoint, "Firefox did not expose its local test endpoint")
                ws = websocket.create_connection(endpoint, timeout=20, suppress_origin=True)
                serial = 0

                def call(method, params):
                    nonlocal serial
                    serial += 1
                    ws.send(json.dumps(dict(id=serial, method=method, params=params)))
                    while True:
                        reply = json.loads(ws.recv())
                        if reply.get("id") == serial:
                            self.assertNotEqual(reply.get("type"), "error", reply)
                            return reply.get("result", {})

                call("session.new", {"capabilities": {}})
                context = call("browsingContext.create", {"type": "tab"})["context"]
                call("browsingContext.setViewport", {
                    "context": context, "viewport": {"width": 1600, "height": 1100},
                    "devicePixelRatio": 1,
                })
                url = f"http://127.0.0.1:{server.server_port}/"

                def evaluate(expression):
                    result = call("script.evaluate", {
                        "expression": expression, "target": {"context": context},
                        "awaitPromise": True,
                    })
                    self.assertEqual(result.get("type"), "success", result)
                    return result["result"].get("value")

                def wait_for_text(text):
                    for _ in range(40):
                        if evaluate(f"document.body.innerText.includes({json.dumps(text)})"):
                            return
                        time.sleep(0.15)
                    self.fail(f"Viewer did not render {text!r}: " + evaluate("document.body.innerText.slice(0,500)"))

                call("browsingContext.navigate", {"context": context, "url": url, "wait": "complete"})
                wait_for_text("TRUE compares descriptions")
                self.assertGreater(evaluate("document.querySelectorAll('svg foreignObject, svg text').length"), 15)
                self.assertFalse(evaluate("!!document.querySelector('[contenteditable=true], textarea')"))
                evaluate("document.querySelector('[title=\"Next Page\"]').click()")
                wait_for_text("Proposed weekly targets")
                evaluate("document.querySelector('[title=\"Previous Page\"]').click()")
                wait_for_text("TRUE compares descriptions")
                external = evaluate("JSON.stringify(performance.getEntriesByType('resource').map(r=>r.name).filter(u=>!u.startsWith(location.origin+'/')&&!u.startsWith('data:')))")
                self.assertEqual(json.loads(external), [], "Viewer fetched a resource outside its own host")

                # Change only the served test fixture, then reload the same page.
                diagram = public / "october-18-release.drawio"
                diagram.write_text(diagram.read_text().replace(
                    "October 18 release · dependency map", "Updated plan received"))
                call("browsingContext.reload", {"context": context, "wait": "complete"})
                wait_for_text("Updated plan received")

                # A missing source must produce a visible error, not an empty viewer.
                diagram.unlink()
                call("browsingContext.reload", {"context": context, "wait": "complete"})
                wait_for_text("Could not load diagram")
                call("session.end", {})
            finally:
                if ws is not None:
                    ws.close()
                browser.terminate()
                try:
                    browser.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    browser.kill()
                    browser.wait()
                log.close()
                server.shutdown()
                server.server_close()
                thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
