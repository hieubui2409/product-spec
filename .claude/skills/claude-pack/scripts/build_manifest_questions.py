"""build_manifest_questions — canonical question bank for the interactive manifest builder.

``list_questions(discovery, lang)`` returns the 4-batch JSON tree that the LLM
walks via AskUserQuestion. The questions are keyed by discovery output so only
options that exist on disk are offered, preventing E070-E073 validation errors at
write time.

Python never calls AskUserQuestion — this module only produces the question
payload; the LLM layer drives the conversation.
"""

from __future__ import annotations


def _option_list(values: list[str]) -> list[dict]:
    return [{"label": v, "value": v} for v in values]


def list_questions(discovery: dict, lang: str = "en") -> dict:
    """Return canonical question bank as a 4-batch JSON tree."""
    return {
        "schema_version": "1.0",
        "lang": lang,
        "batches": [
            {
                "id": "version-and-name",
                "questions": [
                    {"id": "version", "header": "Version", "type": "text",
                     "question": "Bundle version (SemVer 2.0.0, e.g. 1.0.0)?",
                     "default": "0.1.0", "validate": "semver"},
                    {"id": "bundle_name", "header": "Bundle name", "type": "text",
                     "question": "Bundle filename stem?",
                     "default": "claude-pack"},
                ],
            },
            {
                "id": "categories",
                "questions": [
                    {"id": "skills", "header": "Skills", "type": "multi-select",
                     "question": "Which skills to include?",
                     "options": _option_list(discovery["available_skills"])},
                    {"id": "agents", "header": "Agents", "type": "multi-select",
                     "question": "Which agents to include?",
                     "options": _option_list(discovery["available_agents"])},
                    {"id": "hooks", "header": "Hooks", "type": "multi-select",
                     "question": "Which hooks to include?",
                     "options": _option_list(discovery["available_hooks"])},
                    {"id": "rules", "header": "Rules", "type": "multi-select",
                     "question": "Which rules to include?",
                     "options": _option_list(discovery["available_rules"])},
                ],
            },
            {
                "id": "top-level",
                "questions": [
                    {"id": "include_readme", "header": "README", "type": "bool",
                     "question": "Include repo-root README.md?",
                     "default": False, "available": discovery["has_readme"]},
                    {"id": "include_claudemd", "header": "CLAUDE.md", "type": "bool",
                     "question": "Include repo-root CLAUDE.md?",
                     "default": False, "available": discovery["has_claudemd"]},
                    {"id": "include_settings", "header": "settings.json", "type": "bool",
                     "question": "Include .claude/settings.json? (opt-in only)",
                     "default": False, "available": discovery["has_settings"]},
                    {"id": "include_ck_config", "header": ".ck.json", "type": "bool",
                     "question": "Include .claude/.ck.json? (opt-in only)",
                     "default": False, "available": discovery["has_ck_config"]},
                ],
            },
            {
                "id": "extras-and-shared",
                "questions": [
                    {"id": "extra", "header": "Extra paths", "type": "text-list",
                     "question": "Extra repo-relative paths (comma-separated). "
                                 "NO absolute, NO `..`.",
                     "default": []},
                    {"id": "follow_shared", "header": "_shared/", "type": "bool",
                     "question": "Auto-include _shared/<name> refs from packed skills? "
                                 "(default false = warn-only)",
                     "default": False},
                ],
            },
        ],
    }
