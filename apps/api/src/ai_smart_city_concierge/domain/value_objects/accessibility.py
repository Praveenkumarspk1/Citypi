"""
Accessibility Features Value Object
"""
from dataclasses import dataclass, field
from enum import Enum, auto


class AccessibilityCategory(Enum):
    """Categories of accessibility features"""
    MOBILITY = auto()      # Wheelchair, ramps, elevators
    VISUAL = auto()        # Braille, high contrast, screen readers
    HEARING = auto()       # Sign language, hearing loops, captions
    COGNITIVE = auto()     # Simple language, clear signage, quiet spaces
    MEDICAL = auto()       # First aid, AED, allergy-friendly
    SENSORY = auto()       # Quiet rooms, sensory-friendly hours


@dataclass(frozen=True, slots=True)
class AccessibilityFeature:
    """
    Individual accessibility feature with metadata.
    """
    name: str
    category: str
    description: str = ""
    available: bool = True
    details: dict = field(default_factory=dict)  # Additional metadata

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Feature name is required")
        if not self.category:
            raise ValueError("Category is required")

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "available": self.available,
            "details": self.details,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AccessibilityFeature":
        return cls(
            name=data["name"],
            category=data["category"],
            description=data.get("description", ""),
            available=data.get("available", True),
            details=data.get("details", {}),
        )


# Predefined accessibility features
class AccessibilityFeatures:
    """Predefined accessibility features registry"""

    # Mobility
    WHEELCHAIR_ACCESSIBLE = AccessibilityFeature(
        name="wheelchair_accessible",
        category="mobility",
        description="Entrance and main areas accessible by wheelchair",
        details={"ramp": True, "door_width_cm": 90}
    )

    WHEELCHAIR_RAMP = AccessibilityFeature(
        name="wheelchair_ramp",
        category="mobility",
        description="Ramp available for wheelchair access",
        details={"gradient_percent": 8, "handrails": True}
    )

    ELEVATOR = AccessibilityFeature(
        name="elevator",
        category="mobility",
        description="Elevator access to all floors",
        details={"capacity_kg": 1000, "door_width_cm": 90}
    )

    ACCESSIBLE_RESTROOM = AccessibilityFeature(
        name="accessible_restroom",
        category="mobility",
        description="Wheelchair accessible restroom",
        details={"grab_bars": True, "turning_space_cm": 150}
    )

    ACCESSIBLE_PARKING = AccessibilityFeature(
        name="accessible_parking",
        category="mobility",
        description="Designated accessible parking spaces",
        details={"spaces_count": 2, "van_accessible": True}
    )

    LOWERED_COUNTER = AccessibilityFeature(
        name="lowered_counter",
        category="mobility",
        description="Lowered service counter for wheelchair users",
        details={"height_cm": 85}
    )

    # Visual
    BRAILLE_SIGNAGE = AccessibilityFeature(
        name="braille_signage",
        category="visual",
        description="Braille signage throughout facility",
        details={"languages": ["en"]}
    )

    HIGH_CONTRAST = AccessibilityFeature(
        name="high_contrast",
        category="visual",
        description="High contrast color schemes and signage",
        details={"contrast_ratio": "7:1"}
    )

    LARGE_PRINT = AccessibilityFeature(
        name="large_print",
        category="visual",
        description="Large print materials available",
        details={"font_size_pt": 18}
    )

    SCREEN_READER_COMPATIBLE = AccessibilityFeature(
        name="screen_reader_compatible",
        category="visual",
        description="Website/app compatible with screen readers",
        details={"wcag_level": "AA"}
    )

    AUDIO_DESCRIPTION = AccessibilityFeature(
        name="audio_description",
        category="visual",
        description="Audio description for visual content",
        details={"languages": ["en"]}
    )

    TACTILE_PATHS = AccessibilityFeature(
        name="tactile_paths",
        category="visual",
        description="Tactile ground surface indicators",
        details={"material": "truncated_domes"}
    )

    # Hearing
    HEARING_LOOP = AccessibilityFeature(
        name="hearing_loop",
        category="hearing",
        description="Induction hearing loop system",
        details={"coverage_area": "main_hall"}
    )

    SIGN_LANGUAGE = AccessibilityFeature(
        name="sign_language",
        category="hearing",
        description="Sign language interpretation available",
        details={"languages": ["ASL", "BSL"]}
    )

    CLOSED_CAPTIONS = AccessibilityFeature(
        name="closed_captions",
        category="hearing",
        description="Closed captions for video content",
        details={"languages": ["en", "es"]}
    )

    VISUAL_ALERTS = AccessibilityFeature(
        name="visual_alerts",
        category="hearing",
        description="Visual fire alarms and notifications",
        details={"strobe_lights": True}
    )

    # Cognitive
    SIMPLE_LANGUAGE = AccessibilityFeature(
        name="simple_language",
        category="cognitive",
        description="Information in plain/simple language",
        details={"reading_level": "grade_6"}
    )

    CLEAR_SIGNAGE = AccessibilityFeature(
        name="clear_signage",
        category="cognitive",
        description="Clear, consistent wayfinding signage",
        details={"pictograms": True, "color_coded": True}
    )

    QUIET_SPACE = AccessibilityFeature(
        name="quiet_space",
        category="cognitive",
        description="Designated quiet/sensory room",
        details={"capacity": 4, "soundproofing": True}
    )

    PREDICTABLE_LAYOUT = AccessibilityFeature(
        name="predictable_layout",
        category="cognitive",
        description="Consistent, predictable spatial layout",
        details={}
    )

    # Medical
    FIRST_AID = AccessibilityFeature(
        name="first_aid",
        category="medical",
        description="First aid kit and trained staff",
        details={"aed": True, "staff_trained": True}
    )

    ALLERGY_FRIENDLY = AccessibilityFeature(
        name="allergy_friendly",
        category="medical",
        description="Allergy-aware food options and labeling",
        details={"common_allergens_labeled": True}
    )

    # Sensory
    SENSORY_FRIENDLY_HOURS = AccessibilityFeature(
        name="sensory_friendly_hours",
        category="sensory",
        description="Designated low-sensory hours",
        details={"days": ["Sunday"], "hours": "10:00-12:00"}
    )

    REDUCED_STIMULATION = AccessibilityFeature(
        name="reduced_stimulation",
        category="sensory",
        description="Reduced lighting, sound, and crowds",
        details={"lighting_level": "dim", "music": False}
    )

    @classmethod
    def all(cls) -> list:
        """Get all predefined features"""
        return [
            cls.WHEELCHAIR_ACCESSIBLE,
            cls.WHEELCHAIR_RAMP,
            cls.ELEVATOR,
            cls.ACCESSIBLE_RESTROOM,
            cls.ACCESSIBLE_PARKING,
            cls.LOWERED_COUNTER,
            cls.BRAILLE_SIGNAGE,
            cls.HIGH_CONTRAST,
            cls.LARGE_PRINT,
            cls.SCREEN_READER_COMPATIBLE,
            cls.AUDIO_DESCRIPTION,
            cls.TACTILE_PATHS,
            cls.HEARING_LOOP,
            cls.SIGN_LANGUAGE,
            cls.CLOSED_CAPTIONS,
            cls.VISUAL_ALERTS,
            cls.SIMPLE_LANGUAGE,
            cls.CLEAR_SIGNAGE,
            cls.QUIET_SPACE,
            cls.PREDICTABLE_LAYOUT,
            cls.FIRST_AID,
            cls.ALLERGY_FRIENDLY,
            cls.SENSORY_FRIENDLY_HOURS,
            cls.REDUCED_STIMULATION,
        ]

    @classmethod
    def by_category(cls, category: str) -> list:
        """Get features by category"""
        return [f for f in cls.all() if f.category == category]

    @classmethod
    def get_names(cls) -> list[str]:
        """Get all feature names"""
        return [f.name for f in cls.all()]


@dataclass(frozen=True, slots=True)
class AccessibilityProfile:
    """
    Complete accessibility profile for a place.
    Immutable collection of features.
    """
    features: tuple[AccessibilityFeature, ...] = field(default_factory=tuple)
    overall_score: float = 0.0  # 0-100 accessibility score
    last_audited: str | None = None  # ISO date string
    notes: str = ""

    def __post_init__(self) -> None:
        # Calculate overall score if not provided
        if self.overall_score == 0.0 and self.features:
            available = sum(1 for f in self.features if f.available)
            total = len(self.features)
            object.__setattr__(self, 'overall_score', round(available / total * 100, 1))

    def has_feature(self, feature_name: str) -> bool:
        """Check if a specific feature is available"""
        for feature in self.features:
            if feature.name == feature_name and feature.available:
                return True
        return False

    def get_features_by_category(self, category: str) -> list[AccessibilityFeature]:
        """Get all features in a category"""
        return [f for f in self.features if f.category == category and f.available]

    def get_categories(self) -> list[str]:
        """Get list of categories with available features"""
        categories = set()
        for f in self.features:
            if f.available:
                categories.add(f.category)
        return sorted(categories)

    def to_dict(self) -> dict:
        return {
            "features": [f.to_dict() for f in self.features],
            "overall_score": self.overall_score,
            "last_audited": self.last_audited,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AccessibilityProfile":
        return cls(
            features=tuple(AccessibilityFeature.from_dict(f) for f in data.get("features", [])),
            overall_score=data.get("overall_score", 0.0),
            last_audited=data.get("last_audited"),
            notes=data.get("notes", ""),
        )

    @classmethod
    def from_feature_names(cls, feature_names: list[str]) -> "AccessibilityProfile":
        """Create profile from list of feature names"""
        all_features = {f.name: f for f in AccessibilityFeatures.all()}
        features = []
        for name in feature_names:
            if name in all_features:
                features.append(all_features[name])
            else:
                # Create custom feature
                features.append(AccessibilityFeature(name=name, category="custom"))
        return cls(features=tuple(features))

    @classmethod
    def fully_accessible(cls) -> "AccessibilityProfile":
        """Create a fully accessible profile"""
        return cls(features=tuple(AccessibilityFeatures.all()))

    @classmethod
    def wheelchair_accessible(cls) -> "AccessibilityProfile":
        """Create profile with key wheelchair features"""
        return cls(features=(
            AccessibilityFeatures.WHEELCHAIR_ACCESSIBLE,
            AccessibilityFeatures.WHEELCHAIR_RAMP,
            AccessibilityFeatures.ELEVATOR,
            AccessibilityFeatures.ACCESSIBLE_RESTROOM,
            AccessibilityFeatures.ACCESSIBLE_PARKING,
        ))

    def __str__(self) -> str:
        available = sum(1 for f in self.features if f.available)
        return f"AccessibilityProfile(score={self.overall_score:.0f}, features={available}/{len(self.features)})"

    def __repr__(self) -> str:
        return f"AccessibilityProfile(score={self.overall_score:.1f}, features={len(self.features)})"


@dataclass(frozen=True, slots=True)
class AccessibilityInfo:
    """
    Simple accessibility info for POIs (used in tests).
    For more detailed accessibility, use AccessibilityProfile.
    """
    wheelchair_accessible: bool = False
    wheelchair_accessible_entrance: bool = False
    wheelchair_accessible_parking: bool = False
    wheelchair_accessible_restroom: bool = False
    hearing_loop_available: bool = False
    visual_aids_available: bool = False
