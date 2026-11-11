#!/usr/bin/env python3
"""scripts/generate-gp4.py — Generate PS4 .gp4 project file directly from a staged directory.

Bypasses create-gp4 CLI argument limits (OS [Errno 7] Argument list too long)
and supports games with thousands of mod files (e.g. Kitserver with 12,000+ files).
Strictly enforces <volume_type>pkg_ps4_app</volume_type> (ContentType.GD) to avoid PS4 error 2157510736.
"""

import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import sys


def build_dir_tree(dirs):
    """Build nested dict hierarchy from set of relative directory paths."""
    tree = {}
    for d in sorted(dirs):
        parts = Path(d).parts
        cur = tree
        for part in parts:
            cur = cur.setdefault(part, {})
    return tree


def render_dir_tree(node, depth=2):
    """Render nested <dir targ_name="..."> tags matching LibOrbisPkg hierarchy."""
    lines = []
    indent = "\t" * depth
    for name in sorted(node.keys()):
        children = node[name]
        lines.append(f'{indent}<dir targ_name="{name}">')
        if children:
            lines.extend(render_dir_tree(children, depth + 1))
        lines.append(f'{indent}</dir>')
    return lines


def generate_gp4(stage_dir: Path, content_id: str, output_gp4: Path):
    stage_dir = stage_dir.resolve()
    files = []
    dir_set = set()

    for p in stage_dir.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(stage_dir).as_posix()
        # Skip package artifacts, logs, and gp4 project files
        if rel in ("pkg.gp4", "pkg-build.log") or rel.endswith(".pkg") or rel.endswith(".log"):
            continue
        files.append(rel)

        # Collect all parent directories up to root
        parent = p.relative_to(stage_dir).parent
        while parent != Path("."):
            dir_set.add(parent.as_posix())
            parent = parent.parent

    files.sort()
    tree = build_dir_tree(dir_set)

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    xml_lines = [
        '<?xml version="1.0"?>',
        '<psproject xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" fmt="gp4" version="1000">',
        '\t<volume>',
        '\t\t<volume_type>pkg_ps4_app</volume_type>',
        '\t\t<volume_id>PS4VOLUME</volume_id>',
        f'\t\t<volume_ts>{ts}</volume_ts>',
        f'\t\t<package content_id="{content_id}" passcode="00000000000000000000000000000000"',
        '\t\t\tstorage_type="digital50" app_type="full" />',
        '\t\t<chunk_info chunk_count="1" scenario_count="1">',
        '\t\t\t<chunks>',
        '\t\t\t\t<chunk id="0" layer_no="0" label="Chunk #0" />',
        '\t\t\t</chunks>',
        '\t\t\t<scenarios default_id="0">',
        '\t\t\t\t<scenario id="0" type="sp" initial_chunk_count="1" label="Scenario #0">0</scenario>',
        '\t\t\t</scenarios>',
        '\t\t</chunk_info>',
        '\t</volume>',
        '\t<files img_no="0">',
    ]

    for f in files:
        xml_lines.append(f'\t\t<file targ_path="{f}" orig_path="{f}" />')

    xml_lines.append('\t</files>')
    xml_lines.append('\t<rootdir>')
    xml_lines.extend(render_dir_tree(tree, depth=2))
    xml_lines.append('\t</rootdir>')
    xml_lines.append('</psproject>')
    xml_lines.append('')

    output_gp4.write_text("\n".join(xml_lines), encoding="utf-8")
    print(f"[+] Successfully generated GP4 project: {output_gp4} ({len(files)} files, {len(dir_set)} directories)")


def main():
    parser = argparse.ArgumentParser(description="Generate PS4 .gp4 project file")
    parser.add_argument("--stage-dir", required=True, type=Path, help="Path to staged package files")
    parser.add_argument("--content-id", required=True, help="PS4 Package Content ID")
    parser.add_argument("--output", required=True, type=Path, help="Output .gp4 file path")
    args = parser.parse_args()

    if not args.stage_dir.is_dir():
        print(f"[ERROR] Stage directory not found: {args.stage_dir}", file=sys.stderr)
        sys.exit(1)

    generate_gp4(args.stage_dir, args.content_id, args.output)


if __name__ == "__main__":
    main()

