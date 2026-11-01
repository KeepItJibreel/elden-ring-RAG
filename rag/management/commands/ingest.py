import ast
import re
from pathlib import Path

import pandas as pd
from django.core.management.base import BaseCommand
from sentence_transformers import SentenceTransformer

from rag.models import Chunk

PLACEHOLDERS = {"", "-", "???", "nan", "None", "['None']"}
DROP_COLUMNS = {
    "id", "image", "weapon_id", "shield_id",
    "name", "weapon name", "shield name", "description",
}
NAME_COLUMNS = ("name", "weapon name", "shield name")


UPGRADE_FILES = {"weapons_upgrades", "shields_upgrades"}
UPGRADABLE_FILES = {"weapons", "shields"}
UPGRADE_LABEL = re.compile(r"^\s*(.*?)\s*(?:\+\s*(\d+))?\s*$")  # "Heavy +12 " -> affinity "Heavy", level 12
UPGRADE_NOTES = {
    "somber": "somber weapon, upgrades to +10 with Somber Smithing Stones, cannot change affinity",
    "standard": "standard weapon, upgrades to +25 with Smithing Stones, can change affinity with an Ash of War",
}


def structure_to_text(data):
    """Turn a parsed list or dict into a short readable string."""
    if isinstance(data, dict):
        # {'Phy': '125 ', 'Mag': '- '} -> "Phy 125"
        parts = []
        for key, val in data.items():
            val = str(val).strip()
            if val not in ("", "-"):
                parts.append(f"{key} {val}")
        return ", ".join(parts)

    parts = []
    for item in data:
        if isinstance(item, dict):
            if item.get("amount") == 0:     # skip 0 values
                continue
            label = item.get("name", "")
            rest = [str(v) for k, v in item.items() if k != "name"]
            parts.append(" ".join([label] + rest).strip())
        else:
            parts.append(str(item))
    return ", ".join(parts)


def cell_to_text(value):
    """Convert one CSV cell to clean text."""
    if pd.isna(value):
        return ""
    raw = str(value).strip()
    if raw in PLACEHOLDERS:
        return ""

    # Some cells hold a dict/list as a string
    if raw.startswith(("[", "{")):
        try:
            parsed = ast.literal_eval(raw)
        except (ValueError, SyntaxError):
            return raw
        return structure_to_text(parsed)

    return raw


def get_name(row):
    """Return the item name, regardless of column name."""
    for column in NAME_COLUMNS:
        name = cell_to_text(row.get(column))
        if name:
            return name
    return "Unknown"


def upgrade_path(top_level):
    """Somber weapons top out at +10, standard ones go up to +25."""
    return "somber" if top_level <= 10 else "standard"


def parse_upgrade(label):
    """'Heavy +12 ' -> ('Heavy', 12)"""
    match = UPGRADE_LABEL.match(str(label))
    return match.group(1), int(match.group(2) or 0)


def find_upgrade_paths(folder):
    """Map item name -> 'somber' or 'standard', from its highest upgrade level."""
    paths = {}
    for stem in UPGRADE_FILES:
        file = folder / f"{stem}.csv"
        if not file.exists():
            continue

        table = pd.read_csv(file)
        name_column = next(c for c in NAME_COLUMNS if c in table.columns)
        levels = table["upgrade"].map(lambda u: parse_upgrade(u)[1])
        names = table[name_column].astype(str).str.strip()
        for item, top in levels.groupby(names).max().items():
            paths[item] = upgrade_path(top)

    return paths


def build_chunk_text(category, row, extra_lines=()):
    """Build the text for one CSV row. Returns (name, text)."""
    name = get_name(row)
    lines = [f"{name} ({category})"]

    for column, value in row.items():
        if column in DROP_COLUMNS:
            continue
        text = cell_to_text(value)
        if text:
            lines.append(f"{column}: {text}")

    lines.extend(extra_lines)

    # Description goes last so any cutoff trims lore, which isn't relevant to build making
    description = cell_to_text(row.get("description"))
    if description:
        lines.append(f"description: {description}")

    return name, "\n".join(lines)


def build_upgrade_chunks(category, table):
    """
    One chunk per (item, affinity), summarizing its lowest and highest
    upgrade level. Returns a list of (name, text).
    """
    name_column = next(c for c in NAME_COLUMNS if c in table.columns)
    parsed = table["upgrade"].map(parse_upgrade)
    table = table.assign(
        affinity=parsed.map(lambda p: p[0]),
        level=parsed.map(lambda p: p[1]),
    )

    results = []
    for (item, affinity), group in table.groupby([name_column, "affinity"], sort=False):
        group = group.sort_values("level")
        rows = [group.iloc[0]] if len(group) == 1 else [group.iloc[0], group.iloc[-1]]

        path = upgrade_path(rows[-1]["level"])
        lines = [
            f"{item} - {affinity} affinity ({category})",
            f"upgrade path: {UPGRADE_NOTES[path]}",
        ]
        for row in rows:
            parts = []
            for label, column in (
                ("attack", "attack power"),
                ("scaling", "stat scaling"),
                ("damage reduction %", "damage reduction (%)"),
            ):
                text = cell_to_text(row[column])
                if text:
                    parts.append(f"{label}: {text}")
            lines.append(f"At +{row['level']}: " + " | ".join(parts))

        passive = cell_to_text(rows[-1]["passive effects"])
        if passive:
            lines.append(f"passive effects: {passive}")

        results.append((f"{item} ({affinity})", "\n".join(lines)))
    return results


class Command(BaseCommand):
    help = "Loads Elden Ring CSVs from a folder into the Chunk table"

    def add_arguments(self, parser):
        parser.add_argument("folder", help="Folder containing the CSV files")

    def handle(self, *_, **options):
        folder = Path(options["folder"])
        csv_files = sorted(folder.glob("*.csv"))
        if not csv_files:
            self.stderr.write(f"No CSVs found in {folder}")
            return

        model = SentenceTransformer("all-MiniLM-L6-v2") # same model as query embeddings in rag.py
        upgrade_paths = find_upgrade_paths(folder)
        Chunk.objects.all().delete()

        total = 0
        for path in csv_files:
            category = path.stem
            table = pd.read_csv(path)

            if category in UPGRADE_FILES:
                rows = build_upgrade_chunks(category, table)
            else:
                rows = []
                for record in table.to_dict("records"):
                    extra = ()
                    if category in UPGRADABLE_FILES:
                        kind = upgrade_paths.get(get_name(record))
                        if kind:
                            extra = (f"upgrade path: {UPGRADE_NOTES[kind]}",)
                    rows.append(build_chunk_text(category, record, extra))

            names = [r[0] for r in rows]
            texts = [r[1] for r in rows]

            vectors = model.encode(texts, normalize_embeddings=True)    # vectorize item's text

            Chunk.objects.bulk_create([
                Chunk(
                    name=n,
                    category=category,
                    source=path.name,
                    text=t,
                    embedding=v.tolist(),
                )
                for n, t, v in zip(names, texts, vectors)
            ])

            total += len(texts)

        self.stdout.write(self.style.SUCCESS(f"{total} chunks stored."))