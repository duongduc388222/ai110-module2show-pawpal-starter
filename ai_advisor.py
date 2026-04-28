"""PawPal+ — Gemini-powered care task advisor."""

from __future__ import annotations

import json
import os
import re

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()  # loads .env from project root if present

ALLOWED_SPECIES = {"dog", "cat", "rabbit", "bird", "fish", "other"}
_VALID_PRIORITY = {"low", "medium", "high"}
_VALID_FREQUENCY = {"once", "daily", "weekly"}
_TIME_RE = re.compile(r"^\d{2}:\d{2}$")

_PROMPT_TEMPLATE = """\
You are a veterinary care assistant. Given a pet's details, suggest 3–5 appropriate \
care tasks spread across a typical day.

Return ONLY a valid JSON array. Each element must be an object with exactly these fields:
- "title": string, max 80 characters, descriptive task name
- "time": string in HH:MM format (24-hour, zero-padded, e.g. "08:00")
- "duration_minutes": integer between 1 and 480
- "priority": one of "low", "medium", "high"
- "frequency": one of "once", "daily", "weekly"

Do not include any explanation, markdown, or extra keys. Output only the JSON array.

Pet: {pet_name} ({species}, {age_years} year(s) old).{notes_line}
"""


class AdvisorError(ValueError):
    """Raised when the advisor cannot return valid task suggestions."""


def get_task_suggestions(
    pet_name: str,
    species: str,
    age_years: float,
    notes: str = "",
) -> list[dict]:
    """Call Gemini and return validated task dicts for the given pet.

    Each dict contains: title, time, duration_minutes, priority, frequency, pet_name.
    Raises AdvisorError on invalid input, API failure, or zero valid tasks returned.
    """
    _validate_inputs(pet_name, species, age_years)
    notes = notes.strip()[:300]
    notes_line = f" Notes: {notes}" if notes else ""

    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        raise AdvisorError(
            "GEMINI_API_KEY environment variable is not set. "
            "Get a free key at https://aistudio.google.com/apikey"
        )

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        generation_config={"response_mime_type": "application/json", "temperature": 0.7},
    )

    prompt = _PROMPT_TEMPLATE.format(
        pet_name=pet_name,
        species=species,
        age_years=age_years,
        notes_line=notes_line,
    )

    try:
        response = model.generate_content(prompt)
        raw = response.text
    except Exception as exc:
        raise AdvisorError(f"Gemini API error: {exc}") from exc

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AdvisorError(f"Gemini returned non-JSON output: {exc}") from exc

    if not isinstance(data, list):
        raise AdvisorError("Gemini returned a JSON object instead of an array.")

    valid_tasks = [t for item in data if (t := _validate_task_dict(item, pet_name)) is not None]

    if not valid_tasks:
        raise AdvisorError("No valid tasks returned. Try different inputs.")

    return valid_tasks


# ── Validation helpers ────────────────────────────────────────────────────────

def _validate_inputs(pet_name: str, species: str, age_years: float) -> None:
    if not isinstance(pet_name, str) or not pet_name.strip():
        raise AdvisorError("pet_name must be a non-empty string.")
    if len(pet_name) > 50:
        raise AdvisorError("pet_name must be 50 characters or fewer.")
    if species not in ALLOWED_SPECIES:
        raise AdvisorError(
            f"Species '{species}' is not supported. "
            f"Choose from: {', '.join(sorted(ALLOWED_SPECIES))}."
        )
    try:
        age = float(age_years)
    except (TypeError, ValueError):
        raise AdvisorError("age_years must be a number.")
    if not (0 < age <= 30):
        raise AdvisorError("age_years must be between 0 (exclusive) and 30.")


def _validate_task_dict(item: object, pet_name: str) -> dict | None:
    """Return a cleaned task dict (with pet_name) or None if the item is malformed."""
    if not isinstance(item, dict):
        return None

    if not {"title", "time", "duration_minutes", "priority", "frequency"}.issubset(item):
        return None

    title = str(item["title"]).strip()[:80]
    if not title:
        return None

    time_val = str(item["time"]).strip()
    if not _TIME_RE.match(time_val):
        return None
    h, m = int(time_val[:2]), int(time_val[3:])
    if not (0 <= h <= 23 and 0 <= m <= 59):
        return None

    try:
        duration = int(item["duration_minutes"])
    except (TypeError, ValueError):
        return None
    if not (1 <= duration <= 480):
        return None

    priority = str(item["priority"]).strip().lower()
    if priority not in _VALID_PRIORITY:
        return None

    frequency = str(item["frequency"]).strip().lower()
    if frequency not in _VALID_FREQUENCY:
        return None

    return {
        "title": title,
        "time": time_val,
        "duration_minutes": duration,
        "priority": priority,
        "frequency": frequency,
        "pet_name": pet_name,
    }
