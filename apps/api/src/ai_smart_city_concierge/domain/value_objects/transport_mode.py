"""
Transport Mode Value Object
"""
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum, auto


class TransportModeType(Enum):
    """Types of transport modes"""
    WALKING = auto()
    CYCLING = auto()
    E_SCOOTER = auto()
    E_BIKE = auto()
    PUBLIC_TRANSIT_BUS = auto()
    PUBLIC_TRANSIT_METRO = auto()
    SUBWAY = PUBLIC_TRANSIT_METRO
    PUBLIC_TRANSIT_TRAM = auto()
    PUBLIC_TRANSIT_TRAIN = auto()
    PUBLIC_TRANSIT_FERRY = auto()
    CAR = auto()
    TAXI = auto()
    RIDE_SHARE = auto()
    CARPOOL = auto()
    MOTORCYCLE = auto()


@dataclass(frozen=True, slots=True)
class TransportMode:
    SUBWAY = "SUBWAY"
    """
    Transport mode with characteristics.
    """
    type: TransportModeType
    name: str = ""
    speed_kmh: float = 0.0
    cost_per_km: Decimal = Decimal("0.0")
    co2_per_km_g: float = 0.0
    capacity: int = 1
    requires_license: bool = False
    is_accessible: bool = False
    description: str = ""

    def __post_init__(self) -> None:
        if not self.name:
            object.__setattr__(self, 'name', self.type.name.lower().replace('_', ' '))

    @property
    def is_active(self) -> bool:
        """Check if human-powered (walking, cycling)"""
        return self.type in (TransportModeType.WALKING, TransportModeType.CYCLING)

    @property
    def is_motorized(self) -> bool:
        """Check if motorized"""
        return not self.is_active

    @property
    def is_public_transit(self) -> bool:
        """Check if public transit"""
        return self.type in (
            TransportModeType.PUBLIC_TRANSIT_BUS,
            TransportModeType.PUBLIC_TRANSIT_METRO,
            TransportModeType.PUBLIC_TRANSIT_TRAM,
            TransportModeType.PUBLIC_TRANSIT_TRAIN,
            TransportModeType.PUBLIC_TRANSIT_FERRY,
        )

    def to_dict(self) -> dict:
        return {
            "type": self.type.name,
            "name": self.name,
            "speed_kmh": self.speed_kmh,
            "cost_per_km": float(self.cost_per_km),
            "co2_per_km_g": self.co2_per_km_g,
            "capacity": self.capacity,
            "requires_license": self.requires_license,
            "is_accessible": self.is_accessible,
            "description": self.description,
        }

    @classmethod
    def walking(cls) -> "TransportMode":
        return cls(
            type=TransportModeType.WALKING,
            speed_kmh=5.0,
            cost_per_km=Decimal("0.0"),
            co2_per_km_g=0.0,
            capacity=1,
            is_accessible=True,
            description="Walking",
        )

    @classmethod
    def cycling(cls) -> "TransportMode":
        return cls(
            type=TransportModeType.CYCLING,
            speed_kmh=15.0,
            cost_per_km=Decimal("0.0"),
            co2_per_km_g=0.0,
            capacity=1,
            is_accessible=True,
            description="Cycling",
        )

    @classmethod
    def public_transit_bus(cls) -> "TransportMode":
        return cls(
            type=TransportModeType.PUBLIC_TRANSIT_BUS,
            speed_kmh=20.0,
            cost_per_km=Decimal("0.50"),
            co2_per_km_g=80.0,
            capacity=50,
            is_accessible=True,
            description="Public Bus",
        )

    @classmethod
    def subway(cls) -> "TransportMode":
        return cls(
            type=TransportModeType.SUBWAY,
            speed_kmh=35.0,
            cost_per_km=Decimal("1.00"),
            co2_per_km_g=40.0,
            capacity=200,
            is_accessible=True,
            description="Metro/Subway",
        )

    @classmethod
    def tram(cls) -> "TransportMode":
        return cls(
            type=TransportModeType.PUBLIC_TRANSIT_TRAM,
            speed_kmh=25.0,
            cost_per_km=Decimal("0.80"),
            co2_per_km_g=50.0,
            capacity=100,
            is_accessible=True,
            description="Tram/Light Rail",
        )

    @classmethod
    def train(cls) -> "TransportMode":
        return cls(
            type=TransportModeType.PUBLIC_TRANSIT_TRAIN,
            speed_kmh=80.0,
            cost_per_km=Decimal("2.00"),
            co2_per_km_g=30.0,
            capacity=300,
            is_accessible=True,
            description="Train",
        )

    @classmethod
    def car(cls) -> "TransportMode":
        return cls(
            type=TransportModeType.CAR,
            speed_kmh=50.0,
            cost_per_km=Decimal("0.60"),
            co2_per_km_g=150.0,
            capacity=5,
            requires_license=True,
            description="Car",
        )

    @classmethod
    def taxi(cls) -> "TransportMode":
        return cls(
            type=TransportModeType.TAXI,
            speed_kmh=40.0,
            cost_per_km=Decimal("3.00"),
            co2_per_km_g=180.0,
            capacity=4,
            requires_license=True,
            description="Taxi",
        )


@dataclass
class TransportModes:
    """Collection of available transport modes for a user"""
    preferred: list[TransportMode] = field(default_factory=list)
    available: list[TransportMode] = field(default_factory=list)
    accessibility_constraints: list[str] = field(default_factory=list)

    def get_fastest(self) -> TransportMode | None:
        """Get fastest available transport mode"""
        if not self.available:
            return None
        return max(self.available, key=lambda m: m.speed_kmh)

    def get_cheapest(self) -> TransportMode | None:
        """Get cheapest available transport mode"""
        if not self.available:
            return None
        return min(self.available, key=lambda m: m.cost_per_km)

    def get_most_eco(self) -> TransportMode | None:
        """Get most eco-friendly available transport mode"""
        if not self.available:
            return None
        return min(self.available, key=lambda m: m.co2_per_km_g)

    def filter_by_accessibility(self, needs: list[str]) -> list[TransportMode]:
        """Filter modes by accessibility needs"""
        return [
            m for m in self.available
            if all(need in m.description.lower() for need in needs)
        ]

    def to_dict(self) -> dict:
        return {
            "preferred": [m.to_dict() for m in self.preferred],
            "available": [m.to_dict() for m in self.available],
            "accessibility_constraints": self.accessibility_constraints,
        }

