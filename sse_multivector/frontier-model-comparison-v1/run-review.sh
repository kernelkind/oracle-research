#!/usr/bin/env bash
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd -- "$here/../.." && pwd)"
binary="$root/target/release/note-sample-review"
if [[ ! -x "$binary" ]]; then
  printf 'Build first:\ncd %q\nnix develop -c cargo build --release --jobs 2 --bin note-sample-review\n' "$root" >&2
  exit 1
fi
exec "$binary" "$here/selection.json" "$@"
