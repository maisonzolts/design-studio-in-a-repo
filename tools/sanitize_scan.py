#!/usr/bin/env python3
"""Fail closed when public-release contains common private-data indicators."""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

TEXT_EXTENSIONS = {
    "", ".css", ".gitignore", ".html", ".js", ".json", ".md", ".mjs",
    ".py", ".sh", ".toml", ".txt", ".yaml", ".yml",
}
BANNED_EXTENSIONS = {
    ".7z", ".ai", ".db", ".dll", ".doc", ".docx", ".exe", ".gif", ".heic",
    ".indd", ".jpeg", ".jpg", ".mov", ".mp3", ".mp4", ".otf", ".pdf", ".png",
    ".psd", ".pyc", ".rar", ".sqlite", ".ttf", ".wav", ".webp", ".woff",
    ".woff2", ".xls", ".xlsx", ".zip",
}
# Needle for the excluded private strategy-document title, assembled from
# fragments so this public detector file never spells the title out and
# cannot match its own configuration. The compiled pattern is unchanged.
_EXCLUDED_STRATEGY_TITLE = r"\s+".join(("Mais" + "on", "Mast" + "er", "Pl" + "an"))
PATTERNS = {
    "access key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "GitHub token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    "Slack token": re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),
    "private key": re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----"),
    "JWT": re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),
    "generic secret": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "email": re.compile(r"(?<![<{])[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}(?![>}])", re.I),
    "phone": re.compile(r"(?<!\d)(?:\+?1[-.\s]?)?\(?[2-9]\d{2}\)?[-.\s]\d{3}[-.\s]\d{4}(?!\d)"),
    "currency amount": re.compile(r"(?:[$€£]\s?\d|(?:USD|CAD|EUR|GBP)\s+\d)", re.I),
    "Windows user path": re.compile(r"C:[/\\]Users[/\\]", re.I),
    "private drive path": re.compile(r"\b[A-Z]:\\", re.I),
    "macOS home path": re.compile("/" + r"Users/[^/<\s]+"),
    "Linux home path": re.compile("/" + r"home/[^/<\s]+"),
    "excluded strategy phrase": re.compile(_EXCLUDED_STRATEGY_TITLE, re.I),
    "webhook URL": re.compile(r"https://hooks\.[^\s\"')]+", re.I),
    "Slack webhook path": re.compile(r"hooks\.slack\.com/services/", re.I),
    "Stripe key": re.compile(r"\b(?:sk|rk|pk)_(?:live|test)_[A-Za-z0-9]{8,}\b"),
    "HubSpot token": re.compile(r"\bpat-[a-z0-9-]{10,}\b", re.I),
    "Google API key": re.compile(r"\bAIza[0-9A-Za-z_\-]{20,}\b"),
    "Anthropic key": re.compile(r"\bsk-ant-[A-Za-z0-9_-]{10,}\b"),
    "UUID or machine id": re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b", re.I),
}
# Approved attributions: source names that may appear in specific files because
# the release intentionally retains third-party credit there. The cockpit code
# keeps its original author's MIT notice; the docs point at that notice. Any
# match of a source name outside these files is still a finding.
APPROVED_ATTRIBUTIONS = {
    "Tom Lyons": {"cockpit/LICENSE", "cockpit/README.md", "README.md", "HANDOFF.md"},
}
# Files whose content is detector configuration, not data. The source-name
# check skips them so the exemption list above cannot flag itself; every other
# pattern still runs on them.
DETECTOR_FILES = {"tools/sanitize_scan.py"}
CODE_SUFFIXES = {".js", ".mjs", ".py"}
BROKEN_PLACEHOLDER = re.compile(
    "<" + "DRIVE_ROOT>|"
    "<" + "USER_HOME>|"
    "<" + "SVETLANA_ROOT>|"
    "(?:htt|fil|wss?)<"
)


def source_names(source: Path | None) -> set[str]:
    names: set[str] = set()
    if source is None:
        return names
    root = source / "Brand Identity Directory"
    if not root.is_dir():
        return names
    for owner in root.iterdir():
        if not owner.is_dir() or owner.name.startswith("_"):
            continue
        names.add(owner.name)
        names.update(child.name for child in owner.iterdir() if child.is_dir())
    return {name for name in names if len(name) >= 4}


def scan(root: Path, source: Path | None = None) -> list[str]:
    findings: list[str] = []
    names = source_names(source)
    tracked = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=root,
        check=True,
        capture_output=True,
    ).stdout.decode("utf-8").split("\0")
    for rel_name in sorted(name for name in tracked if name):
        path = root / rel_name
        if not path.is_file():
            findings.append(f"{rel_name}: tracked path is missing")
            continue
        rel = path.relative_to(root)
        suffix = path.suffix.lower()
        if suffix in BANNED_EXTENSIONS:
            findings.append(f"{rel}: banned binary/export extension {suffix}")
            continue
        raw = path.read_bytes()
        if b"\0" in raw:
            findings.append(f"{rel}: binary NUL byte")
            continue
        if suffix not in TEXT_EXTENSIONS and path.name not in {".env.example", ".gitkeep"}:
            findings.append(f"{rel}: unreviewed file type {suffix or '<none>'}")
            continue
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            findings.append(f"{rel}: not UTF-8 text")
            continue
        for label, pattern in PATTERNS.items():
            for match in pattern.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                findings.append(f"{rel}:{line}: {label}")
        if suffix in CODE_SUFFIXES:
            for match in BROKEN_PLACEHOLDER.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                findings.append(f"{rel}:{line}: broken path placeholder in code")
        lower = text.casefold()
        if str(rel) not in DETECTOR_FILES:
            for name in names:
                if name.casefold() in lower:
                    if str(rel) in APPROVED_ATTRIBUTIONS.get(name, set()):
                        continue
                    findings.append(f"{rel}: source client/brand name match")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--source", help="private source checkout used only to derive client-name needles")
    args = parser.parse_args()
    findings = scan(Path(args.root).resolve(), Path(args.source).resolve() if args.source else None)
    if findings:
        print("\n".join(findings))
        return 1
    print("SANITIZATION SCAN CLEAN")
    return 0


if __name__ == "__main__":
    sys.exit(main())
