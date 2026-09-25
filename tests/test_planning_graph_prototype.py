"""Browser test for the read-only, focusable release-plan graph prototype."""

import base64
import functools
import http.server
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import threading
import time
import unittest

import websocket


class PlanningGraphPrototypeTest(unittest.TestCase):
    def test_focus_expansion_and_source_refresh(self):
        source = Path(__file__).resolve().parents[1] / "docs/planning"
        firefox = os.environ.get("FIREFOX") or shutil.which("firefox")
        self.assertTrue(firefox, "Firefox is required for the browser test")
        with tempfile.TemporaryDirectory(prefix="oracle-planning-graph-test-") as tmp:
            tmp = Path(tmp)
            public = tmp / "public"
            shutil.copytree(source, public)
            (public / "october-18-release.drawio").unlink()
            handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=public)
            server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            log = (tmp / "firefox.log").open("w+")
            home = tmp / "home"
            home.mkdir()
            browser = subprocess.Popen(
                [firefox, "--headless", "--no-remote",
                 "--remote-debugging-port", "0", "about:blank"],
                stdout=log, stderr=log,
                env={**os.environ, "HOME": str(home)},
            )
            ws = None
            try:
                endpoint = None
                for _ in range(300):
                    log.seek(0)
                    match = re.search(r"WebDriver BiDi listening on (ws://[^\s]+)", log.read())
                    if match:
                        endpoint = match.group(1).rstrip("/") + "/session"
                        break
                    time.sleep(0.1)
                log.seek(0)
                self.assertIsNotNone(endpoint, "Firefox did not expose its local test endpoint: " + log.read()[-1000:])
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

                def evaluate(expression):
                    result = call("script.evaluate", {
                        "expression": expression, "target": {"context": context},
                        "awaitPromise": True,
                    })
                    self.assertEqual(result.get("type"), "success", result)
                    return result["result"].get("value")

                def wait_for(predicate):
                    for _ in range(60):
                        if evaluate(predicate):
                            return
                        time.sleep(0.1)
                    self.fail("Prototype did not reach expected state: " + predicate)

                def capture(name):
                    if directory := os.environ.get("PLANNING_SCREENSHOT_DIR"):
                        destination = Path(directory)
                        destination.mkdir(parents=True, exist_ok=True)
                        screenshot = call("browsingContext.captureScreenshot", {"context": context})
                        (destination / f"{name}.png").write_bytes(base64.b64decode(screenshot["data"]))

                call("session.new", {"capabilities": {}})
                context = call("browsingContext.create", {"type": "tab"})["context"]
                call("browsingContext.setViewport", {
                    "context": context, "viewport": {"width": 1280, "height": 800},
                    "devicePixelRatio": 1,
                })
                url = f"http://127.0.0.1:{server.server_port}/graph-prototype.html"
                call("browsingContext.navigate", {"context": context, "url": url, "wait": "complete"})
                wait_for("document.querySelector('#graph-status')?.textContent.includes('Showing')")
                self.assertEqual(evaluate("document.querySelector('#focus-task').value"), "02")
                self.assertEqual(evaluate("document.querySelector('#depth').value"), "1")
                counts = evaluate("document.querySelector('#graph-status').textContent.match(/Showing (\\d+) of (\\d+) tasks/)?.slice(1).join(',')")
                focused_count, total_count = map(int, counts.split(","))
                self.assertGreater(focused_count, 1)
                self.assertLess(focused_count, total_count)
                self.assertIn("other links", evaluate("document.querySelector('#graph-status').textContent"))
                self.assertIn("needed to finish", evaluate("document.querySelector('#details').innerText.toLowerCase()"))
                self.assertIn("Handle node equivalence and TRUE cycles", evaluate("document.querySelector('#details').innerText"))
                self.assertIn("IN PROGRESS", evaluate("document.querySelector('#details').innerText"))
                self.assertTrue(evaluate("document.querySelector('#graph canvas')?.getBoundingClientRect().width > 500"))
                capture("focused")

                evaluate("document.querySelector('#direction').value = 'before'; document.querySelector('#direction').dispatchEvent(new Event('change'))")
                before_count = int(evaluate("document.querySelector('#graph-status').textContent.match(/Showing (\\d+)/)[1]"))
                self.assertLess(before_count, focused_count)
                evaluate("document.querySelector('#direction').value = 'both'; document.querySelector('#direction').dispatchEvent(new Event('change'))")
                evaluate("document.querySelector('#depth').value = '2'; document.querySelector('#depth').dispatchEvent(new Event('change'))")
                two_step_count = int(evaluate("document.querySelector('#graph-status').textContent.match(/Showing (\\d+)/)[1]"))
                self.assertGreater(two_step_count, focused_count)
                evaluate("[...document.querySelectorAll('#details .related button')].find(button => button.textContent.startsWith('25 ·'))?.click()")
                wait_for("document.querySelector('#focus-task').value === '25'")
                evaluate("document.querySelector('#go-back').click()")
                wait_for("document.querySelector('#focus-task').value === '02'")

                evaluate("document.querySelector('#depth').value = '0'; document.querySelector('#depth').dispatchEvent(new Event('change'))")
                wait_for("document.querySelector('#graph-status').textContent.includes('Showing 1 of ')")
                evaluate("document.querySelector('#show-all').click()")
                wait_for(f"document.querySelector('#graph-status').textContent.includes('Showing {total_count} of {total_count} tasks')")
                self.assertGreaterEqual(total_count, 25)
                self.assertTrue(evaluate("document.querySelector('#depth').disabled"))
                capture("all-tasks")

                # The graph must be derived from the served task data, not draw.io.
                data_file = public / "release-plan.json"
                data = json.loads(data_file.read_text())
                next(task for task in data["tasks"] if task["id"] == "02")["title"] = "Review refreshed 100-note hierarchy"
                data_file.write_text(json.dumps(data))
                call("browsingContext.reload", {"context": context, "wait": "complete"})
                wait_for("document.querySelector('#details')?.innerText.includes('Review refreshed 100-note hierarchy')")
                data["links"][0]["target"] = "99"
                data_file.write_text(json.dumps(data))
                call("browsingContext.reload", {"context": context, "wait": "complete"})
                wait_for("document.querySelector('#graph-status')?.textContent.includes('Invalid or duplicate link')")
                external = evaluate("JSON.stringify(performance.getEntriesByType('resource').map(r => r.name).filter(u => !u.startsWith(location.origin + '/') && !u.startsWith('data:')))")
                self.assertEqual(json.loads(external), [], "Prototype must not fetch resources off-host")
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
