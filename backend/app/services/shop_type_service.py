from app.schemas.upload import ShopTypeCandidate, ShopTypeSuggestionResponse
from app.utils.enums import ShopType
from app.utils.geo_math import clamp


class ShopTypeService:
    keyword_map = {
        ShopType.religious_gifts: ["pooja", "puja", "religious", "gift", "spiritual", "agarbatti", "kumkum", "murti", "mandir", "devotional"],
        ShopType.vegetable_fruit: ["fruit", "vegetable", "sabzi", "fresh", "produce"],
        ShopType.pharmacy_medical: ["medical", "pharmacy", "chemist", "drug", "clinic", "tablet", "capsule"],
        ShopType.fast_food_qsr: ["food", "restaurant", "burger", "tea", "snack", "fastfood"],
        ShopType.jewellery: ["gold", "jewellery", "jewelry", "ornament", "silver"],
        ShopType.bakery_sweets: ["bakery", "cake", "sweet", "mithai", "pastry"],
        ShopType.mobile_electronics: ["mobile", "phone", "electronics", "repair", "laptop"],
        ShopType.apparel_boutique: ["fashion", "garment", "clothes", "boutique", "apparel"],
        ShopType.kirana_general: ["kirana", "grocery", "general", "provision", "mart"],
    }

    def _add_score(self, scores: dict[ShopType, float], reasons: dict[ShopType, list[str]], shop_type: ShopType, value: float, reason: str):
        scores[shop_type] += value
        if reason not in reasons[shop_type]:
            reasons[shop_type].append(reason)

    def suggest_shop_type(self, filenames: list[str], image_hints: list[dict] | None = None) -> ShopTypeSuggestionResponse:
        image_hints = image_hints or []
        scores = {shop_type: 0.0 for shop_type in ShopType}
        reasons = {shop_type: [] for shop_type in ShopType}

        for filename in filenames:
            lower = filename.lower()
            for shop_type, keywords in self.keyword_map.items():
                matched_keywords = [keyword for keyword in keywords if keyword in lower]
                if matched_keywords:
                    self._add_score(
                        scores,
                        reasons,
                        shop_type,
                        0.95,
                        f"Filename hints matched {', '.join(matched_keywords[:2])}.",
                    )

        if image_hints:
            ocr_blob = " ".join(
                str(token).lower()
                for hint in image_hints
                for token in ([hint.get("ocr_text", "")] + list(hint.get("ocr_tokens", [])))
                if token
            )
            for shop_type, keywords in self.keyword_map.items():
                matched_ocr_keywords = [keyword for keyword in keywords if keyword in ocr_blob]
                if matched_ocr_keywords:
                    self._add_score(
                        scores,
                        reasons,
                        shop_type,
                        1.1,
                        f"OCR-like text cues matched {', '.join(matched_ocr_keywords[:2])}.",
                    )

            avg_brightness = sum(float(hint.get("brightness_score", 0.5)) for hint in image_hints) / len(image_hints)
            avg_texture = sum(float(hint.get("texture_score", 0.5)) for hint in image_hints) / len(image_hints)
            avg_warm = sum(float(hint.get("warm_ratio", 0.3)) for hint in image_hints) / len(image_hints)
            avg_green = sum(float(hint.get("green_ratio", 0.2)) for hint in image_hints) / len(image_hints)
            avg_saturation = sum(float(hint.get("saturation_score", 0.3)) for hint in image_hints) / len(image_hints)
            avg_edge = sum(float(hint.get("edge_density", 0.15)) for hint in image_hints) / len(image_hints)
            avg_contrast = sum(float(hint.get("contrast_score", 0.25)) for hint in image_hints) / len(image_hints)
            avg_red = sum(float(hint.get("red_ratio", 0.18)) for hint in image_hints) / len(image_hints)
            avg_yellow = sum(float(hint.get("yellow_ratio", 0.12)) for hint in image_hints) / len(image_hints)
            avg_white = sum(float(hint.get("white_ratio", 0.18)) for hint in image_hints) / len(image_hints)
            showcase_score = clamp((avg_brightness * 0.35) + (avg_contrast * 0.25) + (avg_edge * 0.20) + (avg_white * 0.20), 0.0, 1.0)
            devotional_palette = clamp((avg_warm * 1.20) + (avg_red * 1.35) + (avg_yellow * 1.20) + (avg_saturation * 0.85), 0.0, 3.5)
            medical_packaging = clamp((avg_brightness * 0.95) + (avg_white * 0.95) + (avg_green * 0.75) + ((1 - avg_warm) * 0.35) + ((1 - avg_saturation) * 0.25), 0.0, 3.0)

            self._add_score(
                scores,
                reasons,
                ShopType.religious_gifts,
                (devotional_palette * 1.05) + (showcase_score * 0.65) + (avg_texture * 0.20),
                "Warm saffron and red palette with dense showcase merchandising aligns with pooja and religious gift stores.",
            )
            self._add_score(
                scores,
                reasons,
                ShopType.jewellery,
                (showcase_score * 0.95) + (avg_contrast * 0.65) + ((1 - avg_texture) * 0.30),
                "Glass showcase and contrast cues can overlap with jewellery-style merchandising.",
            )
            self._add_score(
                scores,
                reasons,
                ShopType.pharmacy_medical,
                (medical_packaging * 0.85) - (devotional_palette * 0.60),
                "Medical-like shelving should show brighter white-green packaging and less devotional palette bias.",
            )
            self._add_score(
                scores,
                reasons,
                ShopType.kirana_general,
                (avg_texture * 0.85) + (avg_edge * 0.70) + (avg_saturation * 0.30),
                "General trade stores usually show denser mixed packaging and aisle texture.",
            )
            self._add_score(
                scores,
                reasons,
                ShopType.bakery_sweets,
                (avg_warm * 0.70) + (avg_saturation * 0.50),
                "Warm color bias can also appear in sweets and bakery merchandising.",
            )
            self._add_score(
                scores,
                reasons,
                ShopType.mobile_electronics,
                (avg_edge * 0.80) + ((1 - avg_saturation) * 0.45),
                "Sharper edges and lower saturation are common in electronics displays.",
            )
            self._add_score(
                scores,
                reasons,
                ShopType.apparel_boutique,
                (avg_contrast * 0.45) + (avg_saturation * 0.30),
                "Boutique displays often lean on contrast and color curation.",
            )
            self._add_score(
                scores,
                reasons,
                ShopType.fast_food_qsr,
                (avg_warm * 0.45) + (avg_texture * 0.20),
                "Food formats often share some warm color cues but usually have different layout density.",
            )
            self._add_score(
                scores,
                reasons,
                ShopType.vegetable_fruit,
                (avg_green * 0.95) + (avg_saturation * 0.50),
                "Produce-heavy shops usually show stronger green saturation and organic variation.",
            )

        sorted_scores = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        total_score = sum(max(value, 0.01) for _, value in sorted_scores)
        top_score = sorted_scores[0][1]
        second_score = sorted_scores[1][1] if len(sorted_scores) > 1 else 0.0
        margin = max(top_score - second_score, 0.0)
        normalized_confidence = clamp((max(top_score, 0.01) / total_score) + 0.22 + (margin * 0.04), 0.34, 0.95)
        needs_confirmation = normalized_confidence < 0.60 or margin < 0.12

        top_candidates = [
            ShopTypeCandidate(
                shop_type=shop_type,
                confidence=round(clamp((max(score, 0.01) / total_score) + (0.08 if index == 0 else 0.0), 0.05, 0.95), 2),
                reasons=reasons[shop_type][:3],
            )
            for index, (shop_type, score) in enumerate(sorted_scores[:3])
        ]
        detected_shop_type = top_candidates[0].shop_type
        reasoning = reasons[detected_shop_type][:4] or ["Fallback to ranked specialty-retail priors."]

        return ShopTypeSuggestionResponse(
            detected_shop_type=detected_shop_type,
            confidence=round(normalized_confidence, 2),
            source="image_and_filename_inference",
            reasoning=reasoning,
            top_candidates=top_candidates,
            needs_confirmation=needs_confirmation,
        )
