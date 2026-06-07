#!/usr/bin/env bash
# install-vendor-markdown.sh — fetch + verify the pinned marked + DOMPurify JS
# into assets/vendor/.
#
# The product-spec body-bearing HTML outputs (read-once export, --viz board,
# --viz explorer) render artifact markdown bodies client-side via the
# chokepoint  el.innerHTML = DOMPurify.sanitize(marked.parse(md))  with NO
# network at view time. This script downloads the two pinned libraries once;
# subsequent runs skip if already vendored (and matching sha256, when set).
#
# Mirrors install-vendor-mermaid.sh. The two libraries are COMMITTED to the
# repo (.gitignore un-ignores product-spec/**) so a fresh clone is offline-ready
# and release ships them deterministically.
#
# NOTE: the `</script>` close-tag escape needed for safe inlining is applied at
# INLINE time in render_html._load_vendored_markdown_libs(), NOT here — so the
# vendored files stay byte-identical to the CDN originals and the sha256 pin +
# idempotent-skip both keep working.
#
# Usage:
#   ./install-vendor-markdown.sh             # default: skill_dir = ../, log to /tmp
#   ./install-vendor-markdown.sh <skill_dir> <log_file>
set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SKILL_DIR="${1:-$(cd "$SCRIPT_DIR/.." && pwd)}"
LOG_FILE="${2:-/tmp/product-spec-vendor-markdown.log}"

VENDOR_DIR="$SKILL_DIR/assets/vendor"
mkdir -p "$VENDOR_DIR"

# Pinned releases. sha256 of each file as fetched 2026-05-29; locking the hash
# rejects a tampered CDN payload. Bump the hash together with the version.
# Format: "<target-filename>|<url>|<sha256>"
MARKED_URL="https://cdn.jsdelivr.net/npm/marked@18.0.4/lib/marked.umd.js"
PURIFY_URL="https://cdn.jsdelivr.net/npm/dompurify@3.4.7/dist/purify.min.js"
MARKED_SHA256="5d35f05a51554f8665066455535e3adf642df0da7e2a18d39766d5a3ecb4846c"
PURIFY_SHA256="f84e522876a6cfadecb89c173356409acec39f580c69018559c9a50e96299b0c"

LIBS=(
    "marked.min.js|$MARKED_URL|$MARKED_SHA256"
    "purify.min.js|$PURIFY_URL|$PURIFY_SHA256"
)

fetch_one() {
    local target="$1" url="$2" expected="$3"
    # Idempotent: skip if already vendored (and matching sha256 when set).
    if [ -s "$target" ]; then
        if [ -z "$expected" ]; then
            echo "product-spec vendor: $(basename "$target") already present ($(wc -c < "$target") bytes)"
            return 0
        fi
        have=$(sha256sum "$target" | awk '{print $1}')
        if [ "$have" = "$expected" ]; then
            echo "product-spec vendor: $(basename "$target") already present (sha256 OK)"
            return 0
        fi
        echo "product-spec vendor: $(basename "$target") sha256 mismatch, re-downloading" >&2
    fi

    echo "product-spec vendor: fetching $url" >&2
    if command -v curl >/dev/null 2>&1; then
        curl -fsSL "$url" -o "$target" 2>>"$LOG_FILE"
    elif command -v wget >/dev/null 2>&1; then
        wget -q "$url" -O "$target" 2>>"$LOG_FILE"
    else
        echo "product-spec vendor: neither curl nor wget available" >&2
        return 1
    fi

    if [ ! -s "$target" ]; then
        echo "product-spec vendor: download was empty" >&2
        rm -f "$target"
        return 1
    fi
    if [ -n "$expected" ]; then
        got=$(sha256sum "$target" | awk '{print $1}')
        if [ "$got" != "$expected" ]; then
            echo "product-spec vendor: $(basename "$target") sha256 mismatch (expected $expected, got $got)" >&2
            rm -f "$target"
            return 1
        fi
    fi
    echo "product-spec vendor: $(basename "$target") vendored ($(wc -c < "$target") bytes)"
}

for entry in "${LIBS[@]}"; do
    IFS='|' read -r name url sha <<< "$entry"
    fetch_one "$VENDOR_DIR/$name" "$url" "$sha"
done
