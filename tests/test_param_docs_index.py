"""docs/params must stay consistent with the registry and the generator index.

The block docs are generated from ``configs/block_purpose_zh.json`` and grouped
by ``_GROUPS`` in ``scripts/export_param_docs.py``. Nothing re-ran the generator
in CI, so the committed output drifted: the index advertised 86 blocks while 87
documents existed, and ``rfd4_search`` had a page but no purpose text, no group
row, and no index entry. These checks are cheap and catch that class of drift
without importing every block.
"""

from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
DOCS = REPO / "docs" / "params"
INDEX = DOCS / "README.md"


def _group_rows() -> list[str]:
    """Names listed in the generator's ``_GROUPS``, in index order."""
    spec = importlib.util.spec_from_file_location(
        "export_param_docs", REPO / "scripts" / "export_param_docs.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return [name for _title, names in module._GROUPS for name in names]


def _block_pages() -> list[str]:
    return sorted(p.stem for p in DOCS.glob("*.md") if p.name != "README.md")


def test_every_grouped_block_has_a_page():
    """``_GROUPS`` may omit blocks (they fall under 其他) but never invent them."""
    pages = set(_block_pages())
    grouped = set(_group_rows())
    assert grouped - pages == set(), "_GROUPS names without a documentation page"


def test_pages_match_the_block_registry():
    from blocks import Blocks

    assert set(_block_pages()) == set(Blocks.keys())


def test_index_count_matches_pages():
    stated = re.search(r"^(\d+) 个 block", INDEX.read_text(), re.MULTILINE)
    assert stated, "index lost its block count line"
    assert int(stated.group(1)) == len(_block_pages())


def test_index_links_every_page():
    text = INDEX.read_text()
    missing = [name for name in _block_pages() if f"({name}.md)" not in text]
    assert not missing, f"pages not linked from the index: {missing}"


def test_every_page_has_purpose_text():
    """A page without the purpose section is generated from a missing entry."""
    missing = [
        name
        for name in _block_pages()
        if "## 干什么用的" not in (DOCS / f"{name}.md").read_text()
    ]
    assert not missing, f"pages without 干什么用的: {missing}"


@pytest.mark.parametrize("name", _block_pages())
def test_group_row_comes_from_purpose_data(name):
    """The index blurb is the purpose entry, not a hand-written duplicate."""
    purposes = _purpose_data()
    assert name in purposes, f"{name} has no entry in block_purpose_zh.json"
    assert purposes[name].get("what"), f"{name} purpose entry has no 'what'"


def _purpose_data() -> dict:
    return json.loads((REPO / "configs" / "block_purpose_zh.json").read_text())