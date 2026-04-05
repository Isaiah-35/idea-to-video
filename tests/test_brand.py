"""Unit tests for brand.py"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from brand import brand_prefix, save_brand, load_brand, BRAND_FILE


def test_brand_prefix_empty():
    assert brand_prefix({"name": "", "audience": "", "tone": "", "style_notes": ""}) == ""


def test_brand_prefix_name_only():
    prefix = brand_prefix({"name": "TechSimplified", "audience": "", "tone": "", "style_notes": ""})
    assert "TechSimplified" in prefix
    assert "Brand context" in prefix


def test_brand_prefix_full():
    b = {"name": "Acme", "audience": "engineers", "tone": "direct", "style_notes": "no jargon"}
    prefix = brand_prefix(b)
    assert "Acme" in prefix
    assert "engineers" in prefix
    assert "direct" in prefix
    assert "no jargon" in prefix


def test_save_load_brand(tmp_path, monkeypatch):
    test_file = tmp_path / "brand.json"
    monkeypatch.setattr("brand.BRAND_FILE", test_file)

    b = {"name": "Test", "audience": "devs", "tone": "casual", "style_notes": ""}
    save_brand(b)
    assert test_file.exists()
    loaded = load_brand()
    assert loaded["name"] == "Test"
    assert loaded["audience"] == "devs"


def test_load_brand_missing_file(tmp_path, monkeypatch):
    monkeypatch.setattr("brand.BRAND_FILE", tmp_path / "nonexistent.json")
    b = load_brand()
    assert b["name"] == ""
    assert b["audience"] == ""


def test_brand_prefix_none_uses_file(tmp_path, monkeypatch):
    test_file = tmp_path / "brand.json"
    test_file.write_text(json.dumps({"name": "FromFile", "audience": "", "tone": "", "style_notes": ""}))
    monkeypatch.setattr("brand.BRAND_FILE", test_file)
    prefix = brand_prefix(None)
    assert "FromFile" in prefix
