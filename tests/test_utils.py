"""Tests for pure utility functions (time parsing and settings I/O)."""
import json
import os
import pytest

from utils import parse_time_input, load_logo_settings, save_logo_settings


# ── parse_time_input ──────────────────────────────────────────────────────────

class TestParseTimeInput:
    def test_mm_ss_format(self):
        assert parse_time_input("45:00") == 45 * 60

    def test_mm_ss_nonzero_seconds(self):
        assert parse_time_input("1:30") == 90

    def test_zero(self):
        assert parse_time_input("0:00") == 0

    def test_large_minutes(self):
        assert parse_time_input("120:00") == 120 * 60

    def test_plain_seconds(self):
        assert parse_time_input("90") == 90

    def test_plain_zero(self):
        assert parse_time_input("0") == 0

    def test_whitespace_stripped(self):
        assert parse_time_input("  45:00  ") == 2700

    def test_invalid_letters_raises(self):
        with pytest.raises(ValueError):
            parse_time_input("abc")

    def test_empty_string_raises(self):
        with pytest.raises(ValueError):
            parse_time_input("")

    def test_too_many_colons_raises(self):
        with pytest.raises(ValueError):
            parse_time_input("1:2:3")

    def test_partial_colon_raises(self):
        with pytest.raises(ValueError):
            parse_time_input("45:")


# ── load_logo_settings ────────────────────────────────────────────────────────

class TestLoadLogoSettings:
    def test_returns_defaults_when_file_missing(self, tmp_path):
        result = load_logo_settings(str(tmp_path / "nonexistent.json"))
        assert result == [None, None]

    def test_loads_saved_paths(self, tmp_path):
        path = tmp_path / "settings.json"
        path.write_text(json.dumps({"logos": ["/a/home.png", "/b/away.png"]}))
        result = load_logo_settings(str(path))
        assert result == ["/a/home.png", "/b/away.png"]

    def test_returns_defaults_on_corrupt_json(self, tmp_path):
        path = tmp_path / "settings.json"
        path.write_text("not valid json{{")
        result = load_logo_settings(str(path))
        assert result == [None, None]

    def test_missing_logos_key_returns_defaults(self, tmp_path):
        path = tmp_path / "settings.json"
        path.write_text(json.dumps({"other": "data"}))
        result = load_logo_settings(str(path))
        assert result == [None, None]


# ── save_logo_settings ────────────────────────────────────────────────────────

class TestSaveLogoSettings:
    def test_saves_and_reloads(self, tmp_path):
        path = str(tmp_path / "settings.json")
        logos = ["/logos/home.png", "/logos/away.png"]
        save_logo_settings(path, logos)
        assert load_logo_settings(path) == logos

    def test_saves_none_values(self, tmp_path):
        path = str(tmp_path / "settings.json")
        save_logo_settings(path, [None, None])
        assert load_logo_settings(path) == [None, None]

    def test_creates_parent_directories(self, tmp_path):
        path = str(tmp_path / "deep" / "nested" / "settings.json")
        save_logo_settings(path, [None, None])
        assert os.path.exists(path)

    def test_overwrites_existing(self, tmp_path):
        path = str(tmp_path / "settings.json")
        save_logo_settings(path, ["/old.png", None])
        save_logo_settings(path, ["/new.png", "/away.png"])
        assert load_logo_settings(path) == ["/new.png", "/away.png"]
