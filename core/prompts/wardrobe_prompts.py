WARDROBE_CLASSIFICATION_PROMPT = """
Analyze this clothing item and return ONLY a JSON object.
Do not wrap in markdown. Do not include explanations.

{
    "category": "top|bottom|shoes|bag|accessory|jewellery|headwear|scarf|belt|outerwear|dress",
    "type": "specific type e.g. hoodie, jeans, sneakers",
    "dominant_color": "human-readable color name e.g. navy",
    "dominant_hex": "hex code of the dominant color e.g. #1F3B73",
    "secondary_color": "human-readable color name or null if none",
    "secondary_hex": "hex code or null if no secondary color",
    "accent_color": "human-readable color name or null if none",
    "accent_hex": "hex code or null if no accent color",
    "pattern": "solid|striped|floral|graphic|checkered|animal|abstract",
    "style": "casual|formal|streetwear|business|athletic|vintage",
    "season": ["spring|summer|fall|winter"],
    "occasion": ["everyday|work|party|sport|formal|outdoor"],
    "brand": "brand name if visible or unknown",
    "pairs_well_with": ["color or item suggestions"],
    "confidence": 0.0 to 1.0
}

Estimate hex codes as accurately as possible based on what you 
visually observe in the image. Return only the JSON. Nothing else.
"""