WARDROBE_CLASSIFICATION_PROMPT = """
Analyze this clothing item and return ONLY a JSON object.
Do not wrap in markdown. Do not include explanations.

{
    "category": "top|bottom|shoes|bag|accessory|jewellery|headwear|scarf|belt|outerwear|dress",
    "type": "specific type e.g. hoodie, jeans, sneakers",
    "colors": ["primary color", "secondary color if any"],
    "pattern": "solid|striped|floral|graphic|checkered|animal|abstract",
    "style": "casual|formal|streetwear|business|athletic|vintage",
    "season": ["spring|summer|fall|winter"],
    "occasion": ["everyday|work|party|sport|formal|outdoor"],
    "brand": "brand name if visible or unknown",
    "pairs_well_with": ["color or item suggestions"],
    "confidence": 0.0 to 1.0
}

Return only the JSON. Nothing else.
"""