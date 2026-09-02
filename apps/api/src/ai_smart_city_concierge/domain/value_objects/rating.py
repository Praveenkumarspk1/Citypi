"""
Rating Value Object
"""
import math
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal


@dataclass(frozen=True, slots=True)
class Rating:
    """
    Immutable rating value with Bayesian average calculation.
    """
    value: Decimal
    review_count: int = 0
    min_value: Decimal = Decimal("1.0")
    max_value: Decimal = Decimal("5.0")

    def __post_init__(self) -> None:
        """Validate and normalize after initialization"""
        if not isinstance(self.value, Decimal):
            object.__setattr__(self, 'value', Decimal(str(self.value)))

        # Round to 1 decimal place
        object.__setattr__(self, 'value', self.value.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP))

        if not isinstance(self.review_count, int):
            object.__setattr__(self, 'review_count', int(self.review_count))

        if self.review_count < 0:
            raise ValueError("Review count cannot be negative")

        if self.value < self.min_value or self.value > self.max_value:
            raise ValueError(f"Rating must be between {self.min_value} and {self.max_value}")

    @property
    def is_rated(self) -> bool:
        """Check if there are any reviews"""
        return self.review_count > 0

    @property
    def stars(self) -> int:
        """Get integer star rating (rounded)"""
        return int(round(float(self.value)))

    @property
    def percentage(self) -> float:
        """Get rating as percentage (0-100)"""
        return float((self.value - self.min_value) / (self.max_value - self.min_value) * 100)

    def bayesian_average(self, prior_average: Decimal, prior_weight: int) -> Decimal:
        """
        Calculate Bayesian average to handle low review counts.

        Args:
            prior_average: Global average rating (e.g., 3.5)
            prior_weight: Weight of prior (e.g., 10 reviews worth)

        Returns:
            Bayesian adjusted rating
        """
        if not self.is_rated:
            return prior_average.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)

        total_weight = self.review_count + prior_weight
        weighted_sum = (self.value * self.review_count) + (prior_average * prior_weight)
        bayesian = (weighted_sum / total_weight).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)

        return bayesian

    def wilson_lower_bound(self, confidence: float = 0.95) -> Decimal:
        """
        Calculate Wilson score interval lower bound for ranking.
        Useful for sorting by rating with confidence.
        """
        if not self.is_rated:
            return Decimal("0.0")

        # Convert to proportion (0-1)
        p = float((self.value - self.min_value) / (self.max_value - self.min_value))
        n = self.review_count

        # Z-score for confidence level
        z_scores = {0.90: 1.645, 0.95: 1.96, 0.99: 2.576}
        z = z_scores.get(confidence, 1.96)

        # Wilson score formula
        denominator = 1 + z**2 / n
        centre = p + z**2 / (2 * n)
        adjustment = z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2))
        lower = (centre - adjustment) / denominator

        # Convert back to rating scale
        rating_range = float(self.max_value - self.min_value)
        lower_bound = float(self.min_value) + lower * rating_range

        return Decimal(str(lower_bound)).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)

    def add_review(self, new_rating: Decimal) -> "Rating":
        """Add a new review and return updated rating"""
        new_count = self.review_count + 1
        new_total = (self.value * self.review_count) + new_rating
        new_average = (new_total / new_count).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
        return Rating(value=new_average, review_count=new_count)

    def remove_review(self, old_rating: Decimal) -> "Rating":
        """Remove a review and return updated rating"""
        if self.review_count <= 1:
            return Rating(value=Decimal("0.0"), review_count=0)

        new_count = self.review_count - 1
        new_total = (self.value * self.review_count) - old_rating
        new_average = (new_total / new_count).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
        return Rating(value=new_average, review_count=new_count)

    def to_stars_string(self, max_stars: int = 5) -> str:
        """Return visual star representation"""
        full_stars = int(self.value)
        half_star = 1 if (self.value - full_stars) >= Decimal("0.5") else 0
        empty_stars = max_stars - full_stars - half_star

        return "★" * full_stars + ("½" if half_star else "") + "☆" * empty_stars

    def to_dict(self) -> dict:
        return {
            "value": str(self.value),
            "review_count": self.review_count,
            "min_value": str(self.min_value),
            "max_value": str(self.max_value),
            "stars": self.stars,
            "percentage": self.percentage,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Rating":
        return cls(
            value=Decimal(data["value"]),
            review_count=data.get("review_count", 0),
            min_value=Decimal(data.get("min_value", "1.0")),
            max_value=Decimal(data.get("max_value", "5.0")),
        )

    @classmethod
    def unrated(cls) -> "Rating":
        """Create an unrated rating"""
        return cls(value=Decimal("0.0"), review_count=0)

    def __str__(self) -> str:
        if not self.is_rated:
            return "Unrated"
        return f"{self.value} ({self.review_count} reviews)"

    def __repr__(self) -> str:
        return f"Rating(value={self.value}, review_count={self.review_count})"


@dataclass(frozen=True, slots=True)
class RatingDistribution:
    """
    Distribution of ratings (1-5 stars).
    """
    counts: tuple[int, int, int, int, int]  # 1-star to 5-star counts

    def __post_init__(self) -> None:
        if len(self.counts) != 5:
            raise ValueError("Must have exactly 5 counts (1-5 stars)")
        if any(c < 0 for c in self.counts):
            raise ValueError("Counts cannot be negative")

    @property
    def total_reviews(self) -> int:
        return sum(self.counts)

    @property
    def average_rating(self) -> Decimal:
        if self.total_reviews == 0:
            return Decimal("0.0")

        weighted_sum = sum((i + 1) * count for i, count in enumerate(self.counts))
        return Decimal(str(weighted_sum / self.total_reviews)).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)

    @property
    def percentages(self) -> tuple[float, float, float, float, float]:
        if self.total_reviews == 0:
            return (0.0, 0.0, 0.0, 0.0, 0.0)
        return tuple(c / self.total_reviews * 100 for c in self.counts)

    def add_rating(self, stars: int) -> "RatingDistribution":
        """Add a rating and return new distribution"""
        if not 1 <= stars <= 5:
            raise ValueError("Stars must be 1-5")
        new_counts = list(self.counts)
        new_counts[stars - 1] += 1
        return RatingDistribution(counts=tuple(new_counts))

    def remove_rating(self, stars: int) -> "RatingDistribution":
        """Remove a rating and return new distribution"""
        if not 1 <= stars <= 5:
            raise ValueError("Stars must be 1-5")
        if self.counts[stars - 1] == 0:
            raise ValueError(f"No {stars}-star ratings to remove")
        new_counts = list(self.counts)
        new_counts[stars - 1] -= 1
        return RatingDistribution(counts=tuple(new_counts))

    def to_dict(self) -> dict:
        return {
            "counts": list(self.counts),
            "total_reviews": self.total_reviews,
            "average": str(self.average_rating),
            "percentages": list(self.percentages),
        }

    @classmethod
    def from_counts(cls, counts: list[int]) -> "RatingDistribution":
        return cls(counts=tuple(counts))

    @classmethod
    def empty(cls) -> "RatingDistribution":
        return cls(counts=(0, 0, 0, 0, 0))

    def __str__(self) -> str:
        if self.total_reviews == 0:
            return "No ratings"
        return f"{self.average_rating} ({self.total_reviews} reviews)"

    def __repr__(self) -> str:
        return f"RatingDistribution(counts={self.counts})"
