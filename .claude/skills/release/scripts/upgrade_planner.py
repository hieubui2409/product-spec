"""upgrade_planner — pure, deterministic upgrade plan builder.

Plans which legacy 1.x artifacts to remove, prompt, unlink, or skip.
NO disk writes during planning. The apply phase lives in upgrade_apply.py.

Public surface:
    load_legacy_map(path)  -> dict
    plan(target_root, legacy_map) -> list[PlanItem]
    main()  CLI: --target --legacy-map [--dry-run | --apply] [--json]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Action constants
# ---------------------------------------------------------------------------
NOOP = "noop"
REMOVE = "remove"            # absent pristine data → remove-with-backup
PROMPT = "prompt"            # content differs from pristine hash → ask PO
UNLINK_ONLY = "unlink_only"  # symlink: unlink the link, never follow


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------
@dataclass
class PlanItem:
    """One planned action for one legacy entry."""
    path: str           # repo-relative path (from legacy-map entry)
    kind: str           # "file" | "dir"
    action: str         # NOOP | REMOVE | PROMPT | UNLINK_ONLY
    reason: str
    superseded_by: Optional[str]
    modified: list      # relpaths inside a dir that differ from pristine
    is_symlink: bool
    pristine_verified: bool  # True only when action=REMOVE AND pristine hashes matched

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "kind": self.kind,
            "action": self.action,
            "reason": self.reason,
            "superseded_by": self.superseded_by,
            "modified": self.modified,
            "is_symlink": self.is_symlink,
            "pristine_verified": self.pristine_verified,
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _check_dir_against_pristine(live_dir: Path, pristine_map: dict) -> list[str]:
    """Compare every file in live_dir against pristine sha256 map.

    Returns list of relative paths that are new or whose content differs.
    Sorting is deterministic (lexicographic).
    """
    modified: list[str] = []
    for rel, expected_hash in sorted(pristine_map.items()):
        live_file = live_dir / rel
        if not live_file.exists():
            modified.append(rel)
            continue
        if _sha256_file(live_file) != expected_hash:
            modified.append(rel)
    # Files present in live_dir but NOT in pristine map also count as modified.
    for f in sorted(live_dir.rglob("*")):
        if f.is_file() and not f.is_symlink():
            rel = f.relative_to(live_dir).as_posix()
            if rel not in pristine_map and rel not in modified:
                modified.append(rel)
    return sorted(modified)


# ---------------------------------------------------------------------------
# Core planner
# ---------------------------------------------------------------------------
def load_legacy_map(path: Path) -> dict:
    """Load and return the legacy-map JSON. Raises ValueError on parse failure."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid legacy-map JSON at {path}: {e}") from e


def plan(target_root: Path, legacy_map: dict) -> list[PlanItem]:
    """Compute upgrade plan: no disk writes; deterministic entry order.

    Signature check: at least one legacy_signature_path must exist in target
    for entries that have requires_signature=True. This prevents removing
    a dev repo's own rule files whose basenames collide with legacy paths.
    """
    sig_paths = legacy_map.get("legacy_signature_paths", [])
    signature_present = any((target_root / p).exists() for p in sig_paths)

    items: list[PlanItem] = []
    for entry in legacy_map.get("entries", []):
        entry_path = entry["path"]
        kind = entry.get("kind", "file")
        action_hint = entry.get("action", "remove")
        superseded_by = entry.get("superseded_by")
        requires_sig = bool(entry.get("requires_signature", False))
        reason = entry.get("reason", "")
        pristine_sha = entry.get("pristine_sha256")

        live = target_root / entry_path

        # --- Signature gate ---
        if requires_sig and not signature_present:
            items.append(PlanItem(
                path=entry_path, kind=kind, action=NOOP,
                reason="skipped: no 1.x legacy signature in target",
                superseded_by=superseded_by,
                modified=[], is_symlink=False, pristine_verified=False,
            ))
            continue

        # --- Symlink check (before existence check — a symlink may point to missing) ---
        if live.is_symlink():
            items.append(PlanItem(
                path=entry_path, kind=kind, action=UNLINK_ONLY,
                reason="symlink: unlink only, never follow to external target",
                superseded_by=superseded_by,
                modified=[], is_symlink=True, pristine_verified=False,
            ))
            continue

        # --- Absent ---
        if not live.exists():
            items.append(PlanItem(
                path=entry_path, kind=kind, action=NOOP,
                reason="absent — nothing to sweep",
                superseded_by=superseded_by,
                modified=[], is_symlink=False, pristine_verified=False,
            ))
            continue

        # --- Pristine hash comparison ---
        if pristine_sha is not None:
            if kind == "file":
                live_hash = _sha256_file(live)
                if live_hash != pristine_sha:
                    items.append(PlanItem(
                        path=entry_path, kind=kind, action=PROMPT,
                        reason="content differs from pristine sha256 — PO may have edited; keep or change?",
                        superseded_by=superseded_by,
                        modified=[entry_path], is_symlink=False, pristine_verified=False,
                    ))
                    continue
                # Hash matches: safe pristine remove
                items.append(PlanItem(
                    path=entry_path, kind=kind, action=REMOVE,
                    reason=reason,
                    superseded_by=superseded_by,
                    modified=[], is_symlink=False, pristine_verified=True,
                ))
            else:
                # dir: pristine_sha is a relpath→sha256 mapping object
                if not isinstance(pristine_sha, dict):
                    raise ValueError(
                        f"pristine_sha256 for dir entry '{entry_path}' must be a relpath→sha256 object, "
                        f"got {type(pristine_sha).__name__}"
                    )
                modified = _check_dir_against_pristine(live, pristine_sha)
                if modified:
                    items.append(PlanItem(
                        path=entry_path, kind=kind, action=PROMPT,
                        reason="dir content differs from pristine — modified files listed",
                        superseded_by=superseded_by,
                        modified=modified, is_symlink=False, pristine_verified=False,
                    ))
                else:
                    items.append(PlanItem(
                        path=entry_path, kind=kind, action=REMOVE,
                        reason=reason,
                        superseded_by=superseded_by,
                        modified=[], is_symlink=False, pristine_verified=True,
                    ))
        else:
            # No pristine data — remove without hash verification
            items.append(PlanItem(
                path=entry_path, kind=kind, action=REMOVE,
                reason=reason,
                superseded_by=superseded_by,
                modified=[], is_symlink=False, pristine_verified=False,
            ))

    return items


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _print_plan_human(items: list[PlanItem]) -> None:
    print("Upgrade plan:")
    for item in items:
        tag = f"[{item.action.upper()}]"
        sup = f" -> {item.superseded_by}" if item.superseded_by else ""
        print(f"  {tag} {item.path}{sup}")
        print(f"        reason: {item.reason}")
        if item.modified:
            print(f"        modified: {item.modified}")
    print(f"\n  Total: {len(items)} entries")
    removals = sum(1 for i in items if i.action == REMOVE)
    prompts = sum(1 for i in items if i.action == PROMPT)
    print(f"  Remove: {removals}  Prompt: {prompts}  "
          f"Unlink: {sum(1 for i in items if i.action == UNLINK_ONLY)}  "
          f"Skip/noop: {sum(1 for i in items if i.action == NOOP)}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Plan (and optionally apply) the 1.x -> 2.x legacy sweep."
    )
    parser.add_argument("--target", required=True, help="Target repo root directory")
    parser.add_argument("--legacy-map", required=True, help="Path to legacy-map.json")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true",
                      help="Print plan, write nothing (this is the default when neither flag is given)")
    mode.add_argument("--apply", action="store_true",
                      help="Execute the plan (backs up + removes legacy artifacts)")
    parser.add_argument("--json", action="store_true", dest="json_out",
                        help="Emit machine-readable JSON")
    args = parser.parse_args()

    try:
        legacy_map = load_legacy_map(Path(args.legacy_map))
    except (ValueError, OSError) as e:
        print(f"[upgrade] ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    target = Path(args.target).resolve()
    items = plan(target, legacy_map)

    if args.json_out:
        print(json.dumps([i.to_dict() for i in items], indent=2))
    else:
        _print_plan_human(items)

    if args.apply:
        import upgrade_apply  # type: ignore[import-not-found]
        from datetime import datetime, timezone
        now_ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")
        backup_root = target
        result = upgrade_apply.apply(items, target, backup_root, now_ts=now_ts)
        print("\nApply result:")
        print(json.dumps(result, indent=2))
    else:
        print("\nDry-run complete — no files changed. Re-run with --apply to execute.")


if __name__ == "__main__":
    main()
