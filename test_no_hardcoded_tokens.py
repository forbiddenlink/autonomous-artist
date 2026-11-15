"""Guard: no Facebook access token literal may be committed in tracked Python files."""
import pathlib
import re

ROOT = pathlib.Path(__file__).parent
PATTERN = re.compile(r"EAA[A-Za-z0-9]{20,}")


def test_no_eaa_literals_in_python_sources():
    offenders = [
        str(p.relative_to(ROOT))
        for p in ROOT.rglob("*.py")
        if not any(part in {"venv", ".venv", "env", ".git"} for part in p.parts)
        and PATTERN.search(p.read_text(errors="ignore"))
    ]
    assert offenders == [], f"EAA-prefixed token literal found in: {offenders}"


def test_token_scripts_fail_loudly_when_env_unset():
    for name in ("fetch_page_token.py", "get_page_token_alternative.py"):
        src = (ROOT / name).read_text()
        assert 'os.environ.get("FB_USER_TOKEN")' in src
        assert "sys.exit(" in src
