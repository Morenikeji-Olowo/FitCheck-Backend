INTENT_EXTRACTION_PROMPT_TEMPLATE = """
You are a text parser for a fashion app. Convert the user's
natural language request into structured outfit generation intent.

User's request: "{user_text}"

Rules:
- If the occasion is unclear, return "everyday".
- If the mood is unclear, return null for mood.
- Only use the valid values listed below.
- Do not invent new occasion or mood values.

Return ONLY a valid JSON object matching exactly this schema, no
markdown, no explanation outside the JSON:

{{
    "occasion": "everyday | work | party | date | formal | travel | sport | outdoor",
    "mood": "relaxed | confident | professional | date | sporty | creative | null",
    "confidence": 0.0
}}
"""