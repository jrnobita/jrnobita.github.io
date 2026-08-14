"""A small, strict parser for Paradox (Clausewitz) script files.

Hearts of Iron IV loads `common/**.txt`, `events/*.txt` and `.mod` descriptors as
Clausewitz script. The game is silent about most mistakes: an unbalanced brace or
a stray operator usually means the whole file is dropped, and the only trace is a
line in `error.log` that nobody reads until the mod "does nothing".

This module exists so the mod can be checked before it is ever loaded.

Grammar (the subset the game actually uses):

    file    := entry*
    entry   := key op value | value          # bare values appear inside lists
    key     := bareword | quoted | number
    op      := "=" | "==" | "!=" | "<" | ">" | "<=" | ">="
    value   := scalar | "{" entry* "}"

Comments run from `#` to end of line. Strings are double quoted.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator, List, Optional, Sequence, Tuple, Union

__all__ = ["ParseError", "Node", "Block", "parse", "parse_file", "walk", "find_all"]


class ParseError(Exception):
    """Raised with a line number so the message is actionable."""

    def __init__(self, message: str, line: int, path: Optional[str] = None) -> None:
        where = f"{path}:{line}" if path else f"line {line}"
        super().__init__(f"{where}: {message}")
        self.message = message
        self.line = line
        self.path = path


# --------------------------------------------------------------------------- #
# tokenizer
# --------------------------------------------------------------------------- #

_OPERATORS = ("<=", ">=", "==", "!=", "=", "<", ">")
_PUNCT = set("{}")
_WHITESPACE = set(" \t\r\n")


@dataclass(frozen=True)
class Token:
    kind: str  # "word" | "string" | "op" | "{" | "}"
    text: str
    line: int


def tokenize(text: str, path: Optional[str] = None) -> List[Token]:
    tokens: List[Token] = []
    i = 0
    line = 1
    n = len(text)

    while i < n:
        ch = text[i]

        if ch == "\n":
            line += 1
            i += 1
            continue
        if ch in _WHITESPACE:
            i += 1
            continue

        if ch == "#":
            while i < n and text[i] != "\n":
                i += 1
            continue

        if ch in _PUNCT:
            tokens.append(Token(ch, ch, line))
            i += 1
            continue

        if ch == '"':
            start_line = line
            i += 1
            buf: List[str] = []
            while True:
                if i >= n:
                    raise ParseError("unterminated string", start_line, path)
                c = text[i]
                if c == "\\" and i + 1 < n:
                    buf.append(text[i + 1])
                    i += 2
                    continue
                if c == '"':
                    i += 1
                    break
                if c == "\n":
                    line += 1
                buf.append(c)
                i += 1
            tokens.append(Token("string", "".join(buf), start_line))
            continue

        matched_op = next((op for op in _OPERATORS if text.startswith(op, i)), None)
        if matched_op:
            tokens.append(Token("op", matched_op, line))
            i += len(matched_op)
            continue

        start = i
        while i < n and text[i] not in _WHITESPACE and text[i] not in _PUNCT and text[i] != "#":
            if text[i] == '"':
                break
            if any(text.startswith(op, i) for op in _OPERATORS):
                break
            i += 1
        if i == start:  # pragma: no cover - defensive
            raise ParseError(f"unexpected character {text[i]!r}", line, path)
        tokens.append(Token("word", text[start:i], line))

    return tokens


# --------------------------------------------------------------------------- #
# parser
# --------------------------------------------------------------------------- #


@dataclass
class Block:
    """A `{ ... }` block: an ordered list of child nodes."""

    children: List["Node"] = field(default_factory=list)
    line: int = 0

    def get(self, key: str) -> Optional["Node"]:
        for child in self.children:
            if child.key == key:
                return child
        return None

    def get_all(self, key: str) -> List["Node"]:
        return [c for c in self.children if c.key == key]

    def scalar(self, key: str) -> Optional[str]:
        node = self.get(key)
        if node is None or isinstance(node.value, Block):
            return node.value if node is not None else None  # type: ignore[return-value]
        return node.value

    def __iter__(self) -> Iterator["Node"]:
        return iter(self.children)

    def __len__(self) -> int:
        return len(self.children)


Value = Union[str, Block]


@dataclass
class Node:
    """One `key op value` pair, or a bare value (key is None)."""

    key: Optional[str]
    op: Optional[str]
    value: Value
    line: int

    @property
    def block(self) -> Optional[Block]:
        return self.value if isinstance(self.value, Block) else None


def parse(text: str, path: Optional[str] = None) -> Block:
    tokens = tokenize(text, path)
    pos = 0

    def peek() -> Optional[Token]:
        return tokens[pos] if pos < len(tokens) else None

    def parse_block(depth: int, open_line: int) -> Block:
        nonlocal pos
        block = Block(line=open_line)
        while True:
            token = peek()
            if token is None:
                if depth > 0:
                    raise ParseError(
                        f"unclosed '{{' (opened on line {open_line}) — brace never closed",
                        open_line,
                        path,
                    )
                return block
            if token.kind == "}":
                if depth == 0:
                    raise ParseError("unexpected '}' with no matching '{'", token.line, path)
                pos += 1
                return block
            block.children.append(parse_node(depth))

    def parse_node(depth: int) -> Node:
        nonlocal pos
        token = tokens[pos]

        if token.kind == "{":
            pos += 1
            return Node(None, None, parse_block(depth + 1, token.line), token.line)

        if token.kind == "op":
            raise ParseError(f"operator '{token.text}' with no left-hand key", token.line, path)

        # token is a word or string: either a bare list item or a key
        key = token.text
        pos += 1
        nxt = peek()

        if nxt is None or nxt.kind != "op":
            return Node(None, None, key, token.line)

        op = nxt.text
        pos += 1
        val_token = peek()
        if val_token is None:
            raise ParseError(f"'{key} {op}' has no value", token.line, path)

        if val_token.kind == "{":
            pos += 1
            return Node(key, op, parse_block(depth + 1, val_token.line), token.line)
        if val_token.kind == "}":
            raise ParseError(f"'{key} {op}' has no value before '}}'", val_token.line, path)
        if val_token.kind == "op":
            raise ParseError(
                f"'{key} {op}' is followed by another operator '{val_token.text}'",
                val_token.line,
                path,
            )
        pos += 1
        return Node(key, op, val_token.text, token.line)

    return parse_block(0, 1)


def parse_file(path: str) -> Block:
    with open(path, "r", encoding="utf-8-sig") as handle:
        return parse(handle.read(), path)


# --------------------------------------------------------------------------- #
# traversal helpers
# --------------------------------------------------------------------------- #


def walk(block: Block, _trail: Sequence[str] = ()) -> Iterator[Tuple[Tuple[str, ...], Node]]:
    """Yield every node in the tree with the chain of keys leading to it."""
    for child in block.children:
        trail = tuple(_trail) + ((child.key,) if child.key else ("<list>",))
        yield trail, child
        if isinstance(child.value, Block):
            yield from walk(child.value, trail)


def find_all(block: Block, key: str) -> Iterator[Node]:
    """Yield every node with the given key, at any depth."""
    for _trail, node in walk(block):
        if node.key == key:
            yield node
