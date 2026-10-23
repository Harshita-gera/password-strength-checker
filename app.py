"""
password_checker/app.py
-----------------------
Flask backend for the Password Strength Checker.

Scoring algorithm (max 100 pts):
  Length band  ≥8 chars  → +10  pts
               ≥12 chars → +20  pts  (cumulative, replaces the 8-char bonus)
               ≥16 chars → +30  pts  (cumulative, replaces the 12-char bonus)
  Character variety (each category present adds points):
               Lowercase letters → +15 pts
               Uppercase letters → +15 pts
               Digits            → +20 pts
               Special chars     → +20 pts

  Total max = 30 (length) + 15 + 15 + 20 + 20 = 100

Strength labels:
  0–39   → Weak
  40–69  → Fair
  70–89  → Strong
  90–100 → Very Strong

NO passwords are stored, logged, or transmitted externally.
The /check endpoint accepts a POST request with JSON body {"password": "..."}
and returns a JSON response. The password never leaves this process.
"""

import re
from flask import Flask, render_template, request, jsonify, abort

app = Flask(__name__)


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def _score_password(password: str) -> dict:
    """
    Analyse *password* and return a dict with:
      score        (int 0-100)
      label        (str)
      suggestions  (list[str])
      breakdown    (dict)  – per-criterion scores, for transparency
    """
    if not isinstance(password, str):
        raise TypeError("password must be a string")

    length = len(password)

    has_lower   = bool(re.search(r"[a-z]", password))
    has_upper   = bool(re.search(r"[A-Z]", password))
    has_digit   = bool(re.search(r"\d",    password))
    has_special = bool(re.search(r"[^a-zA-Z0-9]", password))

    # Length score (cumulative band)
    if length >= 16:
        length_score = 30
    elif length >= 12:
        length_score = 20
    elif length >= 8:
        length_score = 10
    else:
        length_score = 0

    lower_score   = 15 if has_lower   else 0
    upper_score   = 15 if has_upper   else 0
    digit_score   = 20 if has_digit   else 0
    special_score = 20 if has_special else 0

    score = length_score + lower_score + upper_score + digit_score + special_score

    # Label
    if score >= 90:
        label = "Very Strong"
    elif score >= 70:
        label = "Strong"
    elif score >= 40:
        label = "Fair"
    else:
        label = "Weak"

    # Improvement suggestions (only shown when the criterion is missing)
    suggestions = []
    if length < 8:
        suggestions.append("Use at least 8 characters.")
    elif length < 12:
        suggestions.append("Consider using 12 or more characters for a stronger password.")
    elif length < 16:
        suggestions.append("16+ characters gives maximum length points.")

    if not has_lower:
        suggestions.append("Add lowercase letters (a–z).")
    if not has_upper:
        suggestions.append("Add uppercase letters (A–Z).")
    if not has_digit:
        suggestions.append("Include at least one digit (0–9).")
    if not has_special:
        suggestions.append("Include at least one special character (e.g. !@#$%^&*).")

    return {
        "score": score,
        "label": label,
        "suggestions": suggestions,
        "breakdown": {
            "length_score":   length_score,
            "lowercase":      lower_score,
            "uppercase":      upper_score,
            "digits":         digit_score,
            "special_chars":  special_score,
        },
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    """Serve the single-page UI."""
    return render_template("index.html")


@app.route("/check", methods=["POST"])
def check():
    """
    POST /check
    Body:  {"password": "<string>"}
    Returns JSON result from _score_password().
    The password is used only in-memory and is never logged.
    """
    data = request.get_json(silent=True)
    if not data or "password" not in data:
        abort(400, description="Request body must be JSON with a 'password' key.")

    password = data["password"]
    if not isinstance(password, str):
        abort(400, description="'password' must be a string.")

    result = _score_password(password)
    return jsonify(result)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # debug=True is fine for local development; never use in production.
    app.run(debug=True, port=5000)
