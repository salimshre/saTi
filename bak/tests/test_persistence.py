import json

from core.persistence import load_json_file, save_json_file


def test_save_json_file_creates_backup_when_file_exists(tmp_path):
    target = tmp_path / "data.json"
    target.write_text(json.dumps({"old": True}), encoding="utf-8")

    save_json_file(str(target), {"new": True}, "data")

    backup = tmp_path / "data.json.bak"
    assert backup.exists()
    assert json.loads(backup.read_text(encoding="utf-8")) == {"old": True}
    assert json.loads(target.read_text(encoding="utf-8")) == {"new": True}


def test_load_json_file_returns_default_on_corrupt_json(tmp_path):
    target = tmp_path / "broken.json"
    target.write_text("{broken", encoding="utf-8")

    result = load_json_file(str(target), {"fallback": True}, "broken")

    assert result == {"fallback": True}
