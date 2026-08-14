#!/usr/bin/env python3
"""Static checks for the Smart Navy AI mod.

HOI4 fails quietly. A misspelled `ai_strategy` type, a strategic region id that
does not exist, or a scripted effect that was renamed in one file but not the
other all produce a mod that loads, runs, and does nothing — the failure only
shows up as an unremarkable game where the AI still sails into the Channel.

Run this before shipping:

    python3 tools/validate.py            # check the mod next to this script
    python3 tools/validate.py --strict   # treat warnings as failures too

Exit code is 0 when there are no errors, 1 otherwise.
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Set, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pdxscript import Block, Node, ParseError, parse_file, walk  # noqa: E402

MOD_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(MOD_ROOT, "tools", "data")

# Strategy types whose `id` names a strategic region rather than a state,
# a country or an equipment archetype.
REGION_ID_STRATEGIES = {
    "area_priority",
    "naval_avoid_region",
    "naval_convoy_raid_region",
    "naval_convoy_escort_region",
    "naval_mission_threshold",
    "invasion_unit_request",
    "strategic_air_importance",
}

# Strategy types whose `id` names a country tag.
TAG_ID_STRATEGIES = {
    "conquer",
    "contain",
    "consider_weak",
    "ignore",
    "antagonize",
    "befriend",
    "protect",
    "alliance",
    "influence",
    "front_control",
    "declare_war",
    "prepare_for_war",
    "send_lend_lease",
    "send_volunteers_desire",
    "diplo_action_desire",
    "diplo_action_acceptance",
}

TAG_RE = re.compile(r"^[A-Z]{3}$")
INT_RE = re.compile(r"^-?\d+$")


@dataclass
class Report:
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    checks_run: int = 0

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def note(self, message: str) -> None:
        self.notes.append(message)


# --------------------------------------------------------------------------- #
# data tables
# --------------------------------------------------------------------------- #


def load_lines(name: str) -> Optional[Set[str]]:
    path = os.path.join(DATA_DIR, name)
    if not os.path.exists(path):
        return None
    values: Set[str] = set()
    with open(path, "r", encoding="utf-8") as handle:
        for raw in handle:
            line = raw.split("#", 1)[0].strip()
            if line:
                values.add(line)
    return values


def load_regions() -> Optional[Dict[int, Tuple[str, str]]]:
    """id -> (name, confidence). Confidence is HIGH/MEDIUM/LOW."""
    path = os.path.join(DATA_DIR, "naval_regions.csv")
    if not os.path.exists(path):
        return None
    regions: Dict[int, Tuple[str, str]] = {}
    with open(path, "r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if not row.get("id", "").strip().isdigit():
                continue
            regions[int(row["id"])] = (
                row.get("name", "").strip(),
                row.get("confidence", "").strip().upper() or "UNKNOWN",
            )
    return regions


# --------------------------------------------------------------------------- #
# file collection
# --------------------------------------------------------------------------- #


def script_files() -> List[str]:
    found: List[str] = []
    for sub in ("common", "events", "history", "map"):
        root = os.path.join(MOD_ROOT, sub)
        for dirpath, _dirnames, filenames in os.walk(root):
            for filename in sorted(filenames):
                if filename.endswith(".txt"):
                    found.append(os.path.join(dirpath, filename))
    return sorted(found)


def rel(path: str) -> str:
    return os.path.relpath(path, MOD_ROOT)


# --------------------------------------------------------------------------- #
# checks
# --------------------------------------------------------------------------- #


def check_parse(report: Report) -> Dict[str, Block]:
    """Every script file must parse. This catches the unbalanced brace."""
    report.checks_run += 1
    trees: Dict[str, Block] = {}
    files = script_files()
    if not files:
        report.warn("no script files found under common/ or events/")
        return trees
    for path in files:
        try:
            trees[path] = parse_file(path)
        except ParseError as exc:
            report.error(f"parse failure — {exc}")
        except UnicodeDecodeError as exc:
            report.error(f"{rel(path)}: not valid UTF-8 ({exc})")
    report.note(f"parsed {len(trees)}/{len(files)} script files")
    return trees


def check_descriptor(report: Report) -> None:
    """descriptor.mod and the launcher-side .mod file must agree."""
    report.checks_run += 1
    descriptor = os.path.join(MOD_ROOT, "descriptor.mod")
    if not os.path.exists(descriptor):
        report.error("descriptor.mod is missing — the launcher will not list the mod")
        return
    try:
        tree = parse_file(descriptor)
    except ParseError as exc:
        report.error(f"descriptor.mod does not parse — {exc}")
        return

    for required in ("name", "supported_version"):
        if tree.get(required) is None:
            report.error(f"descriptor.mod has no `{required}`")

    tags = tree.get("tags")
    if tags is None or tags.block is None:
        report.warn("descriptor.mod has no `tags` block — the launcher shows it uncategorised")

    if tree.get("path") is not None:
        report.warn(
            "descriptor.mod contains `path` — that key belongs in the launcher-side "
            "<mod>.mod file, not in the copy inside the mod folder"
        )

    outer = [
        f for f in os.listdir(MOD_ROOT) if f.endswith(".mod") and f != "descriptor.mod"
    ]
    if not outer:
        report.warn(
            "no launcher-side <mod>.mod file next to descriptor.mod — see README for "
            "where it has to be copied"
        )
        return
    try:
        outer_tree = parse_file(os.path.join(MOD_ROOT, outer[0]))
    except ParseError as exc:
        report.error(f"{outer[0]} does not parse — {exc}")
        return
    if outer_tree.get("path") is None:
        report.error(f"{outer[0]} has no `path` — the launcher cannot find the mod files")
    name_inner = tree.scalar("name")
    name_outer = outer_tree.scalar("name")
    if name_inner and name_outer and name_inner != name_outer:
        report.error(
            f"descriptor.mod name ({name_inner!r}) and {outer[0]} name ({name_outer!r}) differ"
        )
    version_inner = tree.scalar("supported_version")
    version_outer = outer_tree.scalar("supported_version")
    if version_inner and version_outer and version_inner != version_outer:
        report.warn(
            f"supported_version differs: descriptor.mod {version_inner!r} vs "
            f"{outer[0]} {version_outer!r}"
        )


def iter_ai_strategies(trees: Dict[str, Block]) -> Iterable[Tuple[str, Node]]:
    for path, tree in trees.items():
        if os.sep + "ai_strategy" + os.sep not in path:
            continue
        for _trail, node in walk(tree):
            if node.key == "ai_strategy" and node.block is not None:
                yield path, node


def check_ai_strategy_types(report: Report, trees: Dict[str, Block]) -> None:
    """A misspelled `type` is the classic silent failure."""
    report.checks_run += 1
    known = load_lines("ai_strategy_types.txt")
    if known is None:
        report.warn("tools/data/ai_strategy_types.txt missing — strategy types unchecked")
        return

    seen = 0
    for path, node in iter_ai_strategies(trees):
        seen += 1
        block = node.block
        assert block is not None
        type_value = block.scalar("type")
        if not type_value:
            report.error(f"{rel(path)}:{node.line}: ai_strategy has no `type`")
            continue
        if type_value not in known:
            report.error(
                f"{rel(path)}:{node.line}: unknown ai_strategy type `{type_value}` — "
                f"not in tools/data/ai_strategy_types.txt"
            )
        if block.scalar("value") is None:
            report.error(
                f"{rel(path)}:{node.line}: ai_strategy `{type_value}` has no `value`"
            )
    report.note(f"checked {seen} ai_strategy entries")


def check_region_ids(report: Report, trees: Dict[str, Block]) -> None:
    """Region-scoped strategies must point at a real naval strategic region."""
    report.checks_run += 1
    regions = load_regions()
    if regions is None:
        report.warn("tools/data/naval_regions.csv missing — region ids unchecked")
        return

    used: Counter = Counter()
    for path, node in iter_ai_strategies(trees):
        block = node.block
        assert block is not None
        type_value = block.scalar("type")
        if type_value not in REGION_ID_STRATEGIES:
            continue
        raw_id = block.scalar("id")
        if raw_id is None:
            report.error(f"{rel(path)}:{node.line}: `{type_value}` has no `id`")
            continue
        if not INT_RE.match(raw_id):
            report.error(
                f"{rel(path)}:{node.line}: `{type_value}` id `{raw_id}` is not a number"
            )
            continue
        region_id = int(raw_id)
        used[region_id] += 1
        if region_id not in regions:
            report.error(
                f"{rel(path)}:{node.line}: `{type_value}` points at strategic region "
                f"{region_id}, which is not in tools/data/naval_regions.csv"
            )
            continue
        name, confidence = regions[region_id]
        if confidence == "LOW":
            report.warn(
                f"{rel(path)}:{node.line}: region {region_id} ({name}) is marked "
                f"LOW confidence — verify against the game files before release"
            )
    report.note(f"checked {sum(used.values())} region references across {len(used)} regions")


def check_tag_ids(report: Report, trees: Dict[str, Block]) -> None:
    report.checks_run += 1
    for path, node in iter_ai_strategies(trees):
        block = node.block
        assert block is not None
        type_value = block.scalar("type")
        if type_value not in TAG_ID_STRATEGIES:
            continue
        raw_id = block.scalar("id")
        if raw_id and not TAG_RE.match(raw_id):
            report.error(
                f"{rel(path)}:{node.line}: `{type_value}` id `{raw_id}` is not a "
                f"three-letter country tag"
            )


def collect_definitions(trees: Dict[str, Block], folder: str) -> Dict[str, str]:
    """Top-level keys defined in common/<folder>/ — the trigger or effect names."""
    defined: Dict[str, str] = {}
    marker = os.sep + folder + os.sep
    for path, tree in trees.items():
        if marker not in path:
            continue
        for node in tree.children:
            if node.key:
                defined[node.key] = path
    return defined


def check_scripted_references(report: Report, trees: Dict[str, Block]) -> None:
    """Every scripted trigger/effect the mod calls must be one the mod defines."""
    report.checks_run += 1
    triggers = collect_definitions(trees, "scripted_triggers")
    effects = collect_definitions(trees, "scripted_effects")
    defined = set(triggers) | set(effects)
    if not defined:
        report.note("no scripted triggers or effects defined")
        return

    prefix_owned = tuple(sorted({name.split("_")[0] + "_" for name in defined}))
    used: Dict[str, List[Tuple[str, int]]] = defaultdict(list)

    for path, tree in trees.items():
        if os.sep + "scripted_triggers" + os.sep in path:
            continue
        if os.sep + "scripted_effects" + os.sep in path:
            top_level = {n.key for n in tree.children}
        else:
            top_level = set()
        for _trail, node in walk(tree):
            if not node.key or node.key in top_level:
                continue
            if node.key.startswith(prefix_owned) or node.key in defined:
                used[node.key].append((path, node.line))

    for name, sites in sorted(used.items()):
        if name not in defined:
            first_path, first_line = sites[0]
            report.error(
                f"{rel(first_path)}:{first_line}: calls `{name}`, which is not defined in "
                f"common/scripted_triggers or common/scripted_effects"
            )

    unused = sorted(defined - set(used))
    for name in unused:
        report.warn(f"`{name}` is defined but never used")
    report.note(f"{len(defined)} scripted trigger/effect definitions, {len(used)} used")


def check_events(report: Report, trees: Dict[str, Block]) -> Tuple[Set[str], Set[str]]:
    """Event ids must match their declared namespace and be unique."""
    report.checks_run += 1
    namespaces: Set[str] = set()
    event_ids: Counter = Counter()
    loc_keys: Set[str] = set()

    for path, tree in trees.items():
        if os.sep + "events" + os.sep not in path:
            continue
        file_namespaces = {n.value for n in tree.get_all("add_namespace") if isinstance(n.value, str)}
        namespaces |= file_namespaces
        for node in tree.children:
            if node.key not in ("country_event", "news_event", "state_event", "unit_leader_event"):
                continue
            block = node.block
            if block is None:
                continue
            event_id = block.scalar("id")
            if not event_id:
                report.error(f"{rel(path)}:{node.line}: {node.key} has no `id`")
                continue
            event_ids[event_id] += 1
            namespace = event_id.split(".")[0]
            if namespace not in file_namespaces:
                report.error(
                    f"{rel(path)}:{node.line}: event `{event_id}` uses namespace "
                    f"`{namespace}` but the file declares {sorted(file_namespaces) or 'none'}"
                )
            if block.scalar("hidden") != "yes":
                for key in ("title", "desc"):
                    value = block.scalar(key)
                    if value:
                        loc_keys.add(value)
                for option in block.get_all("option"):
                    if option.block is not None:
                        name = option.block.scalar("name")
                        if name:
                            loc_keys.add(name)
                    else:
                        report.error(f"{rel(path)}:{option.line}: option is not a block")

    for event_id, count in event_ids.items():
        if count > 1:
            report.error(f"event id `{event_id}` is defined {count} times")

    report.note(f"{len(event_ids)} events across {len(namespaces)} namespaces")
    return loc_keys, namespaces


def check_on_actions(report: Report, trees: Dict[str, Block]) -> Set[str]:
    """on_action keys are fixed by the game; a typo means the hook never fires."""
    report.checks_run += 1
    known = load_lines("on_actions.txt")
    referenced_events: Set[str] = set()
    for path, tree in trees.items():
        if os.sep + "on_actions" + os.sep not in path:
            continue
        for node in tree.children:
            if node.key != "on_actions" or node.block is None:
                report.warn(f"{rel(path)}:{node.line}: expected a top-level `on_actions` block")
                continue
            for hook in node.block.children:
                if not hook.key:
                    continue
                if known is not None and hook.key not in known:
                    report.error(
                        f"{rel(path)}:{hook.line}: unknown on_action `{hook.key}` — "
                        f"not in tools/data/on_actions.txt"
                    )
                if hook.block is None:
                    continue
                for effect in hook.block.get_all("effect"):
                    if effect.block is None:
                        continue
                    for _trail, inner in walk(effect.block):
                        if inner.key in ("country_event", "news_event") and inner.block:
                            event_id = inner.block.scalar("id")
                            if event_id:
                                referenced_events.add(event_id)
                for random_events in hook.block.get_all("random_events"):
                    if random_events.block is None:
                        continue
                    for child in random_events.block.children:
                        if child.key and child.key != "0":
                            referenced_events.add(child.key)
    if known is None:
        report.warn("tools/data/on_actions.txt missing — on_action keys unchecked")
    return referenced_events


def check_event_wiring(report: Report, trees: Dict[str, Block], hooked: Set[str]) -> None:
    """An event nothing ever fires is dead weight; a hook pointing nowhere is a bug."""
    report.checks_run += 1
    defined: Set[str] = set()
    fired: Set[str] = set(hooked)
    for path, tree in trees.items():
        for _trail, node in walk(tree):
            if node.key in ("country_event", "news_event", "state_event") and node.block:
                event_id = node.block.scalar("id")
                if event_id and os.sep + "events" + os.sep in path and node.block.get("is_triggered_only"):
                    defined.add(event_id)
                elif event_id and os.sep + "events" + os.sep not in path:
                    fired.add(event_id)
                elif event_id and os.sep + "events" + os.sep in path:
                    defined.add(event_id)
            elif node.key in ("country_event", "news_event") and isinstance(node.value, str):
                fired.add(node.value)

    for path, tree in trees.items():
        if os.sep + "events" + os.sep not in path:
            continue
        for _trail, node in walk(tree):
            if node.key in ("country_event", "news_event") and node.block:
                event_id = node.block.scalar("id")
                if event_id:
                    fired.add(event_id)

    for event_id in sorted(fired - defined):
        report.error(f"something fires event `{event_id}`, which the mod does not define")
    for event_id in sorted(defined - fired):
        report.warn(f"event `{event_id}` is defined but nothing fires it")


def check_localisation(report: Report, needed: Set[str]) -> None:
    """Localisation is the one place HOI4 is picky about encoding."""
    report.checks_run += 1
    loc_root = os.path.join(MOD_ROOT, "localisation")
    if not os.path.isdir(loc_root):
        if needed:
            report.error("localisation/ is missing but events reference localisation keys")
        return

    defined: Dict[str, str] = {}
    entry_re = re.compile(r'^\s*([A-Za-z0-9_.\-]+):\s*(\d+)?\s*"(.*)"\s*$')

    for dirpath, _dirnames, filenames in os.walk(loc_root):
        for filename in sorted(filenames):
            if not filename.endswith(".yml"):
                continue
            path = os.path.join(dirpath, filename)
            language = os.path.basename(dirpath)
            if not filename.endswith(f"_l_{language}.yml"):
                report.error(
                    f"{rel(path)}: filename must end with `_l_{language}.yml` or the game "
                    f"ignores it"
                )
            with open(path, "rb") as handle:
                raw = handle.read()
            if not raw.startswith(b"\xef\xbb\xbf"):
                report.error(
                    f"{rel(path)}: missing UTF-8 BOM — HOI4 silently skips localisation "
                    f"files that do not start with one"
                )
            text = raw.decode("utf-8-sig")
            lines = text.splitlines()
            if not lines or lines[0].strip() != f"l_{language}:":
                report.error(f"{rel(path)}: first line must be `l_{language}:`")
            for number, line in enumerate(lines[1:], start=2):
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                match = entry_re.match(line)
                if not match:
                    report.error(f"{rel(path)}:{number}: malformed localisation entry")
                    continue
                key = match.group(1)
                if key in defined:
                    report.warn(f"{rel(path)}:{number}: duplicate localisation key `{key}`")
                defined[key] = path

    for key in sorted(needed):
        if key not in defined and not key.startswith("["):
            report.error(f"localisation key `{key}` is used by an event but never defined")
    report.note(f"{len(defined)} localisation keys defined")


def check_equipment_modules(report: Report, trees: Dict[str, Block]) -> None:
    """Ship designs reference module and hull keys that must exist in the base game."""
    report.checks_run += 1
    known_modules = load_lines("ship_modules.txt")
    known_hulls = load_lines("ship_hulls.txt")
    if known_modules is None or known_hulls is None:
        report.warn(
            "tools/data/ship_modules.txt or ship_hulls.txt missing — ship designs unchecked"
        )
        return

    designs = 0
    for path, tree in trees.items():
        if os.sep + "ai_equipment_design" + os.sep not in path:
            continue
        for node in tree.children:
            block = node.block
            if block is None:
                continue
            designs += 1
            hull = block.scalar("type")
            if hull and hull not in known_hulls:
                report.error(
                    f"{rel(path)}:{node.line}: design `{node.key}` uses hull `{hull}` "
                    f"which is not in tools/data/ship_hulls.txt"
                )
            modules = block.get("modules")
            if modules is None or modules.block is None:
                report.warn(f"{rel(path)}:{node.line}: design `{node.key}` has no `modules`")
                continue
            for slot in modules.block.children:
                if not slot.key or isinstance(slot.value, Block):
                    continue
                if slot.value in ("empty", "0"):
                    continue
                if slot.value not in known_modules:
                    report.error(
                        f"{rel(path)}:{slot.line}: module `{slot.value}` in slot "
                        f"`{slot.key}` is not in tools/data/ship_modules.txt"
                    )
    report.note(f"checked {designs} AI ship designs")


def check_duplicate_names(report: Report, trees: Dict[str, Block]) -> None:
    """Two strategy plans sharing a name is legal but always a copy-paste slip."""
    report.checks_run += 1
    names: Counter = Counter()
    for path, tree in trees.items():
        if os.sep + "ai_strategy" + os.sep not in path:
            continue
        for node in tree.children:
            if node.block is not None:
                name = node.block.scalar("name")
                if name:
                    names[name] += 1
    for name, count in names.items():
        if count > 1:
            report.warn(f"ai strategy plan name `{name}` is used {count} times")


# --------------------------------------------------------------------------- #
# entry point
# --------------------------------------------------------------------------- #


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true", help="treat warnings as failures")
    parser.add_argument("--quiet", action="store_true", help="only print problems")
    args = parser.parse_args(argv)

    report = Report()
    trees = check_parse(report)
    check_descriptor(report)
    check_ai_strategy_types(report, trees)
    check_region_ids(report, trees)
    check_tag_ids(report, trees)
    check_scripted_references(report, trees)
    loc_keys, _namespaces = check_events(report, trees)
    hooked = check_on_actions(report, trees)
    check_event_wiring(report, trees, hooked)
    check_localisation(report, loc_keys)
    check_equipment_modules(report, trees)
    check_duplicate_names(report, trees)

    if not args.quiet:
        for note in report.notes:
            print(f"  ·  {note}")
    for warning in report.warnings:
        print(f"warning: {warning}")
    for error in report.errors:
        print(f"ERROR:   {error}")

    print(
        f"\n{report.checks_run} checks · {len(report.errors)} errors · "
        f"{len(report.warnings)} warnings"
    )
    if report.errors:
        return 1
    if args.strict and report.warnings:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
