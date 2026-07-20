import re
from dataclasses import dataclass
import tree_sitter_html as tshtml
import tree_sitter_css as tscss
import tree_sitter_javascript as tsjs
from tree_sitter import Language, Parser

from workspace_context import get_workspace

_CSS = Language(tscss.language())
_HTML = Language(tshtml.language())
_JS = Language(tsjs.language())


@dataclass
class Chunk:
    file: str
    type: str          # node type, e.g. "rule_set", "element", "function_declaration"
    text: str
    start_line: int
    end_line: int
    summary: str = ""      # filled in by Layer 4 enrichment


def _walk(node):
    yield node
    for child in node.children:
        yield from _walk(child)


def _make_chunk(file: str, node, source: bytes) -> Chunk:
    return Chunk(
        file=file,
        type=node.type,
        text=source[node.start_byte:node.end_byte].decode("utf-8", errors="ignore"),
        start_line=node.start_point[0] + 1,
        end_line=node.end_point[0] + 1,
    )


def _merge(chunks: list[Chunk]) -> Chunk:
    return Chunk(
        file=chunks[0].file,
        type="group",
        text="\n\n".join(c.text for c in chunks),
        start_line=chunks[0].start_line,
        end_line=chunks[-1].end_line,
    )


def _tag_name(element, source: bytes) -> str:
    for child in element.children:
        if child.type == "start_tag":
            for sub in child.children:
                if sub.type == "tag_name":
                    return source[sub.start_byte:sub.end_byte].decode()
    return ""


def _chunk_css(source: bytes, file: str) -> list[Chunk]:
    tree = Parser(_CSS).parse(source)
    return [_make_chunk(file, n, source)
            for n in tree.root_node.children if n.type == "rule_set"]


_SELECTOR_RE = re.compile(r"^\s*([.#]?[\w-]+)")


def _base_selector(text: str) -> str:
    m = _SELECTOR_RE.match(text)
    return m.group(1) if m else ""


def _group_css(chunks: list[Chunk]) -> list[Chunk]:
    # merge consecutive rule_sets sharing a base selector into one component
    # chunk, e.g. .navbar / .navbar.scrolled / .navbar a -> "navbar" chunk
    grouped = []
    i = 0
    while i < len(chunks):
        base = _base_selector(chunks[i].text)
        j = i + 1
        while j < len(chunks) and base and _base_selector(chunks[j].text) == base:
            j += 1
        group = chunks[i:j]
        grouped.append(_merge(group) if len(group) > 1 else group[0])
        i = j
    return grouped


def _chunk_js(source: bytes, file: str) -> list[Chunk]:
    # landing-page JS is mostly top-level statements (const decls, event listeners),
    # not named functions — so one chunk per top-level statement
    tree = Parser(_JS).parse(source)
    return [_make_chunk(file, n, source)
            for n in tree.root_node.children if n.is_named and n.type != "comment"]


_DECL_RE = re.compile(r"^\s*(?:const|let|var)\s+([A-Za-z_$][\w$]*)")


def _declared_name(text: str) -> str:
    m = _DECL_RE.match(text)
    return m.group(1) if m else ""


def _group_js(chunks: list[Chunk]) -> list[Chunk]:
    # merge a declaration with the immediately-following statements that
    # reference it by name, e.g. `const navbar = ...` + its scroll listener
    grouped = []
    i = 0
    while i < len(chunks):
        name = _declared_name(chunks[i].text)
        j = i + 1
        while j < len(chunks) and name and re.search(rf"\b{re.escape(name)}\b", chunks[j].text):
            j += 1
        group = chunks[i:j]
        grouped.append(_merge(group) if len(group) > 1 else group[0])
        i = j
    return grouped


def _chunk_html(source: bytes, file: str) -> list[Chunk]:
    # one chunk per top-level section: the direct element children of <body>
    tree = Parser(_HTML).parse(source)
    chunks = []
    for node in _walk(tree.root_node):
        if node.type == "element" and _tag_name(node, source) == "body":
            chunks = [_make_chunk(file, c, source)
                      for c in node.children if c.type == "element"]
            break
    return chunks


def chunk_file(path: str) -> list[Chunk]:
    file = get_workspace() / path
    if not file.exists():
        return []
    source = file.read_bytes()
    ext = file.suffix.lower()
    if ext == ".css":
        return _group_css(_chunk_css(source, path))
    if ext == ".js":
        return _group_js(_chunk_js(source, path))
    if ext in (".html", ".htm"):
        return _chunk_html(source, path)
    return []
