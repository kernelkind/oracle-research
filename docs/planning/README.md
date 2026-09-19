# Release-plan viewer

[Release decisions and open questions](release-decisions.md) records the planning
discussion, including corpus scope, validation, Vast.ai compute and rented hosting.

`october-18-release.drawio` is the editable source. `index.html` displays it
read-only using draw.io's renderer. Refresh the browser after saving changes;
no export or copied preview is needed. The page fetches the source and renderer
from its own host only.

## Local access

From this directory, serve the planning files locally:

```sh
python3 -m http.server 8000 --bind 127.0.0.1
```

Open `http://127.0.0.1:8000/` in a browser on the same machine.

## Bundled renderer

`vendor/viewer-static.min.js` is the unmodified draw.io v31.4.6 bundle from:

<https://raw.githubusercontent.com/jgraph/drawio/v31.4.6/src/main/webapp/js/viewer-static.min.js>

SHA-256: `e49a0d5d1eac05351c3d21a22d5278fcab5d20066bdbdf074edc0b9989c611cd`

The upstream license is retained in `vendor/LICENSE.drawio`. Bundling the
renderer avoids sending the planning document to an external viewer service.

`tests/test_planning_viewer.py` checks the actual page in isolated headless
Firefox: rendering, page switching, read-only controls, local resource loads,
refreshing changed source, and a visible error for missing source. It requires
Firefox and Python's `websocket-client` package.
