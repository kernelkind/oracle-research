"""Browser integration check for the actual planning page and bundled renderer.

Requires Firefox (FIREFOX or PATH) and the Python websocket-client package.
Uses an isolated profile and a loopback-only server; never edits the real plan.
"""

import base64
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
import xml.etree.ElementTree as ET

import websocket


class PlanningViewerTest(unittest.TestCase):
    def test_publication_preparation_belongs_to_existing_tasks(self):
        diagram = Path(__file__).resolve().parents[1] / "docs/planning/october-18-release.drawio"
        root = ET.parse(diagram)
        labels = {cell.get("id"): cell.get("value", "")
                  for cell in root.findall("./diagram/mxGraphModel/root/mxCell")}
        self.assertIn("weight-release permission before selection", labels["m2"])
        self.assertNotIn("weight-release terms", labels["m4"])
        for term in ("supporting files", "usage instructions", "evaluation results",
                     "Verify loading", "mask/prominence generation"):
            with self.subTest(model_release=term):
                self.assertIn(term, labels["m4"])
        for term in ("runnable code", "instructions", "architecture", "continual-update path"):
            with self.subTest(hierarchy_release=term):
                self.assertIn(term, labels["s4"])
                self.assertIn(term, labels["week4"])
        for term in ("distilled model (08)", "continual-update path (12)"):
            self.assertIn(term, labels["d4"])
        self.assertIn("evaluation results", labels["week3"])
        self.assertIn("distilled model (08)", labels["week5"])
        self.assertIn("prepared", labels["week-launch"])

    def test_saved_titles_make_hierarchy_ready_to_resume(self):
        diagram = Path(__file__).resolve().parents[1] / "docs/planning/october-18-release.drawio"
        root = ET.parse(diagram).find("./diagram[@id='dependencies']/mxGraphModel/root")
        cells = {cell.get("id"): cell for cell in root.findall("mxCell")}
        self.assertIn("COMPLETE", cells["h1"].get("value"))
        self.assertIn("Subject and mask prompts finished", cells["h1"].get("value"))
        self.assertNotIn("IN PROGRESS", cells["h1"].get("value"))
        completed_style = (
            "fillColor=light-dark(#fbfbfc, #232a33)",
            "strokeColor=light-dark(#d9dde2, #566575)",
            "fontColor=light-dark(#697583, #c2cbd5)",
        )
        for key in ("h1", "h-title"):
            for part in completed_style:
                self.assertIn(part, cells[key].get("style"))
        self.assertIn("h-title", cells)
        self.assertIn("23 · Fix and validate node-title prompt", cells["h-title"].get("value"))
        self.assertIn("COMPLETE", cells["h-title"].get("value"))
        self.assertIn("129", cells["h-title"].get("value"))
        self.assertIn("v38", cells["h-title"].get("value"))
        self.assertNotIn("23 ·", cells["ready-summary"].get("value"))
        edge = cells["e-title-h2"]
        self.assertEqual((edge.get("source"), edge.get("target")), ("h-title", "h2"))
        self.assertNotIn("dashed=1", edge.get("style"))
        self.assertIn("READY TO RESUME", cells["h2"].get("value"))
        self.assertIn("saved v38 titles", cells["h2"].get("value"))
        self.assertIn("Connect saved v38 titles to TRUE inputs", cells["h2"].get("value"))
        self.assertIn("correctness at minimal scope", cells["h2"].get("value"))
        self.assertIn("finish requires 25", cells["h2"].get("value"))
        self.assertIn("fillColor=light-dark(#e6f4ea,", cells["h2"].get("style"))
        self.assertIn("02 ·", cells["ready-summary"].get("value"))
        self.assertNotIn("IN PROGRESS", cells["h2"].get("value"))
        self.assertNotIn("WAITING FOR 01", cells["h2"].get("value"))
        self.assertIn("WAITING FOR 04 + 17", cells["m1"].get("value"))
        self.assertNotIn("WAITING FOR 01", cells["m1"].get("value"))
        self.assertIn("PAUSED", cells["m0"].get("value"))
        self.assertIn("Mask prompt finished; prominence remains paused", cells["m0"].get("value"))
        self.assertIn("fillColor=light-dark(#f7f8fa,", cells["m0"].get("style"))
        self.assertNotIn("IN PROGRESS", cells["m0"].get("value"))
        self.assertNotIn("READY TO START", cells["m0"].get("value"))
        self.assertNotIn("04 ·", cells["ready-summary"].get("value"))

    def test_weekly_delivery_track_is_parallel_without_new_dates(self):
        diagram = Path(__file__).resolve().parents[1] / "docs/planning/october-18-release.drawio"
        root = ET.parse(diagram).find("./diagram[@id='weekly-targets']/mxGraphModel/root")
        cells = {cell.get("id"): cell for cell in root.findall("mxCell")}
        self.assertIn("week-delivery", cells)
        self.assertIn("Parallel track", cells["week-delivery-heading"].get("value"))
        self.assertIn("not week assignments", cells["week-delivery-note"].get("value"))
        self.assertIn("dates remain open", cells["week-delivery-note"].get("value"))
        self.assertIn("100-note snapshot (02)", cells["week-service-client"].get("value"))
        self.assertIn("Service development can start after protocol (13)",
                      cells["week-service-client"].get("value"))
        self.assertIn("Notedeck can start with 13", cells["week-service-client"].get("value"))
        self.assertIn("integration needs 14", cells["week-service-client"].get("value"))
        self.assertIn("final snapshot (12)", cells["week-launch"].get("value"))
        self.assertIn("October 18", cells["week-launch"].get("value"))
        self.assertNotIn("prepare service", cells["week4"].get("value"))
        self.assertIn("04 · Mask prominence remains paused; mask prompt is finished", cells["week-subtitle"].get("value"))
        self.assertIn("Revisit during the 100-note build", cells["week-subtitle"].get("value"))
        self.assertIn("Subject and mask prompts finished", cells["week1"].get("value"))
        self.assertIn("v38 titles saved for all 129 groups", cells["week1"].get("value"))
        self.assertIn("check correctness at minimal scope", cells["week1"].get("value"))
        self.assertIn("25 must finish before 02 can finish", cells["week1"].get("value"))
        self.assertIn("23 · Node-title prompt complete", cells["week1"].get("value"))
        self.assertIn("Map: 01–02, 23, 25", cells["week1"].get("value"))
        for stage in ("200: correctness + prominence ordering",
                      "300: correctness + scalable construction",
                      "500: combined validation + build profiling"):
            self.assertIn(stage, cells["week2"].get("value"))
        lane = cells["week-delivery"].find("mxGeometry")
        self.assertGreaterEqual(float(lane.get("width")), 1600)
        week = cells["week1"].find("mxGeometry")
        self.assertGreater(float(lane.get("y")), float(week.get("y")) + float(week.get("height")))

    def test_missing_pipeline_work_has_completion_dependencies(self):
        diagram = Path(__file__).resolve().parents[1] / "docs/planning/october-18-release.drawio"
        root = ET.parse(diagram).find("./diagram[@id='dependencies']/mxGraphModel/root")
        cells = {cell.get("id"): cell for cell in root.findall("mxCell")}
        edges = {(cell.get("source"), cell.get("target")): cell
                 for cell in cells.values() if cell.get("edge") == "1"}
        for key, number in [("h-recovery", "24"), ("h-relations", "25")]:
            with self.subTest(task=number):
                self.assertIn(key, cells)
                self.assertIn(number + " ·", cells[key].get("value"))
                self.assertIn("READY TO START", cells[key].get("value"))
                self.assertIn("fillColor=light-dark(#e6f4ea,", cells[key].get("style"))
                self.assertIn(number + " ·", cells["ready-summary"].get("value"))
                self.assertIn((key, "h3"), edges)
                self.assertNotIn("dashed=1", edges[key, "h3"].get("style"))
        self.assertNotIn(("h-recovery", "h2"), edges,
                         "Membership expansion is outside the initial diagnostic")
        self.assertIn(("h-relations", "h2"), edges)
        self.assertNotIn("dashed=1", edges["h-relations", "h2"].get("style"))
        collapse = cells["h-collapse"]
        self.assertIn("VALIDATION PENDING", collapse.get("value"))
        self.assertIn("Implemented and regression-tested", collapse.get("value"))
        self.assertIn("fillColor=light-dark(#f7f8fa,", collapse.get("style"))
        self.assertNotIn("26 ·", cells["ready-summary"].get("value"))
        self.assertIn(("h-collapse", "h3"), edges)
        self.assertIn("Title pass complete September 24", cells["subtitle"].get("value"))
        for pair in [("m0", "m-order"), ("m-order", "h3"),
                     ("h3", "s-build"), ("s-hdbscan", "s-build"),
                     ("s-stage-costs", "s-build"), ("s-build", "s2")]:
            self.assertIn(pair, edges)
            self.assertNotIn("dashed=1", edges[pair].get("style"))
        self.assertIn("NEEDS 04", cells["m-order"].get("value"))
        self.assertIn("NEEDS 03 + 21 + 22", cells["s-build"].get("value"))
        self.assertIn("strategies tested in 03", cells["s-build"].get("value"))
        for key in ("m-order", "s-build"):
            self.assertIn("fillColor=light-dark(#f7f8fa,", cells[key].get("style"))
            self.assertNotIn("READY TO START", cells[key].get("value"))
        self.assertIn("FINISH WITH 24–27", cells["h3"].get("value"))
        for stage in ("200: prominence + correctness",
                      "300: scalable construction + correctness",
                      "500: combine both; profile build"):
            self.assertIn(stage, cells["h3"].get("value"))
        self.assertIn("pair filtering keeps useful links", cells["h3"].get("value"))
        self.assertIn("08 + 09 + 20 + 28", cells["s2"].get("value"))
        self.assertIn("dashed=1", edges["h-recovery", "s-analysis"].get("style"))
        self.assertIn("membership recovery", cells["s-analysis"].get("value"))
        self.assertIn("title input growth", cells["s-stage-costs"].get("value"))
        self.assertIn("small hierarchy from pilot outputs before model selection", cells["m2"].get("value"))
        self.assertNotIn(("s-build", "s-analysis"), edges, "Early estimates must not wait for the finished implementation")
        pending = {key: set() for key in cells}
        for (source, target), edge in edges.items():
            if "dashed=1" not in edge.get("style"):
                pending[target].add(source)
        while pending:
            ready = {key for key, deps in pending.items() if not deps}
            self.assertTrue(ready, "Completion dependencies must not contain a cycle")
            pending = {key: deps - ready for key, deps in pending.items() if key not in ready}
        weekly = ET.parse(diagram).find("./diagram[@id='weekly-targets']/mxGraphModel/root")
        labels = {cell.get("id"): cell.get("value", "") for cell in weekly.findall("mxCell")}
        for number in ("24", "25", "26", "27", "28"):
            self.assertIn(number, labels["week-pipeline"])
        self.assertIn("not new week assignments", labels["week-pipeline-heading"])

    def test_training_data_comparison_is_active_without_separate_preparation(self):
        diagram = Path(__file__).resolve().parents[1] / "docs/planning/october-18-release.drawio"
        document = ET.parse(diagram)
        root = document.find("./diagram[@id='dependencies']/mxGraphModel/root")
        cells = {cell.get("id"): cell for cell in root.findall("mxCell")}
        self.assertFalse("m-annotator-prep" in cells, "Remove the separate task 19")
        comparison = cells["m-annotator"]
        self.assertIn("IN PROGRESS", comparison.get("value"))
        self.assertIn("fillColor=light-dark(#e7f1ff,", comparison.get("style"))
        self.assertIn("Muse high vs Astra low; no teacher selected", comparison.get("value"))
        self.assertIn("FINISH WITH 04", comparison.get("value"))
        self.assertNotIn("17 ·", cells["ready-summary"].get("value"))
        incoming = set()
        for cell in cells.values():
            if cell.get("edge") == "1":
                self.assertIn(cell.get("source"), cells)
                self.assertIn(cell.get("target"), cells)
                if cell.get("target") == "m-annotator":
                    incoming.add(cell.get("source"))
        self.assertEqual(incoming, {"h1", "m0"})
        outgoing = {(cell.get("source"), cell.get("target")): cell
                    for cell in cells.values() if cell.get("edge") == "1"}
        self.assertIn(("m-annotator", "m1"), outgoing,
                      "The selected teachers must write 05's labels")
        self.assertNotIn("dashed=1", outgoing[("m-annotator", "m1")].get("style"))
        self.assertIn("teachers", cells["m1"].get("value"))
        for cell in document.findall(".//mxCell"):
            self.assertNotIn("19 ·", cell.get("value", ""))

    def test_ready_preparation_is_separate_from_blocked_work(self):
        diagram = Path(__file__).resolve().parents[1] / "docs/planning/october-18-release.drawio"
        root = ET.parse(diagram).find("./diagram[@id='dependencies']/mxGraphModel/root")
        cells = {cell.get("id"): cell for cell in root.findall("mxCell")}
        edges = {(cell.get("source"), cell.get("target"))
                 for cell in cells.values() if cell.get("edge") == "1"}
        for ready, blocked in [("m-setup", "m2"),
                               ("s-hdbscan", "s-analysis"), ("s-stage-costs", "s-analysis")]:
            with self.subTest(ready=ready):
                self.assertIn(ready, cells, "Executable preparation needs its own node")
                self.assertIn("fillColor=light-dark(#e6f4ea,", cells[ready].get("style"))
                self.assertIn("READY TO START", cells[ready].get("value"))
                self.assertIn("fillColor=light-dark(#f7f8fa,", cells[blocked].get("style"))
                self.assertIn((ready, blocked), edges)
        self.assertIn(("m1", "m2"), edges)
        self.assertIn(("m-setup", "m2"), edges)
        self.assertNotIn("STARTING SCOPE UNRESOLVED", cells["m-setup"].get("value"))
        self.assertIn("18 · Prepare training code for the fine-tuning pilot", cells["ready-summary"].get("value"))
        self.assertIn("save/reload", cells["m-setup"].get("value"))
        self.assertIn("outputs for evaluation", cells["m-setup"].get("value"))
        self.assertIn("Format examples and evaluate", cells["m2"].get("value"))
        self.assertIn(("s1", "s2"), edges)
        self.assertIn(("m2", "s-analysis"), edges)
        self.assertIn(("m-annotator", "m3"), edges)
        for cell in cells.values():
            self.assertNotIn("#fff4ce", cell.get("style", ""))
            self.assertNotIn("amber", cell.get("value", "").lower())

    def test_scale_measurements_inform_corpus_selection_before_final_validation(self):
        diagram = Path(__file__).resolve().parents[1] / "docs/planning/october-18-release.drawio"
        root = ET.parse(diagram).find("./diagram[@id='dependencies']/mxGraphModel/root")
        cells = {cell.get("id"): cell for cell in root.findall("mxCell")}
        edges = {(cell.get("source"), cell.get("target")): cell
                 for cell in cells.values() if cell.get("edge") == "1"}
        self.assertIn("fillColor=light-dark(#f7f8fa,", cells["s-analysis"].get("style"))
        self.assertIn("NEEDS 21 + 22", cells["s-analysis"].get("value"))
        self.assertNotIn("20 ·", cells["ready-summary"].get("value"))
        self.assertIn("21 · Assess HDBSCAN at launch scale", cells["ready-summary"].get("value"))
        self.assertIn("22 · Measure SSE, node-title and TRUE processing costs", cells["ready-summary"].get("value"))
        self.assertIn("existing masks and nodes", cells["s-stage-costs"].get("value"))
        for pair in [("s-analysis", "s1"), ("s-analysis", "s2"), ("s1", "s2"),
                     ("m4", "s2"), ("s-hdbscan", "s-analysis"), ("s-stage-costs", "s-analysis")]:
            self.assertIn(pair, edges)
            self.assertNotIn("dashed=1", edges[pair].get("style"))
        self.assertIn("dashed=1", edges[("m2", "s-analysis")].get("style"))
        self.assertIn("dashed=1", edges[("h3", "s-analysis")].get("style"))
        self.assertFalse(any(target == "s-stage-costs" for source, target in edges),
                         "Stage measurements can start from existing artifacts")
        self.assertIn("cosine", cells["h-note"].get("value").lower())

    def test_plan_exposes_dependencies_without_prescribing_unsettled_order(self):
        diagram = Path(__file__).resolve().parents[1] / "docs/planning/october-18-release.drawio"
        root = ET.parse(diagram).find("./diagram[@id='dependencies']/mxGraphModel/root")
        cells = {cell.get("id"): cell for cell in root.findall("mxCell")}
        edges = {(cell.get("source"), cell.get("target")): cell
                 for cell in cells.values() if cell.get("edge") == "1"}
        for pair in [("h1", "m-annotator"), ("m0", "m-annotator"),
                     ("s2", "s4"), ("s3", "s4")]:
            self.assertIn(pair, edges)
            self.assertNotIn("dashed=1", edges[pair].get("style"))
        self.assertIn("dashed=1", edges[("m2", "m3")].get("style"))
        self.assertIn("VOLUME DECISION", cells["m3"].get("value"))
        self.assertNotIn(("s2", "s3"), edges)
        self.assertNotIn(("s3", "s2"), edges)
        for node in ("s2", "s3"):
            self.assertNotIn("RELATIONSHIP OPEN", cells[node].get("value"))
        self.assertIn("Check full-build time and cost", cells["s2"].get("value"))
        self.assertIn("Test hierarchy with the distilled model", cells["s3"].get("value"))
        self.assertIn("Training labels:", cells["h-note"].get("value"))
        self.assertIn("Distilled model:", cells["h-note"].get("value"))
        self.assertIn("does not authorize execution", cells["legend"].get("value"))
        self.assertIn("Overall plan not approved", cells["subtitle"].get("value"))

    def test_labels_identify_model_roles_without_tracing_dependencies(self):
        diagram = Path(__file__).resolve().parents[1] / "docs/planning/october-18-release.drawio"
        root = ET.parse(diagram)
        labels = {cell.get("id"): cell.get("value", "")
                  for cell in root.findall("./diagram/mxGraphModel/root/mxCell")}
        for term in ("distilled model", "masks", "prominence", "hierarchy", "budget"):
            with self.subTest(term=term):
                self.assertIn(term, labels["s2"])
        self.assertIn("Compare teachers", labels["m-annotator"])
        self.assertIn("Choose the model to train", labels["m2"])
        self.assertNotIn("SP + MP", labels["h1"])
        for term in ("distilled model", "masks", "prominence", "hierarchy"):
            with self.subTest(weekly_term=term):
                self.assertIn(term, labels["week4"])

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

                def capture_page(name):
                    if directory := os.environ.get("PLANNING_SCREENSHOT_DIR"):
                        destination = Path(directory)
                        destination.mkdir(parents=True, exist_ok=True)
                        screenshot = call("browsingContext.captureScreenshot", {"context": context})
                        (destination / f"{name}.png").write_bytes(base64.b64decode(screenshot["data"]))

                def assert_readable_size():
                    # Measure the rendered SVG, not just its configuration.
                    self.assertGreaterEqual(evaluate("""(() => {
                        const label = document.querySelector('svg foreignObject');
                        return label.getScreenCTM().a;
                    })()"""), 1, "Opening a page must not shrink its text to fit the whole map")
                    self.assertTrue(evaluate("""(() => {
                        const main = document.querySelector('main');
                        return main.scrollWidth > main.clientWidth &&
                            main.scrollHeight > main.clientHeight &&
                            getComputedStyle(main).overflow === 'auto';
                    })()"""), "The readable-size map must scroll in both directions")

                def assert_dark_mode():
                    self.assertEqual(evaluate("getComputedStyle(document.documentElement).colorScheme"), "dark")
                    self.assertTrue(evaluate("""(() => {
                        const dark = color => {
                            const rgb = color.match(/[\\d.]+/g)?.slice(0, 3).map(Number);
                            return rgb?.length === 3 && Math.max(...rgb) < 100;
                        };
                        return ['body', 'header', '#refresh', '#diagram', '.diagram-toolbar']
                            .every(selector => dark(getComputedStyle(document.querySelector(selector)).backgroundColor));
                    })()"""), "Page, diagram and controls must have dark backgrounds")
                    self.assertEqual(evaluate("getComputedStyle(document.querySelector('#diagram')).colorScheme"), "dark")
                    self.assertTrue(evaluate("""(() => {
                        const labels = [...document.querySelectorAll('svg foreignObject')];
                        return labels.length > 10 && labels.every(label => {
                            const text = label.querySelector('div > div > div');
                            const rgb = getComputedStyle(text).color.match(/[\\d.]+/g).slice(0, 3).map(Number);
                            return Math.max(...rgb) > 150;
                        });
                    })()"""), "Diagram text must adapt to dark mode, not remain dark on dark")

                def assert_palette_contrast():
                    measured = json.loads(evaluate("""JSON.stringify((() => {
                        const rgb = color => color.match(/[\\d.]+/g).slice(0, 3).map(Number);
                        const luminance = color => rgb(color).map(c => c / 255)
                            .map(c => c <= .04045 ? c / 12.92 : ((c + .055) / 1.055) ** 2.4)
                            .reduce((sum, c, i) => sum + c * [.2126, .7152, .0722][i], 0);
                        const contrast = (a, b) => {
                            a = luminance(a); b = luminance(b);
                            return (Math.max(a, b) + .05) / (Math.min(a, b) + .05);
                        };
                        const card = document.querySelector('svg [fill*="#f7f8fa"]') ||
                            document.querySelector('svg [fill*="#f4f7fc"]');
                        const style = getComputedStyle(card);
                        const background = getComputedStyle(document.querySelector('#diagram')).backgroundColor;
                        const labels = [...document.querySelectorAll('svg foreignObject div > div > div')];
                        const label = labels.find(e => e.textContent.includes('02 · Build and review')) ||
                            labels.find(e => e.textContent.startsWith('Week 1'));
                        const text = getComputedStyle(label).color;
                        return {cardContrast: contrast(style.fill, background),
                            borderContrast: contrast(style.stroke, style.fill),
                            textContrast: contrast(text, style.fill),
                            textRGB: rgb(text)};
                    })())"""))
                    self.assertGreaterEqual(measured["cardContrast"], 1.4, "Cards must stand out from the canvas")
                    self.assertGreaterEqual(measured["borderContrast"], 3, "Card boundaries must remain visible")
                    self.assertGreaterEqual(measured["textContrast"], 7, "Task text needs strong contrast")
                    self.assertGreaterEqual(min(measured["textRGB"]), 220, "Task text, including waiting tasks, must be off-white")

                def assert_completed_cards_recede(scheme):
                    evaluate(f"document.querySelector('#diagram').style.colorScheme = '{scheme}'")
                    measured = json.loads(evaluate("""JSON.stringify((() => {
                        const rgb = color => color.match(/[\\d.]+/g).slice(0, 3).map(Number);
                        const luminance = color => rgb(color).map(c => c / 255)
                            .map(c => c <= .04045 ? c / 12.92 : ((c + .055) / 1.055) ** 2.4)
                            .reduce((sum, c, i) => sum + c * [.2126, .7152, .0722][i], 0);
                        const contrast = (a, b) => {
                            a = luminance(a); b = luminance(b);
                            return (Math.max(a, b) + .05) / (Math.min(a, b) + .05);
                        };
                        const completed = getComputedStyle(document.querySelector('svg [fill*="#fbfbfc"]'));
                        const waiting = getComputedStyle(document.querySelector('svg [fill*="#f7f8fa"]'));
                        const label = [...document.querySelectorAll('svg foreignObject div > div > div')]
                            .find(e => e.textContent.includes('01 · Fix subject and mask prompts'));
                        return {completedFill: luminance(completed.fill),
                            waitingFill: luminance(waiting.fill),
                            completedBorder: contrast(completed.stroke, completed.fill),
                            waitingBorder: contrast(waiting.stroke, waiting.fill),
                            completedText: contrast(getComputedStyle(label).color, completed.fill)};
                    })())"""))
                    if scheme == "dark":
                        self.assertLess(measured["completedFill"], measured["waitingFill"])
                    else:
                        self.assertGreater(measured["completedFill"], measured["waitingFill"])
                    self.assertLess(measured["completedBorder"], measured["waitingBorder"])
                    self.assertGreaterEqual(measured["completedText"], 4.5)

                def assert_clear_labels():
                    # Measure rendered text against card geometry and all edge captions.
                    problems = evaluate("""JSON.stringify((() => {
                        const config = JSON.parse(document.querySelector('#diagram').dataset.mxgraph);
                        const source = new DOMParser().parseFromString(config.xml, 'application/xml');
                        const labels = [...document.querySelectorAll('svg foreignObject')].map(fo => {
                            const element = fo.querySelector('div > div > div');
                            return {element, text: element.textContent, matrix: fo.getScreenCTM()};
                        });
                        const cards = [], captions = [], problems = [];
                        for (const cell of source.querySelectorAll('mxCell[value]')) {
                            const text = document.createElement('div');
                            text.innerHTML = cell.getAttribute('value');
                            const label = labels.find(item => item.text === text.textContent);
                            if (!label) continue;
                            if (cell.getAttribute('edge') === '1') { captions.push(label); continue; }
                            if (!cell.getAttribute('style').includes('rounded=1')) continue;
                            const g = cell.querySelector('mxGeometry');
                            const x = +g.getAttribute('x'), y = +g.getAttribute('y');
                            const start = new DOMPoint(x, y).matrixTransform(label.matrix);
                            const end = new DOMPoint(x + +g.getAttribute('width'),
                                y + +g.getAttribute('height')).matrixTransform(label.matrix);
                            const box = {left: start.x, top: start.y, right: end.x, bottom: end.y};
                            const actual = label.element.getBoundingClientRect();
                            if (actual.left < box.left + 4 || actual.right > box.right - 4 ||
                                actual.top < box.top + 4 || actual.bottom > box.bottom - 4) {
                                problems.push(cell.id + ': text lacks space inside its card; bottom gap=' +
                                    (box.bottom - actual.bottom).toFixed(1));
                            }
                            cards.push({id: cell.id, box});
                        }
                        const overlaps = (a, b) => a.left < b.right && a.right > b.left &&
                            a.top < b.bottom && a.bottom > b.top;
                        if (cards.length < 10) problems.push('Expected at least ten rendered cards');
                        return problems.concat(captions.flatMap(caption => cards.filter(card =>
                            overlaps(caption.element.getBoundingClientRect(), card.box))
                            .map(card => caption.text + ' overlaps ' + card.id)));
                    })())""")
                    self.assertEqual(json.loads(problems), [], "Diagram labels need clear space")

                call("browsingContext.navigate", {"context": context, "url": url, "wait": "complete"})
                wait_for_text("TRUE compares descriptions")
                wait_for_text("Ready to start or resume")
                wait_for_text("18 · Prepare training code for the fine-tuning pilot")
                wait_for_text("save/reload its trained weights")
                self.assertFalse(evaluate("document.body.innerText.includes('19 · Plan training-data generator comparison')"))
                wait_for_text("Subject and mask prompts finished")
                wait_for_text("READY TO RESUME")
                wait_for_text("saved v38 titles")
                wait_for_text("23 · Fix and validate node-title prompt")
                wait_for_text("Mask prompt finished; prominence remains paused")
                wait_for_text("24 · Recover missing node memberships")
                wait_for_text("25 · Handle node equivalence and TRUE cycles")
                wait_for_text("26 · Collapse equal-note navigation steps")
                wait_for_text("27 · Order node notes using mask prominence")
                wait_for_text("28 · Implement and validate the launch-scale build")
                wait_for_text("17 · Compare teachers")
                wait_for_text("06 · Choose the model to train")
                wait_for_text("05 · Prepare pilot training data")
                wait_for_text("Labels are written by the teachers")
                wait_for_text("weight-release permission before selection")
                wait_for_text("Verify loading and mask/prominence generation")
                wait_for_text("distilled model (08)")
                wait_for_text("20 · Assess full hierarchy-build resources")
                wait_for_text("22 · Measure SSE, node-title and TRUE processing costs")
                wait_for_text("21 · Assess HDBSCAN at launch scale")
                wait_for_text("10 · Check full-build time and cost")
                wait_for_text("the distilled model")
                wait_for_text("NEEDS 21 + 22")
                wait_for_text("Cosine cutoff selects node pairs")
                wait_for_text("Training labels:")
                wait_for_text("Distilled model:")
                wait_for_text("11 · Test hierarchy with the distilled model")
                self.assertFalse(evaluate("document.body.innerText.includes('RELATIONSHIP OPEN')"))
                wait_for_text("Overall plan not approved")
                assert_dark_mode()
                assert_palette_contrast()
                assert_completed_cards_recede("dark")
                assert_completed_cards_recede("light")
                capture_page("dependencies-light")
                evaluate("document.querySelector('#diagram').style.colorScheme = 'dark'")
                assert_readable_size()
                assert_clear_labels()
                capture_page("dependencies")
                self.assertGreater(evaluate("document.querySelectorAll('svg [fill=\"#e6f4ea\"]').length"), 0)
                self.assertEqual(evaluate("document.querySelectorAll('svg [fill=\"#fff4ce\"]').length"), 0)
                self.assertFalse(evaluate("document.body.innerText.includes('PREPARATION READY')"))
                self.assertGreater(evaluate("document.querySelectorAll('svg foreignObject, svg text').length"), 15)
                self.assertFalse(evaluate("!!document.querySelector('[contenteditable=true], textarea')"))
                evaluate("document.querySelector('main').scrollTo(600, 900)")
                self.assertTrue(evaluate("""(() => {
                    const button = document.querySelector('[title="Next Page"]').getBoundingClientRect();
                    const main = document.querySelector('main').getBoundingClientRect();
                    return button.left >= main.left && button.top >= main.top &&
                        button.right <= main.right && button.bottom <= main.bottom;
                })()"""), "Page controls must stay visible while scrolling")
                evaluate("document.querySelector('[title=\"Next Page\"]').click()")
                wait_for_text("Proposed weekly targets")
                wait_for_text("Distill the model")
                wait_for_text("Build launch hierarchy snapshot")
                wait_for_text("Prepare runnable code")
                wait_for_text("04 · Mask prominence remains paused; mask prompt is finished")
                wait_for_text("Additional completion dependencies—not new week assignments")
                wait_for_text("v38 titles saved for all 129 groups")
                wait_for_text("23 · Node-title prompt complete")
                wait_for_text("Parallel track · protocol, service and Notedeck")
                wait_for_text("Notedeck can start with 13")
                wait_for_text("22: measure SSE, node titles and TRUE")
                assert_dark_mode()
                assert_palette_contrast()
                assert_readable_size()
                assert_clear_labels()
                capture_page("weekly-targets")
                self.assertEqual(evaluate("document.querySelector('main').scrollTop"), 0)
                self.assertEqual(evaluate("document.querySelector('main').scrollLeft"), 0)
                evaluate("document.querySelector('[title=\"Zoom Out\"]').click()")
                self.assertLess(evaluate("document.querySelector('svg foreignObject').getScreenCTM().a"), 1)
                evaluate("document.querySelector('[title=\"Zoom In\"]').click()")
                assert_readable_size()
                evaluate("document.querySelector('[title=\"Zoom Out\"]').click()")
                evaluate("document.querySelector('[title=\"Reset zoom\"]').click()")
                assert_readable_size()
                # A laptop-size window must not trigger whole-map shrink-to-fit.
                call("browsingContext.setViewport", {
                    "context": context, "viewport": {"width": 1280, "height": 800},
                    "devicePixelRatio": 1,
                })
                evaluate("document.querySelector('[title=\"Previous Page\"]').click()")
                wait_for_text("TRUE compares descriptions")
                assert_readable_size()
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
