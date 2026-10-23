"""
password_checker/tests/test_app.py
------------------------------------
Automated tests for the Password Strength Checker.

Run from the project root:
    cd password_checker
    python -m pytest tests/ -v

Requirements:
    pip install flask pytest
"""

import sys
import os

# Ensure the parent package (password_checker/) is on sys.path so we can
# import app.py directly regardless of where pytest is invoked from.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from app import app, _score_password


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    """Flask test client with testing mode enabled."""
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


# ---------------------------------------------------------------------------
# Unit tests — _score_password()
# ---------------------------------------------------------------------------

class TestScorePasswordUnit:
    """Direct unit tests of the scoring function."""

    # --- length scoring -------------------------------------------------------

    def test_empty_password_score_zero(self):
        result = _score_password("")
        assert result["score"] == 0
        assert result["label"] == "Weak"

    def test_short_password_no_length_points(self):
        # 7 chars, lowercase only → 0 (length) + 15 (lower) = 15
        result = _score_password("abcdefg")
        assert result["breakdown"]["length_score"] == 0
        assert result["score"] == 15

    def test_8_char_password_gets_10_length_pts(self):
        result = _score_password("abcdefgh")
        assert result["breakdown"]["length_score"] == 10

    def test_12_char_password_gets_20_length_pts(self):
        result = _score_password("a" * 12)
        assert result["breakdown"]["length_score"] == 20

    def test_16_char_password_gets_30_length_pts(self):
        result = _score_password("a" * 16)
        assert result["breakdown"]["length_score"] == 30

    # --- character variety scoring -------------------------------------------

    def test_lowercase_only_adds_15_pts(self):
        result = _score_password("aaaaaaaa")  # 8 chars lowercase
        assert result["breakdown"]["lowercase"] == 15
        assert result["breakdown"]["uppercase"] == 0
        assert result["breakdown"]["digits"] == 0
        assert result["breakdown"]["special_chars"] == 0

    def test_uppercase_only_adds_15_pts(self):
        result = _score_password("AAAAAAAA")
        assert result["breakdown"]["uppercase"] == 15
        assert result["breakdown"]["lowercase"] == 0

    def test_digits_add_20_pts(self):
        result = _score_password("12345678")
        assert result["breakdown"]["digits"] == 20

    def test_special_chars_add_20_pts(self):
        result = _score_password("!@#$%^&*")
        assert result["breakdown"]["special_chars"] == 20

    # --- combined / label tests ----------------------------------------------

    def test_weak_label(self):
        # short + only lowercase → score 15 → Weak
        result = _score_password("abc")
        assert result["label"] == "Weak"

    def test_fair_label(self):
        # 8 chars + lower + upper = 10+15+15 = 40 → Fair
        result = _score_password("Abcdefgh")
        assert result["score"] == 40
        assert result["label"] == "Fair"

    def test_strong_label(self):
        # 12 chars + lower + upper + digit = 20+15+15+20 = 70 → Strong
        result = _score_password("Abcdefgh1234")
        assert result["score"] == 70
        assert result["label"] == "Strong"

    def test_very_strong_label(self):
        # 16 chars + all 4 types = 30+15+15+20+20 = 100 → Very Strong
        result = _score_password("Abcdefgh1234!@#$")
        assert result["score"] == 100
        assert result["label"] == "Very Strong"

    def test_max_score_100(self):
        result = _score_password("Abcdefgh1234!@#$")
        assert result["score"] == 100

    # --- suggestions ---------------------------------------------------------

    def test_suggests_length_when_too_short(self):
        result = _score_password("ab")
        assert any("8 character" in s for s in result["suggestions"])

    def test_suggests_uppercase_when_missing(self):
        result = _score_password("abcdefgh1!")
        assert any("uppercase" in s.lower() for s in result["suggestions"])

    def test_suggests_lowercase_when_missing(self):
        result = _score_password("ABCDEFGH1!")
        assert any("lowercase" in s.lower() for s in result["suggestions"])

    def test_suggests_digit_when_missing(self):
        result = _score_password("Abcdefgh!")
        assert any("digit" in s.lower() for s in result["suggestions"])

    def test_suggests_special_when_missing(self):
        result = _score_password("Abcdefgh1")
        assert any("special" in s.lower() for s in result["suggestions"])

    def test_no_suggestions_for_perfect_password(self):
        result = _score_password("Abcdefgh1234!@#$")
        assert result["suggestions"] == []

    def test_invalid_type_raises_type_error(self):
        with pytest.raises(TypeError):
            _score_password(12345)


# ---------------------------------------------------------------------------
# Integration tests — HTTP endpoints via Flask test client
# ---------------------------------------------------------------------------

class TestCheckEndpoint:
    """HTTP-level tests for POST /check."""

    def test_returns_200_with_valid_payload(self, client):
        resp = client.post("/check", json={"password": "Hello123!"})
        assert resp.status_code == 200

    def test_response_has_required_keys(self, client):
        resp = client.post("/check", json={"password": "Hello123!"})
        data = resp.get_json()
        assert "score"       in data
        assert "label"       in data
        assert "suggestions" in data
        assert "breakdown"   in data

    def test_score_is_integer(self, client):
        resp = client.post("/check", json={"password": "Hello123!"})
        data = resp.get_json()
        assert isinstance(data["score"], int)

    def test_score_in_valid_range(self, client):
        resp = client.post("/check", json={"password": "Hello123!"})
        data = resp.get_json()
        assert 0 <= data["score"] <= 100

    def test_400_when_body_missing_password_key(self, client):
        resp = client.post("/check", json={"typo": "oops"})
        assert resp.status_code == 400

    def test_400_when_body_is_empty(self, client):
        resp = client.post("/check", data="not json", content_type="text/plain")
        assert resp.status_code == 400

    def test_400_when_password_is_not_string(self, client):
        resp = client.post("/check", json={"password": 42})
        assert resp.status_code == 400

    def test_method_not_allowed_on_get(self, client):
        resp = client.get("/check")
        assert resp.status_code == 405

    def test_index_returns_200(self, client):
        resp = client.get("/")
        assert resp.status_code == 200

    def test_index_returns_html(self, client):
        resp = client.get("/")
        assert b"Password Strength Checker" in resp.data

    def test_empty_string_password(self, client):
        resp = client.post("/check", json={"password": ""})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["score"] == 0
        assert data["label"] == "Weak"

    def test_very_strong_password_via_http(self, client):
        resp = client.post("/check", json={"password": "Abcdefgh1234!@#$"})
        data = resp.get_json()
        assert data["score"] == 100
        assert data["label"] == "Very Strong"
