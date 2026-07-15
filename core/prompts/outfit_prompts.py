OUTFIT_SCORING_PROMPT = """
Analyze this outfit combination and return ONLY a JSON object.
Do not wrap in markdown. Do not include explanations.

{
    "confidence_score": 0.0 to 10.0,
    "color_harmony": "excellent|good|average|poor",
    "style_consistency": "excellent|good|average|poor",
    "occasion_fit": "casual|work|formal|sport|party",
    "strengths": ["what works well"],
    "improvements": ["what could be better"],
    "summary": "one sentence outfit review"
}

Return only the JSON. Nothing else.
"""