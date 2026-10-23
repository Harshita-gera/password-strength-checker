/**
 * password_checker/static/js/main.js
 * ------------------------------------
 * Handles all client-side interactions:
 *  - Debounced POST to /check as the user types
 *  - Strength meter width + colour update
 *  - Score breakdown table population
 *  - Improvement suggestions rendering
 *  - Show/hide password toggle
 *
 * The password is sent over localhost only; it is never persisted
 * client-side (no localStorage, no cookies, no console.log of the value).
 */

"use strict";

// ── DOM refs ────────────────────────────────────────────────────────────────
const input          = document.getElementById("password-input");
const toggleBtn      = document.getElementById("toggle-visibility");
const eyeIcon        = document.getElementById("eye-icon");
const meterWrap      = document.querySelector(".meter-wrap");
const meterBar       = document.getElementById("meter-bar");
const strengthLabel  = document.getElementById("strength-label");
const scoreDisplay   = document.getElementById("score-display");
const breakdownTable = document.getElementById("breakdown-table");
const bdLength       = document.getElementById("bd-length");
const bdLower        = document.getElementById("bd-lower");
const bdUpper        = document.getElementById("bd-upper");
const bdDigits       = document.getElementById("bd-digits");
const bdSpecial      = document.getElementById("bd-special");
const suggList       = document.getElementById("suggestions-list");

// ── Helpers ──────────────────────────────────────────────────────────────────

/**
 * Map a label string to a CSS class name used on the meter and the label.
 * @param {string} label  e.g. "Very Strong"
 * @returns {string}      e.g. "very-strong"
 */
function labelToClass(label) {
  return label.toLowerCase().replace(/\s+/g, "-");
}

/** Remove all strength colour classes from an element. */
function clearColorClasses(el) {
  el.classList.remove("weak", "fair", "strong", "very-strong");
}

/**
 * Update a breakdown <td> with earned/not-earned styling.
 * @param {HTMLElement} td
 * @param {number}      pts  Points for this criterion.
 */
function setBreakdownCell(td, pts) {
  td.textContent = pts;
  td.className = pts > 0 ? "earned" : "not-earned";
}

// ── Reset UI to blank state ───────────────────────────────────────────────────
function resetUI() {
  meterBar.style.width = "0%";
  clearColorClasses(meterBar);

  strengthLabel.textContent = "—";
  clearColorClasses(strengthLabel);

  scoreDisplay.textContent = "";
  breakdownTable.hidden = true;
  suggList.innerHTML = "";

  // ARIA
  meterWrap.setAttribute("aria-valuenow", "0");
}

// ── Apply API response to the UI ─────────────────────────────────────────────
/**
 * @param {{ score: number, label: string, suggestions: string[], breakdown: object }} data
 */
function applyResult(data) {
  const { score, label, suggestions, breakdown } = data;
  const cls = labelToClass(label);

  // Meter
  meterBar.style.width = `${score}%`;
  clearColorClasses(meterBar);
  meterBar.classList.add(cls);
  meterWrap.setAttribute("aria-valuenow", score);

  // Label + score
  strengthLabel.textContent = label;
  clearColorClasses(strengthLabel);
  strengthLabel.classList.add(cls);
  scoreDisplay.textContent = `${score} / 100 pts`;

  // Breakdown table
  setBreakdownCell(bdLength,  breakdown.length_score);
  setBreakdownCell(bdLower,   breakdown.lowercase);
  setBreakdownCell(bdUpper,   breakdown.uppercase);
  setBreakdownCell(bdDigits,  breakdown.digits);
  setBreakdownCell(bdSpecial, breakdown.special_chars);
  breakdownTable.hidden = false;

  // Suggestions
  suggList.innerHTML = "";
  suggestions.forEach((text) => {
    const li = document.createElement("li");
    li.textContent = text;
    suggList.appendChild(li);
  });
}

// ── Debounce helper ───────────────────────────────────────────────────────────
/**
 * Returns a debounced version of `fn` that fires after `delayMs` of silence.
 * @param {Function} fn
 * @param {number}   delayMs
 */
function debounce(fn, delayMs) {
  let timer;
  return function (...args) {
    clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), delayMs);
  };
}

// ── Core check function ───────────────────────────────────────────────────────
async function checkPassword(password) {
  if (password.length === 0) {
    resetUI();
    return;
  }

  try {
    const response = await fetch("/check", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      // NOTE: the password goes to localhost only, never an external server.
      body: JSON.stringify({ password }),
    });

    if (!response.ok) {
      console.error("Server error:", response.status);
      return;
    }

    const data = await response.json();
    applyResult(data);
  } catch (err) {
    console.error("Fetch failed:", err);
  }
}

// ── Event listeners ───────────────────────────────────────────────────────────

// Debounced input handler (fires 200 ms after the user stops typing)
const debouncedCheck = debounce((e) => {
  checkPassword(e.target.value);
}, 200);

input.addEventListener("input", debouncedCheck);

// Show/hide password toggle
toggleBtn.addEventListener("click", () => {
  const isPassword = input.type === "password";
  input.type = isPassword ? "text" : "password";
  eyeIcon.textContent = isPassword ? "🙈" : "👁";
  toggleBtn.setAttribute("aria-label", isPassword ? "Hide password" : "Show password");
});
