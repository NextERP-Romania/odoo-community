#!/usr/bin/env python3
"""Print the addons this repository depends on but does not contain.

These are Odoo core, enterprise and OCA modules. They change when the
container image or requirements change, not when we push, which is what
makes a database with them installed worth caching between runs.
"""

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    ours, depends = set(), set()
    for manifest in ROOT.glob("*/__manifest__.py"):
        try:
            data = ast.literal_eval(manifest.read_text())
        except (SyntaxError, ValueError):
            continue
        ours.add(manifest.parent.name)
        if data.get("installable", True):
            depends |= set(data.get("depends") or ())
    return ",".join(sorted(depends - ours))


if __name__ == "__main__":
    print(main())
