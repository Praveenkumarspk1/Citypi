"""
Money Value Object
"""
import re
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal


@dataclass(frozen=True, slots=True)
class Money:
    """
    Immutable money value with currency.
    Uses Decimal for precise arithmetic.
    """
    amount: Decimal
    currency: str = "USD"

    def __post_init__(self) -> None:
        """Validate and normalize after initialization"""
        if not isinstance(self.amount, Decimal):
            object.__setattr__(self, 'amount', Decimal(str(self.amount)))

        # Round to 2 decimal places for most currencies
        if self.currency in ("USD", "EUR", "GBP", "INR", "JPY"):
            object.__setattr__(self, 'amount', self.amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

        # Validate currency code (ISO 4217)
        if not re.match(r'^[A-Z]{3}$', self.currency):
            raise ValueError(f"Invalid currency code: {self.currency}. Must be 3-letter ISO 4217 code.")

        if self.amount < 0:
            raise ValueError("Money amount cannot be negative")

    def __add__(self, other: "Money") -> "Money":
        """Add two money values (must be same currency)"""
        if not isinstance(other, Money):
            return NotImplemented
        if self.currency != other.currency:
            raise ValueError(f"Cannot add {self.currency} and {other.currency}")
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: "Money") -> "Money":
        """Subtract two money values (must be same currency)"""
        if not isinstance(other, Money):
            return NotImplemented
        if self.currency != other.currency:
            raise ValueError(f"Cannot subtract {self.currency} and {other.currency}")
        result = self.amount - other.amount
        if result < 0:
            raise ValueError("Result cannot be negative")
        return Money(result, self.currency)

    def __mul__(self, multiplier: int | float | Decimal) -> "Money":
        """Multiply money by a number"""
        if not isinstance(multiplier, (int, float, Decimal)):
            return NotImplemented
        return Money(self.amount * Decimal(str(multiplier)), self.currency)

    def __truediv__(self, divisor: int | float | Decimal) -> "Money":
        """Divide money by a number"""
        if not isinstance(divisor, (int, float, Decimal)):
            return NotImplemented
        if divisor == 0:
            raise ZeroDivisionError("Cannot divide by zero")
        return Money(self.amount / Decimal(str(divisor)), self.currency)

    def __lt__(self, other: "Money") -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        if self.currency != other.currency:
            raise ValueError(f"Cannot compare {self.currency} and {other.currency}")
        return self.amount < other.amount

    def __le__(self, other: "Money") -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        if self.currency != other.currency:
            raise ValueError(f"Cannot compare {self.currency} and {other.currency}")
        return self.amount <= other.amount

    def __gt__(self, other: "Money") -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        if self.currency != other.currency:
            raise ValueError(f"Cannot compare {self.currency} and {other.currency}")
        return self.amount > other.amount

    def __ge__(self, other: "Money") -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        if self.currency != other.currency:
            raise ValueError(f"Cannot compare {self.currency} and {other.currency}")
        return self.amount >= other.amount

    def to_dict(self) -> dict:
        """Return as dictionary"""
        return {
            "amount": str(self.amount),
            "currency": self.currency
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Money":
        """Create from dictionary"""
        return cls(
            amount=Decimal(str(data.get("amount", "0"))),
            currency=data.get("currency", "USD")
        )

    @classmethod
    def zero(cls, currency: str = "USD") -> "Money":
        """Create zero money"""
        return cls(Decimal("0"), currency)

    def __str__(self) -> str:
        return f"{self.currency} {self.amount:.2f}"

    def __repr__(self) -> str:
        return f"Money(amount={self.amount}, currency='{self.currency}')"


# Common currency constants
class Currency:
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    INR = "INR"
    JPY = "JPY"
    CNY = "CNY"
    AUD = "AUD"
    CAD = "CAD"
    CHF = "CHF"
    SGD = "SGD"
