#!/usr/bin/env bash
# install_vendor.sh — fetch + verify the pinned Mermaid JS into assets/vendor/.
#
# The product-spec HTML visualization renderer needs an inline Mermaid runtime
# to render without network. This script downloads the pinned version once;
# subsequent runs skip if already vendored (and matching sha256, when set).
#
# Designed to be portable: run standalone OR invoked from `.claude/skills/install.sh`.
# Exits 0 on success or when already vendored; non-zero only on a true fetch failure.
#
# Usage:
#   ./install_vendor.sh             # default: skill_dir = ../, log to /tmp
#   ./install_vendor.sh <skill_dir> <log_file>
set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SKILL_DIR="${1:-$(cd "$SCRIPT_DIR/.." && pwd)}"
LOG_FILE="${2:-/tmp/product-spec-vendor.log}"

VENDOR_DIR="$SKILL_DIR/assets/vendor"
TARGET="$VENDOR_DIR/mermaid.min.js"
PINNED_URL="https://cdn.jsdelivr.net/npm/mermaid@11.4.1/dist/mermaid.min.js"
# Sha256 of mermaid@11.4.1 dist/mermaid.min.js as fetched 2026-05-28.
# Locking this rejects a tampered CDN payload. Bump together with PINNED_URL.
EXPECTED_SHA256="a43bc1afd446f9c4cc66ac5dd45d02e8d65e26fc5344ec0ef787f88d6ddb6f9e"

mkdir -p "$VENDOR_DIR"

# Idempotent: skip if already vendored (and matching sha256 when set).
if [ -s "$TARGET" ]; then
    if [ -z "$EXPECTED_SHA256" ]; then
        echo "product-spec vendor: $TARGET already present ($(wc -c < "$TARGET") bytes)"
        exit 0
    fi
    have=$(sha256sum "$TARGET" | awk '{print $1}')
    if [ "$have" = "$EXPECTED_SHA256" ]; then
        echo "product-spec vendor: $TARGET already present (sha256 OK)"
        exit 0
    fi
    echo "product-spec vendor: sha256 mismatch, re-downloading" >&2
fi

echo "product-spec vendor: fetching $PINNED_URL" >&2
if command -v curl >/dev/null 2>&1; then
    curl -fsSL "$PINNED_URL" -o "$TARGET" 2>>"$LOG_FILE"
elif command -v wget >/dev/null 2>&1; then
    wget -q "$PINNED_URL" -O "$TARGET" 2>>"$LOG_FILE"
else
    echo "product-spec vendor: neither curl nor wget available" >&2
    exit 1
fi

if [ ! -s "$TARGET" ]; then
    echo "product-spec vendor: download was empty" >&2
    rm -f "$TARGET"
    exit 1
fi

if [ -n "$EXPECTED_SHA256" ]; then
    got=$(sha256sum "$TARGET" | awk '{print $1}')
    if [ "$got" != "$EXPECTED_SHA256" ]; then
        echo "product-spec vendor: sha256 mismatch (expected $EXPECTED_SHA256, got $got)" >&2
        rm -f "$TARGET"
        exit 1
    fi
fi

echo "product-spec vendor: $TARGET vendored ($(wc -c < "$TARGET") bytes)"
