from app.schemas.upload import ImageRoleSuggestion, ImageRoleSuggestionResponse
from app.utils.enums import ImageRole


class ImageRoleService:
    keyword_map = {
        ImageRole.street_view: ["street", "road", "outside-road", "surrounding", "lane", "traffic", "neighbourhood"],
        ImageRole.storefront: ["front", "storefront", "shopfront", "exterior", "outside", "signboard", "facade"],
        ImageRole.counter: ["counter", "billing", "cash", "pos", "desk", "register"],
        ImageRole.interior_shelf: ["shelf", "shelves", "inside", "interior", "aisle", "rack", "inventory"],
    }

    ordered_fallback = [
        ImageRole.interior_shelf,
        ImageRole.counter,
        ImageRole.storefront,
        ImageRole.street_view,
        ImageRole.extra,
    ]

    def _score_from_hints(self, hint: dict) -> tuple[ImageRole | None, float, str]:
        aspect_ratio = float(hint.get("aspect_ratio", 1.0))
        brightness = float(hint.get("brightness_score", 0.5))
        texture = float(hint.get("texture_score", 0.5))
        edge_density = float(hint.get("edge_density", 0.5))

        if aspect_ratio > 1.35 and brightness > 0.58 and texture < 0.52:
            return ImageRole.street_view, 0.79, "Wide, brighter outdoor-like frame with lower interior texture."
        if 1.0 <= aspect_ratio <= 1.9 and 0.32 <= brightness <= 0.68 and 0.10 <= edge_density <= 0.20 and 0.30 <= texture <= 0.58:
            return ImageRole.counter, 0.71, "Moderate texture and horizontal framing similar to a billing counter."
        if aspect_ratio > 1.15 and 0.40 <= brightness <= 0.78 and edge_density > 0.17:
            return ImageRole.storefront, 0.74, "Wide frame with facade-like edge structure."
        if 0.9 <= aspect_ratio <= 1.7 and texture > 0.62 and edge_density > 0.18:
            return ImageRole.interior_shelf, 0.76, "Dense texture and edge pattern similar to stocked shelves."
        return None, 0.0, ""

    def suggest_roles(self, filenames: list[str], image_hints: list[dict] | None = None) -> ImageRoleSuggestionResponse:
        suggestions: list[ImageRoleSuggestion] = []
        used_roles: list[ImageRole] = []
        hints_by_filename = {hint.get("filename"): hint for hint in (image_hints or []) if hint.get("filename")}
        for index, filename in enumerate(filenames):
            lower = filename.lower()
            matched_role = None
            reason = "Assigned from upload sequence as a fallback."
            confidence = 0.58

            hint = hints_by_filename.get(filename)
            if hint:
                hint_role, hint_confidence, hint_reason = self._score_from_hints(hint)
                if hint_role:
                    matched_role = hint_role
                    confidence = hint_confidence
                    reason = hint_reason

            for role, keywords in self.keyword_map.items():
                if any(keyword in lower for keyword in keywords):
                    matched_role = role
                    reason = f"Detected filename hints matching {role.value.replace('_', ' ')}."
                    confidence = max(confidence, 0.84)
                    break
            if matched_role is None:
                for fallback_role in self.ordered_fallback:
                    if fallback_role not in used_roles:
                        matched_role = fallback_role
                        break
            matched_role = matched_role or ImageRole.extra
            used_roles.append(matched_role)
            suggestions.append(
                ImageRoleSuggestion(
                    filename=filename,
                    suggested_role=matched_role,
                    confidence=confidence,
                    reason=reason,
                )
            )
        return ImageRoleSuggestionResponse(suggestions=suggestions)
