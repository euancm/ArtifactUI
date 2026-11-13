import argparse
import json
import re
import struct
import warnings
from pathlib import Path


class Reader:
    def __init__(self, path: Path):
        self.data = path.read_bytes()
        self.offset = 0

    def read(self, fmt: str) -> int:
        size = struct.calcsize("<" + fmt)
        if self.offset + size > len(self.data):
            raise ValueError(f"Truncated metadata at offset {self.offset}")
        value = struct.unpack_from("<" + fmt, self.data, self.offset)[0]
        self.offset += size
        return value

    def string(self) -> str:
        count = self.read("i")
        if count == 0:
            return ""
        length = abs(count) * (2 if count < 0 else 1)
        if length > len(self.data) - self.offset:
            raise ValueError(f"Invalid string length at offset {self.offset}")
        data = self.data[self.offset:self.offset + length]
        self.offset += length
        text = data.decode("utf-16-le" if count < 0 else "utf-8")
        if not text.endswith("\0"):
            raise ValueError("Missing string terminator")
        return text[:-1]


def localization_namespaces(path: Path) -> dict[str, set[str]]:
    reader = Reader(path)
    if reader.data[:16].hex() != "0e147475674a03fc4a15909dc3377f1b":
        raise ValueError("Unknown localization resource signature")
    reader.offset = 16
    if reader.read("B") != 3:
        raise ValueError("Only version 3 localization resources are supported")
    strings_offset = reader.read("q")
    expected_count = reader.read("I")
    namespaces: dict[str, set[str]] = {}
    count = 0
    for _ in range(reader.read("I")):
        reader.read("I")
        namespace = reader.string()
        for _ in range(reader.read("I")):
            reader.read("I")
            key = reader.string()
            reader.read("I")
            reader.read("i")
            namespaces.setdefault(key, set()).add(namespace)
            count += 1
    if count != expected_count or reader.offset != strings_offset:
        raise ValueError("Localization key counts or offsets do not match")
    return namespaces


def item_prototypes(path: Path) -> list[dict[str, str]]:
    reader = Reader(path)
    if reader.read("I") != 2:
        raise ValueError("Only version 2 compiled prototype files are supported")
    pool = [reader.string() for _ in range(reader.read("I"))]

    def pool_string() -> str:
        index = reader.read("I")
        if index >= len(pool):
            raise ValueError(f"Invalid prototype string index {index}")
        return pool[index]

    def node() -> tuple[str, str, dict]:
        name, value = pool_string(), pool_string()
        pool_string()
        reference_flags = reader.read("B")
        if reference_flags not in (0, 1, 2, 5):
            raise ValueError(f"Unsupported prototype reference flags {reference_flags}")
        if reference_flags & 1:
            reader.string()
            reader.string()
        children = {}
        for _ in range(reader.read("I")):
            key = pool_string()
            child = node()
            if child[0] != key or key in children:
                raise ValueError(f"Invalid or duplicate prototype field {key}")
            children[key] = child
        return name, value, children

    root = node()
    if reader.offset != len(reader.data):
        raise ValueError("Unparsed prototype data remains")
    return [
        {key: child[1] for key, child in entry[2].items()}
        for entry in root[2].values()
    ]


def build_rows(prototypes: list[dict[str, str]], namespaces: dict[str, set[str]]) -> list[dict[str, str]]:
    rows = {}
    missing = []
    for fields in prototypes:
        if fields.get("Type") != "EItemType::Artifact":
            continue
        sid = fields["SID"]
        if sid.startswith("Template"):
            continue
        blueprint = fields.get("Blueprint", "")
        match = re.fullmatch(r"Blueprint'[^']+\.BP_([^']+)'", blueprint)
        if not match:
            raise ValueError(f"{sid}: unsupported artifact Blueprint path {blueprint!r}")
        class_name = match.group(1)
        localization_sid = fields.get("LocalizationSID") or sid
        name_key = f"sid_items_{localization_sid}_name"
        description_key = f"sid_items_{localization_sid}_description"
        matches = namespaces.get(name_key, set()) & namespaces.get(description_key, set())
        if not matches:
            missing.append(f"{sid}: {localization_sid} (class {class_name})")
            continue
        if len(matches) > 1:
            raise ValueError(f"{sid}: {len(matches)} matching namespaces")
        row = {"Name": class_name, "Namespace": next(iter(matches)), "LocalizationSID": localization_sid}
        key = class_name.casefold()
        if key in rows and rows[key] != row:
            raise ValueError(f"Conflicting artifact class {class_name} for {sid}")
        rows[key] = row
    if missing:
        warnings.warn(
            "Artifacts without complete localized text may share a class with a localized artifact:\n"
            + "\n".join(missing),
            stacklevel=2,
        )
    return sorted(rows.values(), key=lambda row: row["Name"].casefold())


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate artifact aliases without copying game translations.")
    parser.add_argument("--locres", type=Path, required=True)
    parser.add_argument("--prototypes", type=Path, nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    prototypes = [entry for path in args.prototypes for entry in item_prototypes(path)]
    rows = build_rows(prototypes, localization_namespaces(args.locres))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    print(f"Verified {len(rows)} artifact localization mappings.")


if __name__ == "__main__":
    main()
