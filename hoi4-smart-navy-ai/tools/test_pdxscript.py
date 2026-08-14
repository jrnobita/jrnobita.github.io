#!/usr/bin/env python3
"""Tests for the Clausewitz parser. Run: python3 tools/test_pdxscript.py"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pdxscript import Block, ParseError, parse, walk  # noqa: E402

FAILURES: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name} {detail}")
        FAILURES.append(name)


def expect_parse_error(name: str, text: str, fragment: str) -> None:
    try:
        parse(text)
    except ParseError as exc:
        check(name, fragment in str(exc), f"(got {exc})")
        return
    check(name, False, "(no error raised)")


def main() -> int:
    tree = parse(
        """
        # a comment { with a brace } and an = sign
        ai_strategy_plan = {
            name = "Germany — stay out of the Channel"
            enable = { has_war_with = ENG }
            ai_strategy = { type = naval_avoid_region id = 32 value = 200 }
            ai_strategy = { type = area_priority id = 15 value = 100 }
        }
        """
    )
    check("top level has one plan", len(tree) == 1)
    plan = tree.children[0].block
    check("plan is a block", isinstance(plan, Block))
    assert plan is not None
    check("quoted name survives the em dash", plan.scalar("name") == "Germany — stay out of the Channel")
    check("two ai_strategy entries", len(plan.get_all("ai_strategy")) == 2)
    first = plan.get_all("ai_strategy")[0].block
    assert first is not None
    check("type is read", first.scalar("type") == "naval_avoid_region")
    check("id is read", first.scalar("id") == "32")

    tree = parse("has_navy_size = { type = submarine size > 20 }")
    inner = tree.children[0].block
    assert inner is not None
    size = inner.get("size")
    assert size is not None
    check("comparison operator is preserved", size.op == ">" and size.value == "20")

    tree = parse('tags={ "Gameplay" "AI" }')
    tags = tree.children[0].block
    assert tags is not None
    check("bare list items parse", [c.value for c in tags.children] == ["Gameplay", "AI"])
    check("list items have no key", all(c.key is None for c in tags.children))

    tree = parse("a = { b = { c = { d = 1 } } }")
    keys = [trail[-1] for trail, _node in walk(tree)]
    check("walk reaches every depth", keys == ["a", "b", "c", "d"])

    tree = parse("name = value # trailing comment")
    check("trailing comment is dropped", tree.scalar("name") == "value")

    tree = parse('desc = "a \\"quoted\\" word"')
    check("escaped quotes survive", tree.scalar("desc") == 'a "quoted" word')

    tree = parse("date = 1936.1.1\nvalue = -25\nid = GER_focus.3")
    check("dotted and negative scalars parse", tree.scalar("value") == "-25")
    check("dotted ids parse", tree.scalar("id") == "GER_focus.3")

    expect_parse_error("unclosed brace is caught", "a = { b = 1", "unclosed")
    expect_parse_error("stray close brace is caught", "a = 1 }", "unexpected '}'")
    expect_parse_error("missing value is caught", "a = { b = }", "no value")
    expect_parse_error("unterminated string is caught", 'a = "oops', "unterminated string")

    try:
        parse("a = { b = 1\nc = { d = 2 }\n")
    except ParseError as exc:
        check("error names the line the brace opened on", ":1:" in str(exc) or "line 1" in str(exc), f"(got {exc})")

    print()
    if FAILURES:
        print(f"{len(FAILURES)} failing: {', '.join(FAILURES)}")
        return 1
    print("all parser tests pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
