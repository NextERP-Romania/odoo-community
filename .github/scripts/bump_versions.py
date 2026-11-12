#!/usr/bin/env python3
"""Ridica ultima cifra din versiunea modulelor atinse de un pull request.

Un modul se considera atins daca pull request-ul ii schimba cod, vederi, date
sau teste -- nu si daca ii schimba doar documentatia generata (README.rst,
static/description/) sau traducerile, care nu schimba comportamentul.

Daca versiunea din `__manifest__.py` s-a mutat deja fata de baza, modulul e
lasat in pace; altfel i se incrementeaza ultimul segment.

Folosire:
    python3 .github/scripts/bump_versions.py <base> [<head>]   # bumpeaza
    python3 .github/scripts/bump_versions.py --check <base>    # doar raporteaza
"""

import argparse
import ast
import os
import re
import subprocess
import sys

# Fisiere care nu justifica singure un bump: sunt scrise de boti (readme-ul
# generat, coperta modulului) sau sunt traduceri.
IGNORED = re.compile(
    r"""(?x)
    ^README\.rst$
    | ^readme/
    | ^static/description/
    | ^i18n/
    | ^pyproject\.toml$
    """
)

VERSION_RE = re.compile(r"""(["']version["']\s*:\s*)(["'])([^"']*)(["'])""")


def run(*args):
    return subprocess.run(
        args, check=True, capture_output=True, text=True
    ).stdout


def file_at(rev, path):
    """Continutul lui `path` la revizia `rev`, sau None daca nu exista."""
    proc = subprocess.run(
        ["git", "show", f"{rev}:{path}"], capture_output=True, text=True
    )
    return proc.stdout if proc.returncode == 0 else None


def manifest_version(text):
    if text is None:
        return None
    try:
        return ast.literal_eval(text).get("version")
    except (SyntaxError, ValueError):
        match = VERSION_RE.search(text)
        return match.group(3) if match else None


def touched_addons(base, head):
    """Modulele atinse de diff, cu fisierele lor relevante."""
    changed = run("git", "diff", "--name-only", f"{base}...{head}").split()
    addons = {}
    for path in changed:
        head_dir, _, rest = path.partition("/")
        if not rest or IGNORED.search(rest):
            continue
        if not os.path.isfile(os.path.join(head_dir, "__manifest__.py")):
            # Modul sters, sau fisier din afara modulelor (.github, docs).
            continue
        addons.setdefault(head_dir, []).append(path)
    return addons


def bumped(version):
    parts = version.split(".")
    if not parts[-1].isdigit():
        return None
    parts[-1] = str(int(parts[-1]) + 1)
    return ".".join(parts)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base", help="revizia de baza a pull request-ului")
    parser.add_argument("head", nargs="?", default="HEAD")
    parser.add_argument(
        "--check",
        action="store_true",
        help="nu modifica nimic; iese cu 1 daca lipseste vreun bump",
    )
    args = parser.parse_args(argv)

    missing = []
    for addon, files in sorted(touched_addons(args.base, args.head).items()):
        manifest = os.path.join(addon, "__manifest__.py")
        old = manifest_version(file_at(args.base, manifest))
        if old is None:
            # Modul nou: versiunea din manifest e deja cea buna.
            continue
        new_text = open(manifest, encoding="utf-8").read()
        current = manifest_version(new_text)
        if current != old:
            print(f"{addon}: versiune deja ridicata ({old} -> {current})")
            continue
        target = bumped(current or "")
        if target is None:
            print(f"::warning::{addon}: versiune neinteligibila ({current!r})")
            continue
        missing.append((addon, current, target, files))

    if not missing:
        print("Toate modulele atinse au versiunea ridicata.")
        return 0

    for addon, current, target, files in missing:
        if args.check:
            print(
                f"::error file={addon}/__manifest__.py::{addon}: "
                f"versiunea a ramas {current}; ridic-o la {target} "
                f"({len(files)} fisiere schimbate)"
            )
            continue
        manifest = os.path.join(addon, "__manifest__.py")
        text = open(manifest, encoding="utf-8").read()
        text = VERSION_RE.sub(
            lambda m: f"{m.group(1)}{m.group(2)}{target}{m.group(4)}",
            text,
            count=1,
        )
        open(manifest, "w", encoding="utf-8").write(text)
        print(f"{addon}: {current} -> {target}")

    if args.check:
        return 1
    # Lista modulelor bumpate, pentru mesajul de commit.
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a", encoding="utf-8") as fobj:
            fobj.write("bumped=" + ",".join(a for a, _, _, _ in missing) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
