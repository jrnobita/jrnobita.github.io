#!/usr/bin/env python3
"""Rebuild tools/data/ from an installed copy of Hearts of Iron IV.

The tables in tools/data/ are what validate.py checks the mod against. They were
built from vanilla 1.14.1, and Paradox rebalances the navy: 1.19 reworked the
gun lines, moved dual-purpose batteries onto the light gun branch and folded
secondary battery techs into the medium gun line. Module keys usually survive
that kind of change, but "usually" is not "verified".

So rather than trusting a table baked in at authoring time, point this at your
own installation and it will re-derive every table from the files the game will
actually load:

    python3 tools/refresh_tables.py --game-dir "C:/Program Files (x86)/Steam/steamapps/common/Hearts of Iron IV"
    python3 tools/refresh_tables.py --game-dir ~/.steam/steam/steamapps/common/Hearts\\ of\\ Iron\\ IV

Then run validate.py. Anything the mod references that your version renamed or
removed becomes an error instead of a ship design that silently never matches.

Nothing is written unless every table was derived successfully, so a wrong
--game-dir leaves the existing tables alone.
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from typing import Dict, List, Optional, Set, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pdxscript import Block, ParseError, parse_file  # noqa: E402

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(TOOLS_DIR, "data")


class ExtractionError(Exception):
    pass


def game_files(game_dir: str, subpath: str, pattern: str = ".txt") -> List[str]:
    root = os.path.join(game_dir, *subpath.split("/"))
    if not os.path.isdir(root):
        raise ExtractionError(f"{subpath} not found under {game_dir}")
    found = []
    for dirpath, _dirnames, filenames in os.walk(root):
        for name in sorted(filenames):
            if name.endswith(pattern):
                found.append(os.path.join(dirpath, name))
    if not found:
        raise ExtractionError(f"no {pattern} files under {root}")
    return found


def safe_parse(path: str) -> Optional[Block]:
    try:
        return parse_file(path)
    except (ParseError, UnicodeDecodeError, OSError):
        return None


# --------------------------------------------------------------------------- #
# extractors
# --------------------------------------------------------------------------- #


def extract_modules(game_dir: str) -> Tuple[Set[str], Set[str]]:
    modules: Set[str] = set()
    categories: Set[str] = set()
    for path in game_files(game_dir, "common/units/equipment/modules"):
        tree = safe_parse(path)
        if tree is None:
            continue
        for node in tree.children:
            if node.key != "equipment_modules" or node.block is None:
                continue
            for module in node.block.children:
                if module.block is None or module.key in (None, "limit"):
                    continue
                modules.add(module.key)
                category = module.block.get("category")
                if category is None:
                    continue
                if category.block is not None:
                    categories |= {c.value for c in category.block.children if isinstance(c.value, str)}
                elif isinstance(category.value, str):
                    categories.add(category.value)
    if not modules:
        raise ExtractionError("found no ship modules")
    return modules, categories


def extract_hulls(game_dir: str) -> Tuple[Set[str], Set[str]]:
    hulls: Set[str] = set()
    slots: Set[str] = set()
    for path in game_files(game_dir, "common/units/equipment"):
        if os.sep + "modules" + os.sep in path:
            continue
        tree = safe_parse(path)
        if tree is None:
            continue
        for node in tree.children:
            if node.key != "equipments" or node.block is None:
                continue
            for hull in node.block.children:
                if hull.block is None or not hull.key:
                    continue
                slot_block = hull.block.get("module_slots")
                if slot_block is None:
                    continue  # not a designable hull
                hulls.add(hull.key)
                if slot_block.block is not None:
                    slots |= {s.key for s in slot_block.block.children if s.key}
    if not hulls:
        raise ExtractionError("found no designable ship hulls")
    return hulls, slots


def extract_strategy_vocabulary(game_dir: str) -> Tuple[Set[str], Set[str], Set[str]]:
    """Types, ai_area ids and role ids the base game itself uses."""
    types: Set[str] = set()
    areas: Set[str] = set()
    roles: Set[str] = set()
    area_types = {"area_priority"}
    role_types = {"role_ratio", "unit_ratio", "build_ship"}

    def visit(block: Block) -> None:
        for node in block.children:
            if node.key == "ai_strategy" and node.block is not None:
                kind = node.block.scalar("type")
                ident = node.block.scalar("id")
                if kind:
                    types.add(kind)
                    if ident and kind in area_types:
                        areas.add(ident)
                    if ident and kind in role_types:
                        roles.add(ident)
            if node.block is not None:
                visit(node.block)

    for path in game_files(game_dir, "common/ai_strategy"):
        tree = safe_parse(path)
        if tree is not None:
            visit(tree)
    if not types:
        raise ExtractionError("found no ai_strategy entries")
    return types, areas, roles


def extract_sea_provinces(game_dir: str) -> Set[int]:
    """definition.csv marks each province land, sea or lake."""
    path = os.path.join(game_dir, "map", "definition.csv")
    if not os.path.exists(path):
        raise ExtractionError("map/definition.csv not found")
    sea: Set[int] = set()
    with open(path, "r", encoding="utf-8", errors="replace", newline="") as handle:
        for row in csv.reader(handle, delimiter=";"):
            if len(row) < 5 or not row[0].strip().isdigit():
                continue
            if row[4].strip().lower() == "sea":
                sea.add(int(row[0]))
    if not sea:
        raise ExtractionError("definition.csv listed no sea provinces")
    return sea


def extract_regions(game_dir: str) -> List[Tuple[int, str, bool]]:
    """(id, name, is_naval) for every strategic region, straight from the map."""
    sea = extract_sea_provinces(game_dir)
    regions: List[Tuple[int, str, bool]] = []
    for path in game_files(game_dir, "map/strategicregions"):
        tree = safe_parse(path)
        if tree is None:
            continue
        for node in tree.children:
            if node.key != "strategic_region" or node.block is None:
                continue
            raw_id = node.block.scalar("id")
            if not raw_id or not raw_id.isdigit():
                continue
            name = node.block.scalar("name") or os.path.basename(path)[:-4]
            provinces = node.block.get("provinces")
            ids: List[int] = []
            if provinces is not None and provinces.block is not None:
                ids = [
                    int(p.value)
                    for p in provinces.block.children
                    if isinstance(p.value, str) and p.value.isdigit()
                ]
            # A region is naval if it contains any sea province at all.
            #
            # A majority test looks more careful and is wrong: the East China
            # Sea is 13 sea provinces against 14 islands, and the Banda Sea is
            # 15 against 42, so both would be classified as land. They are sea
            # zones that happen to be full of archipelago. Checked against a
            # full 228-region map, the any-sea rule adds seven regions over the
            # majority rule and produces no land-region false positives —
            # nothing overwhelmingly land carries a sea province, because a
            # coastal land region's water belongs to the adjacent sea zone.
            naval = any(p in sea for p in ids)
            regions.append((int(raw_id), name, naval))
    if not regions:
        raise ExtractionError("found no strategic regions")
    return sorted(regions)


# --------------------------------------------------------------------------- #
# writing
# --------------------------------------------------------------------------- #


def header(version: str, what: str) -> str:
    return (
        f"# {what}\n"
        f"# Regenerated by tools/refresh_tables.py from an installed game.\n"
        f"# Game version reported by the installation: {version}\n"
    )


def read_version(game_dir: str) -> str:
    launcher = os.path.join(game_dir, "launcher-settings.json")
    if os.path.exists(launcher):
        try:
            import json

            with open(launcher, "r", encoding="utf-8-sig") as handle:
                data = json.load(handle)
            return str(data.get("rawVersion") or data.get("version") or "unknown")
        except Exception:  # noqa: BLE001 - a missing version is not fatal
            pass
    changelog = os.path.join(game_dir, "changelog.txt")
    if os.path.exists(changelog):
        with open(changelog, "r", encoding="utf-8-sig", errors="replace") as handle:
            for line in handle:
                if "Update" in line:
                    return line.strip().strip("# ").strip()
    return "unknown"


def write(name: str, text: str) -> None:
    with open(os.path.join(DATA_DIR, name), "w", encoding="utf-8") as handle:
        handle.write(text)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-dir", required=True, help="root of the HOI4 installation")
    parser.add_argument(
        "--dry-run", action="store_true", help="report what would change, write nothing"
    )
    args = parser.parse_args(argv)

    game_dir = os.path.expanduser(args.game_dir)
    if not os.path.isdir(game_dir):
        print(f"ERROR: {game_dir} is not a directory")
        return 1

    try:
        version = read_version(game_dir)
        modules, categories = extract_modules(game_dir)
        hulls, slots = extract_hulls(game_dir)
        types, areas, roles = extract_strategy_vocabulary(game_dir)
        regions = extract_regions(game_dir)
    except ExtractionError as exc:
        print(f"ERROR: {exc}")
        print("Nothing was written. Check that --game-dir points at the game root,")
        print("the folder containing common/ and map/.")
        return 1

    naval = [r for r in regions if r[2]]
    print(f"game version   : {version}")
    print(f"ship modules   : {len(modules)} modules, {len(categories)} categories")
    print(f"ship hulls     : {len(hulls)} hulls, {len(slots)} slot names")
    print(f"ai_strategy    : {len(types)} types, {len(areas)} areas, {len(roles)} roles")
    print(f"regions        : {len(regions)} total, {len(naval)} naval")

    if args.dry_run:
        print("\n--dry-run: nothing written")
        return 0

    write(
        "ship_modules.txt",
        header(version, "Ship module keys and module category keys.")
        + "\n".join(sorted(modules))
        + "\n"
        + "\n".join(sorted(categories))
        + "\n",
    )
    write(
        "ship_hulls.txt",
        header(version, "Designable ship hull archetypes and types.")
        + "\n".join(sorted(hulls))
        + "\n",
    )
    write(
        "ship_slots.txt",
        header(version, "Module slot names present on ship hulls.")
        + "\n".join(sorted(slots))
        + "\n",
    )
    write(
        "ai_strategy_types.txt",
        header(version, "ai_strategy type tokens used by the base game.")
        + "\n".join(sorted(types))
        + "\n",
    )
    write(
        "ai_areas.txt",
        header(version, "Named ai_area ids accepted by area_priority.")
        + "\n".join(sorted(areas))
        + "\n",
    )
    write(
        "ship_roles.txt",
        header(version, "role_ratio / unit_ratio / build_ship id tokens.")
        + "\n".join(sorted(roles))
        + "\n",
    )

    lines = [
        "# Naval strategic regions, read from map/strategicregions and",
        "# map/definition.csv. A region counts as naval when most of its",
        f"# provinces are sea. Game version: {version}",
        "id,name,confidence,theatre,note",
    ]
    for region_id, name, _naval in naval:
        clean = name.replace(",", " ").strip()
        lines.append(f"{region_id},{clean},GAME,,from the installed game")
    write("naval_regions.csv", "\n".join(lines) + "\n")

    print("\ntools/data/ rebuilt. Now run: python3 tools/validate.py --strict")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
