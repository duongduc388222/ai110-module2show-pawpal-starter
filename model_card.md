# Model Card — PawPal+ AI Care Advisor

## 1. How AI Was Used During Development

**Building the system:**  
The AI Care Advisor feature was built using the Google Gemini 2.5 Flash model via the `google-genai` SDK. Gemini is called with a structured prompt that instructs it to return a JSON array of care task objects (title, time, duration, priority, frequency). The `response_mime_type: "application/json"` generation config parameter constrains the model to produce parseable output, reducing the need for brittle regex post-processing.

**During development (Claude as coding assistant):**  
Claude (claude-sonnet-4-6) was used throughout development as a coding assistant for:
- Designing the `ai_advisor.py` module structure and the `AdvisorError` exception hierarchy
- Writing the Streamlit tab layout and session state caching logic for AI suggestions
- Structuring the eval harness test matrix (6 cases covering both happy path and guardrail scenarios)
- Debugging the `google-generativeai` → `google-genai` SDK migration when the older package was flagged as deprecated

All AI-generated code was read, understood, and verified before acceptance. No output was committed without manual review.

---

## 2. One Helpful AI Suggestion

**Suggestion:** Use `response_mime_type: "application/json"` in Gemini's generation config.

When first drafting the prompt, the plan was to parse JSON from Gemini's free-text response using a regex to strip markdown code fences. Claude suggested using the `GenerateContentConfig(response_mime_type="application/json")` parameter instead, which instructs the model at the API level to return only valid JSON — no fences, no preamble.

**Why it was helpful:** This eliminated an entire class of parsing failures. The output guardrail in `_validate_task_dict()` still validates field-level correctness, but the JSON parse step itself became reliable. The occasional parse failure that did occur (Case 4 in the eval harness on first run) was caught by the retry loop rather than crashing the app.

---

## 3. One Flawed AI Suggestion

**Suggestion:** Use `google-generativeai` as the SDK dependency.

The initial implementation used `import google.generativeai as genai` with `genai.GenerativeModel(...)`. This worked at the code level but triggered a `FutureWarning` at runtime:

```
All support for the `google.generativeai` package has ended.
Please switch to the `google.genai` package.
```

The package had been fully deprecated with no further updates or bug fixes. Claude had recommended it because it was the widely-documented SDK at the time of training, but it was already obsolete. The fix required migrating to the `google-genai` package, which uses a different client-based API (`genai.Client(api_key=...).models.generate_content(...)`).

**Lesson:** AI coding assistants can suggest dependencies that are current in their training data but deprecated by the time of use. Always check the official SDK README and PyPI release dates before pinning a new dependency.

---

## 4. System Limitations

- **Hallucination risk:** Gemini's task suggestions are plausible but not veterinary-validated. A suggestion like "feed fish every 2 hours" could be generated for a species that requires once-daily feeding. The system has no factual grounding beyond the model's training data.
- **No breed or condition specificity:** The prompt passes species and age but not breed, medical history, or dietary restrictions. A diabetic dog and a healthy dog receive essentially the same suggestions.
- **Single-day scope:** Task times are scheduled across a single day (00:00–23:59). The system cannot model multi-day care regimens or vet appointment scheduling across weeks.
- **No user feedback loop:** Suggestions that the user rejects or edits are not fed back to improve future calls. Every request starts from scratch with no personalization memory.
- **Flaky JSON output:** Despite `response_mime_type: "application/json"`, Gemini occasionally returns malformed JSON. The retry loop (up to 3 attempts) mitigates this but does not eliminate it — a 3-failure streak raises `AdvisorError` and the user must try again.

---

## 5. Potential Future Improvements

- **RAG with a pet care knowledge base:** Index breed-specific care guides, ASPCA feeding guidelines, and vet checklists as documents. Retrieve the top-k relevant chunks before calling Gemini so suggestions are grounded in vetted sources rather than model memory alone.
- **User feedback integration:** Track which AI-suggested tasks the user accepts, edits, or deletes. Use this signal to refine the prompt (e.g., "this owner prefers 30-minute walks, not 15-minute ones") in future sessions.
- **Multi-turn conversation:** Replace the single-shot prompt with a conversational interface so the user can say "make the morning walk shorter" or "add a grooming task on Saturdays" and have Gemini revise the suggestions in context.
- **Confidence scoring:** Ask Gemini to return a `confidence` field (0.0–1.0) per task and surface low-confidence suggestions with a warning badge in the UI.
- **Structured output schema enforcement:** Use Gemini's `response_schema` parameter (available in newer SDK versions) to declare the exact JSON schema, reducing reliance on prompt-level instructions for structure.
