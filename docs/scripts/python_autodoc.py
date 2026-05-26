#!/usr/bin/env python3
"""Expand mkdocstrings-style ::: autodoc blocks in Markdown using reptor source."""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from contextlib import suppress
from pathlib import Path
from typing import Any

import yaml
from griffe import Docstring, GriffeLoader, Object, parse_auto, parse_google

ROOT = Path(__file__).resolve().parents[1]
CACHE_DIR = ROOT / "docs" / ".vitepress" / "cache" / "python-autodoc"
# Bump when expansion output format changes (invalidates cached markdown).
CACHE_VERSION = "1"

AUTODOC_BLOCK_RE = re.compile(
    r"^::: ([^\n]+)\n((?:[ \t].*\n?)*)",
    re.MULTILINE,
)

LOADER = GriffeLoader()

DEFAULT_OPTIONS: dict[str, Any] = {
    "docstring_section_style": "list",
    "heading_level": 2,
    "separate_signature": True,
}

SECTION_TITLES: dict[str, str] = {
    "attributes": "Attributes",
    "functions": "Methods",
    "methods": "Methods",
    "parameters": "Parameters",
    "other_parameters": "Other Parameters",
    "returns": "Returns",
    "raises": "Raises",
    "yields": "Yields",
    "receives": "Receives",
    "warns": "Warns",
    "examples": "Example",
}

DOCSTRING_MEMBER_SECTIONS = frozenset({"attributes", "functions", "methods"})

# reptor docstrings often omit return types in prose; silence Griffe parse warnings.
PARSE_GOOGLE_OPTIONS = {
    "warnings": False,
    "warn_missing_types": False,
    "warn_unknown_params": False,
}
PARSE_AUTO_OPTIONS = {
    "per_style_options": {
        "google": PARSE_GOOGLE_OPTIONS,
        "numpy": {"warnings": False},
        "sphinx": {"warnings": False},
    },
}


def parse_options(raw: str) -> dict[str, Any]:
    if not raw.strip():
        return dict(DEFAULT_OPTIONS)
    lines = raw.splitlines()
    indents = [len(line) - len(line.lstrip()) for line in lines if line.strip()]
    if not indents:
        return dict(DEFAULT_OPTIONS)
    strip = min(indents)
    dedented = "\n".join(line[strip:] if line.strip() else line for line in lines)
    data = yaml.safe_load(dedented) or {}
    if isinstance(data, dict) and "options" in data:
        options = data["options"] or {}
    elif isinstance(data, dict):
        options = data
    else:
        options = {}
    merged = dict(DEFAULT_OPTIONS)
    merged.update(options)
    return merged


def annotation_str(annotation: Any) -> str:
    if annotation is None:
        return ""
    text = str(annotation).replace("typing.", "")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def format_signature(func: Object) -> str:
    params = []
    for param in func.parameters:
        if param.name in {"self", "cls"}:
            continue
        part = param.name
        ann = annotation_str(param.annotation)
        if ann:
            part += f": {ann}"
        if param.default is not None and str(param.default) not in ("", "''"):
            part += f" = {param.default}"
        params.append(part)
    ret = annotation_str(func.returns) if hasattr(func, "returns") else ""
    sig = f"({', '.join(params)})"
    if ret:
        sig += f" -> {ret}"
    return sig


def parse_docstring(obj: Object) -> list[Any]:
    if not obj.docstring:
        return []
    doc = Docstring(obj.docstring.value, lineno=obj.lineno)
    with suppress(AttributeError, TypeError):
        doc.parent = obj  # type: ignore[attr-defined]
    try:
        return list(parse_google(doc, **PARSE_GOOGLE_OPTIONS))
    except Exception:
        return list(parse_auto(doc, **PARSE_AUTO_OPTIONS))


def section_title(section: Any) -> str:
    if section.title:
        return str(section.title).rstrip(":")
    return SECTION_TITLES.get(section.kind.value, section.kind.value.replace("_", " ").title())


def is_method_entry(name: str, type_annotation: str) -> bool:
    return bool(type_annotation and "(" in type_annotation and name in type_annotation.split("(")[0])


def format_default(default: Any) -> str:
    text = annotation_str(default)
    if text in {'""', "''"}:
        return "''"
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'":
        return text
    return text


def render_list_item(
    name: str,
    type_annotation: str,
    description: str,
    *,
    default: Any | None = None,
) -> str:
    name = name.strip()
    type_annotation = annotation_str(type_annotation)
    description = description.strip()
    if is_method_entry(name, type_annotation):
        line = f"- **`{name}`**"
    else:
        type_parts: list[str] = []
        if type_annotation:
            type_parts.append(f"`{type_annotation}`")
        if default is not None:
            type_parts.append(f"default: `{format_default(default)}`")
        if type_parts:
            line = f"- **`{name}`** ({', '.join(type_parts)})"
        else:
            line = f"- **`{name}`**"
    if description:
        line += f" – {description}"
    return line


def render_docstring_list_section(section: Any) -> list[str]:
    lines = [f"**{section_title(section)}:**", ""]
    for item in section.value:
        name = getattr(item, "name", None) or ""
        type_annotation = getattr(item, "annotation", None) or ""
        description = getattr(item, "description", None) or ""
        default = getattr(item, "default", None)
        lines.append(
            render_list_item(
                name,
                type_annotation,
                description,
                default=default,
            )
        )
    lines.append("")
    return lines


def render_text_section(section: Any) -> list[str]:
    text = str(section.value).strip()
    if not text:
        return []
    return [text, ""]


def render_returns_section(section: Any) -> list[str]:
    lines = [f"**{section_title(section)}:**", ""]
    for item in section.value:
        description = getattr(item, "description", None) or ""
        type_annotation = getattr(item, "annotation", None) or ""
        name = getattr(item, "name", None) or ""
        if name:
            lines.append(render_list_item(name, type_annotation, description))
        elif description:
            lines.append(description.strip())
    lines.append("")
    return lines


def render_examples_section(section: Any) -> list[str]:
    lines = [f"**{section_title(section)}:**", ""]
    for item in section.value:
        if hasattr(item, "value"):
            code = str(item.value).strip()
        else:
            code = str(item).strip()
        if not code:
            continue
        if code.startswith("```"):
            lines.append(code)
        else:
            lines.append("```python")
            lines.append(code)
            lines.append("```")
        lines.append("")
    return lines


def render_admonition_section(section: Any) -> list[str]:
    # Example blocks are often parsed as admonitions in Google-style docstrings.
    if section.kind.value != "admonition":
        return []
    admonition = section.value
    title = getattr(admonition, "title", None) or section_title(section)
    description = getattr(admonition, "description", None) or ""
    lines = [f"**{str(title).rstrip(':')}:**", ""]
    if description.strip().startswith("```"):
        lines.append(description.strip())
    else:
        lines.append("```python")
        lines.append(description.strip())
        lines.append("```")
    lines.append("")
    return lines


def render_docstring_sections(sections: list[Any]) -> list[str]:
    lines: list[str] = []
    for section in sections:
        kind = section.kind.value
        if kind == "text":
            lines.extend(render_text_section(section))
        elif kind in DOCSTRING_MEMBER_SECTIONS:
            lines.extend(render_docstring_list_section(section))
        elif kind == "parameters":
            lines.extend(render_docstring_list_section(section))
        elif kind == "returns":
            lines.extend(render_returns_section(section))
        elif kind == "examples":
            lines.extend(render_examples_section(section))
        elif kind == "admonition":
            lines.extend(render_admonition_section(section))
        elif kind in {"raises", "warns", "yields", "receives", "other_parameters"}:
            lines.extend(render_docstring_list_section(section))
    return lines


def documented_names_from_sections(sections: list[Any]) -> tuple[set[str], set[str]]:
    attributes: set[str] = set()
    methods: set[str] = set()
    for section in sections:
        if section.kind.value == "attributes":
            attributes.update(getattr(item, "name", "") for item in section.value)
        elif section.kind.value in {"functions", "methods"}:
            methods.update(getattr(item, "name", "") for item in section.value)
    return attributes, methods


def uses_docstring_member_sections(sections: list[Any]) -> bool:
    return any(section.kind.value in DOCSTRING_MEMBER_SECTIONS for section in sections)


def extra_attribute_members(
    obj: Object, documented: set[str], options: dict[str, Any]
) -> list[Object]:
    members = [
        m
        for m in obj.members.values()
        if m.is_public
        and not m.name.startswith("_")
        and m.kind.name
        in {
            "ATTRIBUTE",
            "INSTANCE_ATTRIBUTE",
            "CLASS_VARIABLE",
            "TYPE_ALIAS",
        }
    ]
    if options.get("members_order") == "source":
        members.sort(key=lambda m: m.lineno or 0)
    else:
        members.sort(key=lambda m: m.name)
    return [m for m in members if m.name not in documented]


def render_extra_attributes(members: list[Object]) -> list[str]:
    if not members:
        return []
    lines = ["**Attributes:**", ""]
    for member in members:
        ann = annotation_str(getattr(member, "annotation", None))
        desc = member.docstring.value.strip() if member.docstring else ""
        lines.append(render_list_item(member.name, ann, desc))
    lines.append("")
    return lines


def render_heading(identifier: str, obj: Object, options: dict[str, Any]) -> list[str]:
    level = int(options.get("heading_level", 2))
    prefix = "#" * level
    anchor = obj.path
    return [f"{prefix} `{identifier}` {{#{anchor}}}", ""]


def render_class_from_docstring(
    obj: Object, identifier: str, options: dict[str, Any]
) -> str:
    sections = parse_docstring(obj)
    lines = render_heading(identifier, obj, options)
    lines.extend(render_docstring_sections(sections))

    documented_attrs, _ = documented_names_from_sections(sections)
    lines.extend(
        render_extra_attributes(extra_attribute_members(obj, documented_attrs, options))
    )

    if options.get("show_source") and obj.source:
        lines.extend(["**Source**", "", "```python", obj.source.strip(), "```", ""])

    return "\n".join(lines).rstrip() + "\n"


def render_member_docstring(member: Object, options: dict[str, Any]) -> list[str]:
    sections = parse_docstring(member)
    if not sections and member.docstring:
        return [member.docstring.value.strip(), ""]
    return render_docstring_sections(sections)


def render_class_from_members(
    obj: Object, identifier: str, options: dict[str, Any]
) -> str:
    lines = render_heading(identifier, obj, options)

    class_sections = parse_docstring(obj)
    class_sections = [
        s for s in class_sections if s.kind.value not in DOCSTRING_MEMBER_SECTIONS
    ]
    lines.extend(render_docstring_sections(class_sections))

    members = [
        m
        for m in obj.members.values()
        if m.is_public and not m.name.startswith("_")
    ]
    if options.get("members_order") == "source":
        members.sort(key=lambda m: m.lineno or 0)
    else:
        members.sort(key=lambda m: m.name)

    for member in members:
        if member.kind.name in {"FUNCTION", "METHOD"}:
            lines.append(f"### `{member.name}`")
            lines.append("")
            if options.get("separate_signature", True):
                lines.append("```python")
                lines.append(f"def {member.name}{format_signature(member)}")
                lines.append("```")
                lines.append("")
            lines.extend(render_member_docstring(member, options))
        elif member.kind.name in {
            "ATTRIBUTE",
            "INSTANCE_ATTRIBUTE",
            "CLASS_VARIABLE",
            "TYPE_ALIAS",
        }:
            lines.append(f"### `{member.name}`")
            lines.append("")
            ann = annotation_str(getattr(member, "annotation", None))
            if ann:
                lines.append(f"Type: `{ann}`")
                lines.append("")
            if member.docstring:
                lines.append(member.docstring.value.strip())
                lines.append("")
        elif member.kind.name == "CLASS":
            lines.append(f"### `{member.name}`")
            lines.append("")
            if member.docstring:
                lines.append(member.docstring.value.strip())
                lines.append("")

    if options.get("show_source") and obj.source:
        lines.extend(["### Source", "", "```python", obj.source.strip(), "```", ""])

    return "\n".join(lines).rstrip() + "\n"


def render_class(obj: Object, identifier: str, options: dict[str, Any]) -> str:
    sections = parse_docstring(obj)
    if uses_docstring_member_sections(sections):
        return render_class_from_docstring(obj, identifier, options)
    return render_class_from_members(obj, identifier, options)


def render_function(obj: Object, identifier: str, options: dict[str, Any]) -> str:
    lines = render_heading(identifier, obj, options)
    if options.get("separate_signature", True):
        lines.append("```python")
        lines.append(f"def {obj.name}{format_signature(obj)}")
        lines.append("```")
        lines.append("")
    lines.extend(render_member_docstring(obj, options))
    if options.get("show_source") and obj.source:
        lines.extend(["### Source", "", "```python", obj.source.strip(), "```", ""])
    return "\n".join(lines).rstrip() + "\n"


def render_object(identifier: str, options: dict[str, Any]) -> str:
    module_path, _, name = identifier.rpartition(".")
    module = LOADER.load(module_path)
    obj = module[name]
    if obj.kind.name == "CLASS":
        return render_class(obj, identifier, options)
    if obj.kind.name in {"FUNCTION", "METHOD"}:
        return render_function(obj, identifier, options)
    if obj.kind.name == "MODULE":
        lines = render_heading(identifier, obj, options)
        if obj.docstring:
            lines.extend(render_docstring_sections(parse_docstring(obj)))
        return "\n".join(lines).rstrip() + "\n"
    raise ValueError(f"Unsupported object kind for {identifier}: {obj.kind}")


def expand_autodoc_blocks(markdown: str) -> str:
    def replace(match: re.Match[str]) -> str:
        identifier = match.group(1).strip()
        options = parse_options(match.group(2))
        return render_object(identifier, options) + "\n"

    return AUTODOC_BLOCK_RE.sub(replace, markdown)


def expand_with_cache(markdown: str, *, use_cache: bool) -> str:
    if not use_cache:
        return expand_autodoc_blocks(markdown)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha256(f"{CACHE_VERSION}\n{markdown}".encode()).hexdigest()
    cache_file = CACHE_DIR / f"{key}.md"
    if cache_file.exists():
        return cache_file.read_text(encoding="utf-8")
    expanded = expand_autodoc_blocks(markdown)
    cache_file.write_text(expanded, encoding="utf-8")
    return expanded


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=("expand", "check"),
        help="expand: read markdown from stdin and write expanded markdown to stdout; "
        "check: verify all autodoc blocks expand without error",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable expansion cache (default: cache enabled for expand)",
    )
    parser.add_argument(
        "--file",
        type=Path,
        help="For check: expand this file instead of stdin",
    )
    args = parser.parse_args()

    if args.command == "expand":
        source = sys.stdin.read()
        if not AUTODOC_BLOCK_RE.search(source):
            sys.stdout.write(source)
            return 0
        try:
            result = expand_with_cache(source, use_cache=not args.no_cache)
        except Exception as exc:
            print(f"python_autodoc: {exc}", file=sys.stderr)
            return 1
        sys.stdout.write(result)
        return 0

    path = args.file
    if path is None:
        print("check requires --file", file=sys.stderr)
        return 2
    source = path.read_text(encoding="utf-8")
    if not AUTODOC_BLOCK_RE.search(source):
        return 0
    try:
        expand_autodoc_blocks(source)
    except Exception as exc:
        print(f"{path}: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
