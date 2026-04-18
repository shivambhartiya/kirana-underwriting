from dataclasses import dataclass, field


@dataclass
class UnderwritingFeatureVector:
    session_id: str
    visual_features: dict = field(default_factory=dict)
    geo_features: dict = field(default_factory=dict)
    qc_features: dict = field(default_factory=dict)
    optional_inputs: dict = field(default_factory=dict)

    def as_flat_dict(self) -> dict:
        return {
            **self.visual_features,
            **self.geo_features,
            **self.qc_features,
            **self.optional_inputs,
        }

