AVATAR_ANALYSIS_PROMPT = """
Analyze this photo of a person and return ONLY a JSON object.
Do not wrap in markdown. Do not include explanations.

{
    "body_shape": "rectangle|triangle|inverted_triangle|hourglass|oval|athletic",
    "estimated_height": "short|average|tall",
    "skin_tone": "fair|light|medium|olive|brown|dark",
    "shoulder_width": "narrow|average|broad",
    "waist_definition": "defined|average|undefined",
    "build": "slim|athletic|average|full",
    "confidence": 0.0 to 1.0
}

Return only the JSON. Nothing else.
"""