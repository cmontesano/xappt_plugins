import os
import re

from collections import namedtuple
from typing import Generator, List, Optional

TEMPLATES_ROOT = os.path.dirname(__file__)
TEXT_TYPES = (".py", ".sh", ".bat", ".txt", ".cfg", ".godot", ".tres", ".gd", ".tscn", ".material", ".shader",
              ".cpp", ".h", ".hpp", ".gdnlib", ".gdns")
TEXT_FILES = ("SConstruct", )

DEFAULT_PERMISSION = 0o0664  # rw-rw-r--

TemplateEntry = namedtuple("TemplateEntry", ["source", "target", "text_mode", "permissions"])
NameDecomposition = namedtuple("NameDecomposition", ["name", "tag_dict"])

# tags are encoded at the head of the file name in the form of [TYPE-VALUE]
TAG_RE = re.compile(r"^\[(?P<type>[a-z0-9_]+)-(?P<value>.*?)](?P<name>.*)$", re.I)
TAG_TYPES = {
    "alt": {
        "label": "alternative",
    },
    "perm": {
        "label": "permissions",
        "convert": lambda x: int(x, 8),
    },
}


def get_templates(category: str) -> List[str]:
    category_path = os.path.join(TEMPLATES_ROOT, category)
    return [item.name for item in os.scandir(category_path) if item.is_dir() and item.name[0] != "."]


def get_file_tags(file_name: str) -> NameDecomposition:
    name = file_name
    tag_dict = {}
    while name.startswith("["):
        match = TAG_RE.match(name)
        if match is None:
            break
        tag_type = match.group("type").lower()
        tag_value = match.group("value")
        name = match.group("name")
        if tag_type in TAG_TYPES:
            key = TAG_TYPES[tag_type].get("label", tag_type)
            convert_fn = TAG_TYPES[tag_type].get("convert")
            if convert_fn is not None:
                # noinspection PyCallingNonCallable
                tag_value = convert_fn(tag_value)
        else:
            key = tag_type
        tag_dict[key] = tag_value
    return NameDecomposition(name=name, tag_dict=tag_dict)


def get_template_files(category: str, template: str, alternative: Optional[str] = None) \
        -> Generator[TemplateEntry, None, None]:
    template_path = os.path.join(TEMPLATES_ROOT, category, template)
    for root, dirs, files in os.walk(template_path):
        for f in files:
            template_file = get_file_tags(f)

            # skip alternatives by default
            if "alternative" in template_file.tag_dict:
                continue

            source_path = os.path.join(root, f)
            ext = os.path.splitext(f)[1].lower()
            if alternative is not None:
                # look for an alternative
                alt_file = os.path.join(root, f"[ALT-{alternative.upper()}]{f}")
                if os.path.isfile(alt_file):
                    source_path = alt_file
            target_path = os.path.join(root, template_file.name)

            permissions = template_file.tag_dict.get("permissions", DEFAULT_PERMISSION)

            text_mode = ext in TEXT_TYPES or f in TEXT_FILES

            yield TemplateEntry(source=source_path, target=os.path.relpath(target_path, template_path),
                                text_mode=text_mode, permissions=permissions)


if __name__ == '__main__':
    v = get_file_tags("[perm-775][alt-other]test.txt")
    assert v.tag_dict['permissions'] == 509
    assert v.tag_dict['alternative'] == 'other'
    assert v.name == "test.txt"
