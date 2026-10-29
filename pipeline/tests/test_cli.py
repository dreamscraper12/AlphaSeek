import os

from portfolio.cli import _load_env_file


def test_loads_values_and_skips_comments_and_blanks(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("# a comment\n\nFOO=bar\nnot-a-pair\n", encoding="utf-8")
    monkeypatch.delenv("FOO", raising=False)

    _load_env_file(env)

    assert os.environ["FOO"] == "bar"


def test_a_real_environment_variable_is_not_overridden(tmp_path, monkeypatch):
    # CI passes the key as a real env var; a stale .env must never shadow it.
    env = tmp_path / ".env"
    env.write_text("TWELVE_DATA_API_KEY=from-the-file\n", encoding="utf-8")
    monkeypatch.setenv("TWELVE_DATA_API_KEY", "from-the-environment")

    _load_env_file(env)

    assert os.environ["TWELVE_DATA_API_KEY"] == "from-the-environment"


def test_missing_file_is_not_an_error(tmp_path):
    _load_env_file(tmp_path / "does-not-exist")
