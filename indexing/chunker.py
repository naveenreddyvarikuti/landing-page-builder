from dataclasses import dataclass
from pathlib import Path
import tree_sitter_html as tshtml
import tree_sitter_css as tscss
import tree_sitter_javascript as tsjs
from tree_sitter import Language, Parser

WORKSPACE = Path(__file__).parent.parent / "workspace"

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


def _chunk_js(source: bytes, file: str) -> list[Chunk]:
    # landing-page JS is mostly top-level statements (const decls, event listeners),
    # not named functions — so one chunk per top-level statement
    tree = Parser(_JS).parse(source)
    return [_make_chunk(file, n, source)
            for n in tree.root_node.children if n.is_named and n.type != "comment"]


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
    file = WORKSPACE / path
    if not file.exists():
        return []
    source = file.read_bytes()
    ext = file.suffix.lower()
    if ext == ".css":
        return _chunk_css(source, path)
    if ext == ".js":
        return _chunk_js(source, path)
    if ext in (".html", ".htm"):
        return _chunk_html(source, path)
    return []
