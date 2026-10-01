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

                def check_routes():
                    wait_for("document.querySelector('#graph-status')?.textContent.includes('Layout ready')")
                    geometry = json.loads(evaluate("""JSON.stringify((() => {
                        const cy = document.querySelector('#graph')._cyreg.cy;
                        return {
                            nodes: cy.nodes(':visible').map(node => ({
                                id: node.id(), box: node.boundingBox({includeLabels: false})})),
                            edges: cy.edges(':visible').map(edge => ({
                                id: edge.id(), source: edge.source().id(), target: edge.target().id(),
                                points: [edge.sourceEndpoint(), ...(edge.segmentPoints() || []),
                                         edge.targetEndpoint()],
                                arrow: edge.style('target-arrow-shape'),
                                line: edge.style('line-style')})),
                        };
                    })())"""))
                    edges = geometry["edges"]
                    for index, edge in enumerate(edges):
                        self.assertEqual(edge["arrow"], "triangle", edge["id"])
                        self.assertEqual(edge["line"], "dashed" if edge["id"].endswith("helpful") else "solid")
                        for other in edges[index + 1:]:
                            if edge["target"] == other["target"]:
                                first, second = edge["points"][-1], other["points"][-1]
                                separation = ((first["x"] - second["x"]) ** 2
                                              + (first["y"] - second["y"]) ** 2) ** 0.5
                                self.assertGreater(separation, 8,
                                                   f"Incoming arrows overlap: {edge['id']} and {other['id']}")
                        for first, second in zip(edge["points"], edge["points"][1:]):
                            self.assertLess(min(abs(first["x"] - second["x"]),
                                                abs(first["y"] - second["y"])), 0.01, edge["id"])
                            for node in geometry["nodes"]:
                                if node["id"] in (edge["source"], edge["target"]):
                                    continue
                                box = node["box"]
                                crosses_box = (
                                    min(first["x"], second["x"]) < box["x2"] - 0.01
                                    and max(first["x"], second["x"]) > box["x1"] + 0.01
                                    and min(first["y"], second["y"]) < box["y2"] - 0.01
                                    and max(first["y"], second["y"]) > box["y1"] + 0.01)
                                self.assertFalse(crosses_box, f"{edge['id']} crosses task {node['id']}")
                    return geometry

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
                url = f"http://127.0.0.1:{server.server_port}/"
                call("browsingContext.navigate", {"context": context, "url": url, "wait": "complete"})
                wait_for("document.querySelector('#graph-status')?.textContent.includes('Showing')")
                wait_for("document.querySelector('#graph-status')?.textContent.includes('Layout ready')")
                self.assertFalse(evaluate("[...document.querySelectorAll('#details .related button')].some(button => button.textContent.startsWith('25 ·'))"),
                                 "HR02-only task 25 must not be a dependency of the current task 02")
                self.assertEqual(evaluate("document.querySelector('#track')?.value"), "release")
                self.assertEqual(json.loads(evaluate("JSON.stringify([...document.querySelector('#track').options].map(option => option.textContent))")),
                                 ["Required release", "Optional model", "Both"])
                plan = json.loads((public / "release-plan.json").read_text())
                shared = {"01", "02", "03", "04", "09", "17", "20", "21", "22", "23", "24", "27", "28", "30"}
                release = {"12", "13", "14", "15", "16"}
                model = {"05", "06", "07", "08", "10", "11", "18", "29"}
                historical = {"25", "26"}
                for task in plan["tasks"]:
                    expected = ("shared" if task["id"] in shared else "release" if task["id"] in release
                                else "model" if task["id"] in model else "historical")
                    self.assertEqual(task["track"], expected, task["title"])
                self.assertFalse(any(link["kind"] == "required" and link["source"] in model
                                     and link["target"] in release | shared for link in plan["links"]),
                                 "Optional-model work must not become a required-release gate")

                def picker_ids():
                    return set(json.loads(evaluate("JSON.stringify([...document.querySelector('#focus-task').options].map(option => option.value))")))

                def visible_ids():
                    return {node["id"] for node in check_routes()["nodes"]}

                self.assertEqual(picker_ids(), shared | release)
                capture("required-release-focused")
                evaluate("document.querySelector('#show-all').click()")
                self.assertEqual(visible_ids(), shared | release)
                self.assertIn("Required release", evaluate("document.querySelector('#graph-status').textContent"))
                capture("required-release")

                evaluate("document.querySelector('#track').value = 'model'; document.querySelector('#track').dispatchEvent(new Event('change'))")
                self.assertEqual(picker_ids(), shared | model)
                self.assertEqual(visible_ids(), shared | model)
                self.assertEqual(evaluate("document.querySelector('#focus-task').value"), "02")
                self.assertIn("Shared", evaluate("document.querySelector('#details .task-track').textContent"))
                capture("optional-model")
                self.assertIn("Shared", evaluate("document.querySelector('#graph')._cyreg.cy.getElementById('02').data('label')"))
                self.assertIn("Optional model", evaluate("document.querySelector('#graph')._cyreg.cy.getElementById('06').data('label')"))

                # Compose with the completed-task filter when that control is present.
                if evaluate("!!document.querySelector('#hide-completed')"):
                    completed = {task["id"] for task in plan["tasks"] if task["status"] == "COMPLETE"}
                    evaluate("document.querySelector('#hide-completed').click()")
                    self.assertEqual(visible_ids(), (shared | model) - completed)
                    evaluate("document.querySelector('#track').value = 'release'; document.querySelector('#track').dispatchEvent(new Event('change'))")
                    self.assertTrue(evaluate("document.querySelector('#hide-completed').checked"))
                    self.assertEqual(visible_ids(), (shared | release) - completed)
                    evaluate("document.querySelector('#hide-completed').click()")
                    evaluate("document.querySelector('#track').value = 'model'; document.querySelector('#track').dispatchEvent(new Event('change'))")

                evaluate("document.querySelector('#focus-selected').click()")
                self.assertTrue(visible_ids() <= shared | model)
                self.assertIn("Required release · outside this view", evaluate("document.querySelector('#details').innerText"))
                evaluate("[...document.querySelectorAll('#details .related button')].find(button => button.textContent.startsWith('14 ·')).click()")
                self.assertEqual(evaluate("document.querySelector('#track').value"), "release")
                self.assertEqual(evaluate("document.querySelector('#focus-task').value"), "14")
                self.assertTrue(visible_ids() <= shared | release)
                evaluate("document.querySelector('#go-back').click()")
                self.assertEqual(evaluate("document.querySelector('#track').value"), "model")
                self.assertEqual(evaluate("document.querySelector('#focus-task').value"), "02")

                evaluate("document.querySelector('#track').value = 'release'; document.querySelector('#track').dispatchEvent(new Event('change'))")
                evaluate("document.querySelector('#focus-task').value = '17'; document.querySelector('#focus-task').dispatchEvent(new Event('change'))")
                evaluate("[...document.querySelectorAll('#details .related button')].find(button => button.textContent.startsWith('05 ·')).click()")
                self.assertEqual(evaluate("document.querySelector('#track').value"), "model")
                self.assertEqual(evaluate("document.querySelector('#focus-task').value"), "05")
                evaluate("document.querySelector('#go-back').click()")
                self.assertEqual(evaluate("document.querySelector('#track').value"), "release")
                self.assertEqual(evaluate("document.querySelector('#focus-task').value"), "17")

                evaluate("document.querySelector('#focus-task').value = '13'; document.querySelector('#focus-task').dispatchEvent(new Event('change'))")
                evaluate("document.querySelector('#depth').value = '2'; document.querySelector('#depth').dispatchEvent(new Event('change'))")
                evaluate("document.querySelector('#direction').value = 'before'; document.querySelector('#direction').dispatchEvent(new Event('change'))")
                evaluate("document.querySelector('#show-inputs').click()")
                evaluate("document.querySelector('#track').value = 'model'; document.querySelector('#track').dispatchEvent(new Event('change'))")
                self.assertIn(evaluate("document.querySelector('#focus-task').value"), shared | model)
                self.assertEqual(evaluate("document.querySelector('#depth').value"), "2")
                self.assertEqual(evaluate("document.querySelector('#direction').value"), "before")
                self.assertFalse(evaluate("document.querySelector('#show-inputs').checked"))
                self.assertTrue(visible_ids() <= shared | model)
                self.assertFalse(any(edge["id"].endswith("helpful") for edge in check_routes()["edges"]))

                evaluate("document.querySelector('#track').value = 'both'; document.querySelector('#track').dispatchEvent(new Event('change'))")
                self.assertEqual(picker_ids(), shared | release | model | historical)
                evaluate("document.querySelector('#show-all').click()")
                self.assertEqual(visible_ids(), shared | release | model | historical)
                capture("both-tracks")
                evaluate("document.querySelector('#focus-task').value = '02'; document.querySelector('#focus-task').dispatchEvent(new Event('change'))")
                evaluate("document.querySelector('#depth').value = '1'; document.querySelector('#depth').dispatchEvent(new Event('change'))")
                evaluate("document.querySelector('#direction').value = 'both'; document.querySelector('#direction').dispatchEvent(new Event('change'))")
                evaluate("document.querySelector('#show-inputs').click()")
                self.assertEqual(evaluate("document.title"), "Oracle release plan · task graph")
                self.assertFalse(evaluate("document.body.innerText.includes('Earlier draw.io')"))
                for retired in ("october-18-release.drawio", "vendor/viewer-static.min.js", "vendor/LICENSE.drawio"):
                    self.assertFalse((source / retired).exists(), f"Retired viewer still present: {retired}")
                self.assertEqual(evaluate("document.querySelector('#focus-task').value"), "02")
                self.assertEqual(evaluate("document.querySelector('#depth').value"), "1")
                counts = evaluate("document.querySelector('#graph-status').textContent.match(/Showing (\\d+) of (\\d+) tasks/)?.slice(1).join(',')")
                focused_count, total_count = map(int, counts.split(","))
                self.assertGreater(focused_count, 1)
                self.assertLess(focused_count, total_count)
                self.assertIn("other links", evaluate("document.querySelector('#graph-status').textContent"))
                self.assertIn("needed to finish", evaluate("document.querySelector('#details').innerText.toLowerCase()"))
                self.assertIn("IN PROGRESS", evaluate("document.querySelector('#details').innerText"))
                self.assertIn("Latest saved test export: 1,740 hierarchy nodes; original subjects and masks preserved.",
                              evaluate("document.querySelector('#details').innerText"))
                hierarchy_details = evaluate("document.querySelector('#details').innerText")
                for pending in (
                    "Same-worded Food preparation/ingredients siblings beneath Food have been combined",
                    "two further bounded passes completed",
                    "The two existing pair-selection rules now nominate no unjudged pairs",
                    "not proof that important parent relationships are complete",
                    "parent links outside the current selection rules",
                    "general conflict handling and production adoption",
                    "bagel-making and pie-making branches disconnected from Food",
                    "experimental Dietary practices / Diets merge",
                    "Launch-scale construction is not this completion gate",
                ):
                    self.assertIn(pending, hierarchy_details)
                self.assertTrue(evaluate("document.querySelector('#graph canvas')?.getBoundingClientRect().width > 500"))
                self.assertGreaterEqual(sum(edge["target"] == "02" for edge in check_routes()["edges"]), 2)
                capture("focused")

                evaluate("document.querySelector('#focus-task').value = '06'; document.querySelector('#focus-task').dispatchEvent(new Event('change'))")
                mixed_routes = check_routes()
                self.assertTrue(any(edge["line"] == "dashed" for edge in mixed_routes["edges"]))
                self.assertTrue(any(edge["line"] == "solid" for edge in mixed_routes["edges"]))
                capture("pilot-connections")
                evaluate("document.querySelector('#show-inputs').click()")
                self.assertTrue(all(edge["line"] == "solid" for edge in check_routes()["edges"]))
                evaluate("document.querySelector('#show-inputs').click()")
                self.assertEqual(check_routes(), mixed_routes, "The same view must produce the same routes")
                evaluate("document.querySelector('#focus-task').value = '02'; document.querySelector('#focus-task').dispatchEvent(new Event('change'))")
                check_routes()

                evaluate("document.querySelector('#direction').value = 'before'; document.querySelector('#direction').dispatchEvent(new Event('change'))")
                before_count = int(evaluate("document.querySelector('#graph-status').textContent.match(/Showing (\\d+)/)[1]"))
                self.assertLess(before_count, focused_count)
                evaluate("document.querySelector('#direction').value = 'both'; document.querySelector('#direction').dispatchEvent(new Event('change'))")
                evaluate("document.querySelector('#depth').value = '2'; document.querySelector('#depth').dispatchEvent(new Event('change'))")
                two_step_count = int(evaluate("document.querySelector('#graph-status').textContent.match(/Showing (\\d+)/)[1]"))
                self.assertGreater(two_step_count, focused_count)
                evaluate("[...document.querySelectorAll('#details .related button')].find(button => button.textContent.startsWith('03 ·'))?.click()")
                wait_for("document.querySelector('#focus-task').value === '03'")
                self.assertFalse(evaluate("[...document.querySelectorAll('#details .related button')].some(button => button.textContent.startsWith('26 ·'))"),
                                 "Earlier equal-note collapse must not gate the current task 03")
                self.assertFalse(evaluate("[...document.querySelectorAll('#details .related button')].some(button => button.textContent.startsWith('25 ·'))"),
                                 "HR02-only task 25 must not be a dependency of the current task 03")
                evaluate("document.querySelector('#go-back').click()")
                wait_for("document.querySelector('#focus-task').value === '02'")

                evaluate("document.querySelector('#depth').value = '0'; document.querySelector('#depth').dispatchEvent(new Event('change'))")
                wait_for("document.querySelector('#graph-status').textContent.includes('Showing 1 of ')")
                self.assertEqual(check_routes()["edges"], [])
                evaluate("document.querySelector('#show-all').click()")
                wait_for(f"document.querySelector('#graph-status').textContent.includes('Showing {total_count} of {total_count} tasks')")
                self.assertGreaterEqual(total_count, 25)
                self.assertTrue(evaluate("document.querySelector('#depth').disabled"))
                check_routes()
                capture("all-tasks")
                evaluate("document.querySelector('#focus-task').value = '25'; document.querySelector('#focus-task').dispatchEvent(new Event('change'))")
                wait_for("document.querySelector('#details h2').textContent.startsWith('25 ·')")
                self.assertEqual(evaluate("document.querySelector('#details .task-status').textContent"), "COMPLETE")
                self.assertEqual(evaluate("document.querySelectorAll('#details .related button').length"), 0)
                self.assertEqual([node["id"] for node in check_routes()["nodes"]], ["25"])
                evaluate("document.querySelector('#focus-task').value = '26'; document.querySelector('#focus-task').dispatchEvent(new Event('change'))")
                wait_for("document.querySelector('#details h2').textContent.startsWith('26 ·')")
                self.assertEqual(evaluate("document.querySelector('#details .task-status').textContent"), "VALIDATION PENDING")
                self.assertEqual(evaluate("document.querySelectorAll('#details .related button').length"), 0)
                self.assertEqual([node["id"] for node in check_routes()["nodes"]], ["26"])
                evaluate("document.querySelector('#focus-task').value = '04'; document.querySelector('#focus-task').dispatchEvent(new Event('change'))")
                wait_for("document.querySelector('#details h2').textContent.startsWith('04 ·')")
                self.assertEqual(evaluate("document.querySelector('#details h2').textContent"), "04 · Define node sort score")
                self.assertEqual(evaluate("document.querySelector('#details .task-status').textContent"), "IN PROGRESS")
                score_details = evaluate("document.querySelector('#details').innerText")
                self.assertIn("one sorting score per note within a hierarchy node", score_details)
                self.assertIn("candidate components, not fixed requirements", score_details)
                self.assertIn("No final formula or model inputs are selected", score_details)
                self.assertIn("11 clear Coffee/Eggs/Music pair preferences", score_details)
                self.assertIn("One Coffee comparison repeated successfully", score_details)
                self.assertTrue(evaluate("[...document.querySelectorAll('#details .related button')].some(button => button.textContent.startsWith('27 ·'))"))

                evaluate("document.querySelector('#focus-task').value = '17'; document.querySelector('#focus-task').dispatchEvent(new Event('change'))")
                wait_for("document.querySelector('#details h2').textContent.startsWith('17 ·')")
                self.assertIn("Additional teacher outputs needed for sorting remain undecided", evaluate("document.querySelector('#details').innerText"))
                self.assertEqual(evaluate("document.querySelector('#details .task-status').textContent"), "IN PROGRESS")
                teacher_details = evaluate("document.querySelector('#details').innerText")
                self.assertTrue(evaluate("[...document.querySelectorAll('#details .related button')].some(button => button.textContent.startsWith('30 ·'))"))
                self.assertIn("Final teacher selection waits for prompt stress-testing", teacher_details)
                self.assertIn("Comparison work may continue", teacher_details)
                evaluate("document.querySelector('#depth').value = '1'; document.querySelector('#depth').dispatchEvent(new Event('change'))")
                self.assertTrue(any(edge["source"] == "30" and edge["target"] == "17" and edge["line"] == "solid" for edge in check_routes()["edges"]))
                for progress in ("Sol low assessed on 20 posts", "20 posts (684 masks)",
                                 "using saved Astra subjects", "Agent reviews",
                                 "Combined Sol subject-and-mask process and resulting hierarchy comparison remain unvalidated",
                                 "Subscription quota use remains unmeasured",
                                 "Mask teacher and final selection remain open"):
                    self.assertIn(progress, teacher_details)
                evaluate("document.querySelector('#focus-task').value = '05'; document.querySelector('#focus-task').dispatchEvent(new Event('change'))")
                wait_for("document.querySelector('#details h2').textContent.startsWith('05 ·')")
                self.assertIn("Additional model outputs needed for sorting remain undecided", evaluate("document.querySelector('#details').innerText"))
                self.assertTrue(evaluate("[...document.querySelectorAll('#details .related button')].some(button => button.textContent.startsWith('17 ·'))"))

                evaluate("document.querySelector('#focus-task').value = '27'; document.querySelector('#focus-task').dispatchEvent(new Event('change'))")
                wait_for("document.querySelector('#details h2').textContent.startsWith('27 ·')")
                self.assertEqual(evaluate("document.querySelector('#details .task-status').textContent"), "IN PROGRESS")
                self.assertEqual(evaluate("document.querySelector('#details h2').textContent"), "27 · Order notes within each node")
                self.assertIn("using the score defined in 04", evaluate("document.querySelector('#details').innerText"))
                self.assertIn("Recursive sorting and parent-child score transfer are out of scope", evaluate("document.querySelector('#details').innerText"))
                ordering_details = evaluate("document.querySelector('#details').innerText")
                self.assertIn("Photography's three-post order and the accepted seven-post Eggs order", ordering_details)
                self.assertIn("Either order is acceptable for four about-equal Coffee pairs", ordering_details)
                self.assertIn("identical scores are not required", ordering_details)
                self.assertIn("Broader-hierarchy validation and a production method remain open", ordering_details)
                self.assertTrue(evaluate("[...document.querySelectorAll('#details .related button')].some(button => button.textContent.startsWith('04 ·'))"))
                self.assertTrue(evaluate("[...document.querySelectorAll('#details .related button')].some(button => button.textContent.startsWith('03 ·'))"))
                evaluate("document.querySelector('#focus-task').value = '13'; document.querySelector('#focus-task').dispatchEvent(new Event('change'))")
                wait_for("document.querySelector('#details h2').textContent.startsWith('13 ·')")
                self.assertEqual(evaluate("document.querySelector('#details .task-status').textContent"), "IN PROGRESS")
                self.assertIn("The current draft covers only the opening proposal", evaluate("document.querySelector('#details').innerText"))
                self.assertTrue(evaluate("[...document.querySelectorAll('#details .related button')].some(button => button.textContent.startsWith('14 ·'))"))
                self.assertTrue(evaluate("[...document.querySelectorAll('#details .related button')].some(button => button.textContent.startsWith('15 ·'))"))

                for task_id, preparation in (("03", "Corpus preparation underway"), ("15", "Integration preparation underway")):
                    evaluate(f"document.querySelector('#focus-task').value = '{task_id}'; document.querySelector('#focus-task').dispatchEvent(new Event('change'))")
                    wait_for(f"document.querySelector('#details h2').textContent.startsWith('{task_id} ·')")
                    self.assertEqual(evaluate("document.querySelector('#details .task-status').textContent"), "IN PROGRESS")
                    self.assertIn(preparation, evaluate("document.querySelector('#details').innerText"))

                evaluate("document.querySelector('#focus-task').value = '03'; document.querySelector('#focus-task').dispatchEvent(new Event('change'))")
                wait_for("document.querySelector('#details h2').textContent.startsWith('03 ·')")
                self.assertIn("New note generation is on hold pending prompt stress-testing", evaluate("document.querySelector('#details').innerText"))
                evaluate("[...document.querySelectorAll('#details .related button')].find(button => button.textContent.startsWith('30 ·')).click()")
                wait_for("document.querySelector('#details h2').textContent === '30 · Stress-test prompts'")
                self.assertEqual(evaluate("document.querySelector('#details .task-status').textContent"), "IN PROGRESS")
                self.assertIn("Shared", evaluate("document.querySelector('#details .task-track').textContent"))
                self.assertIn("Corpus selection and offline preparation may continue", evaluate("document.querySelector('#details').innerText"))
                evaluate("document.querySelector('#depth').value = '1'; document.querySelector('#depth').dispatchEvent(new Event('change'))")
                self.assertTrue(any(edge["source"] == "30" and edge["target"] == "03" and edge["line"] == "solid" for edge in check_routes()["edges"]))
                capture("prompt-stress-testing")
                evaluate("document.querySelector('#focus-task').value = '01'; document.querySelector('#focus-task').dispatchEvent(new Event('change'))")
                wait_for("document.querySelector('#details h2').textContent.startsWith('01 ·')")
                self.assertEqual(evaluate("document.querySelector('#details .task-status').textContent"), "COMPLETE")

                evaluate("document.querySelector('#focus-task').value = '18'; document.querySelector('#focus-task').dispatchEvent(new Event('change'))")
                wait_for("document.querySelector('#details h2').textContent.startsWith('18 ·')")
                self.assertEqual(evaluate("document.querySelector('#details .task-status').textContent"), "COMPLETE")
                setup_details = evaluate("document.querySelector('#details').innerText")
                self.assertIn("local VM tests cover all three candidate families", setup_details)
                self.assertIn("published and verified private", setup_details)
                self.assertIn("candidate execution and quality review are tracked in 29", setup_details)
                self.assertIn("model selection is tracked in 06", setup_details)
                self.assertNotIn("900000053", setup_details)
                self.assertNotIn("Qwen's baseline", setup_details)

                evaluate("document.querySelector('#focus-task').value = '29'; document.querySelector('#focus-task').dispatchEvent(new Event('change'))")
                wait_for("document.querySelector('#details h2').textContent.startsWith('29 ·')")
                self.assertEqual(evaluate("document.querySelector('#details .task-status').textContent"), "IN PROGRESS")
                pilot_details = evaluate("document.querySelector('#details').innerText")
                self.assertIn("All three candidates have saved training runs, matching reload checks and trained evaluations", pilot_details)
                self.assertIn("recovered Gemma baseline subjects still need mask generation", pilot_details)
                self.assertIn("candidate comparison and semantic review remain unfinished", pilot_details)
                self.assertIn("no prominence", pilot_details)
                self.assertIn("larger pilot (06), not final model selection", pilot_details)

                # The graph must be derived from the served task data, not draw.io.
                data_file = public / "release-plan.json"
                data = json.loads(data_file.read_text())
                next(task for task in data["tasks"] if task["id"] == "02")["title"] = "Review refreshed 100-note hierarchy"
                data_file.write_text(json.dumps(data))
                call("browsingContext.reload", {"context": context, "wait": "complete"})
                wait_for("document.querySelector('#details')?.innerText.includes('Review refreshed 100-note hierarchy')")
                # Track membership comes from the refreshed plan, not an ID list in the viewer.
                changed = next(task for task in data["tasks"] if task["id"] == "29")
                changed["track"] = "shared"
                data_file.write_text(json.dumps(data))
                call("browsingContext.reload", {"context": context, "wait": "complete"})
                wait_for("document.querySelector('#focus-task')?.options.length > 0")
                self.assertIn("29", picker_ids())
                changed["track"] = "model"

                invalid = data["tasks"][0]
                saved_track = invalid["track"]
                invalid["track"] = "unknown"
                data_file.write_text(json.dumps(data))
                call("browsingContext.reload", {"context": context, "wait": "complete"})
                wait_for("document.querySelector('#graph-status')?.textContent.includes('Invalid task track')")
                del invalid["track"]
                data_file.write_text(json.dumps(data))
                call("browsingContext.reload", {"context": context, "wait": "complete"})
                wait_for("document.querySelector('#graph-status')?.textContent.includes('Invalid task track')")
                invalid["track"] = saved_track
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
