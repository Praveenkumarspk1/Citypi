"""
Address Value Object
"""
import re
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Address:
    """
    Immutable address value object.
    Supports international addresses with flexible components.
    """
    street: str = ""
    street_number: str = ""
    unit: str = ""  # apartment, suite, floor, etc.
    city: str = ""
    state: str = ""  # state/province/region
    postal_code: str = ""
    country: str = ""
    neighborhood: str = ""
    district: str = ""
    subdistrict: str = ""
    landmark: str = ""

    def __post_init__(self) -> None:
        """Normalize after initialization"""
        # Strip whitespace from all fields
        for field_name in ['street', 'street_number', 'unit', 'city', 'state',
                           'postal_code', 'country', 'neighborhood', 'district',
                           'subdistrict', 'landmark']:
            value = getattr(self, field_name)
            if value:
                object.__setattr__(self, field_name, value.strip())

        # Normalize country to uppercase ISO code if 2-3 letters
        if self.country and len(self.country) <= 3:
            object.__setattr__(self, 'country', self.country.upper())

    @property
    def street_address(self) -> str:
        """Full street address (street + number + unit)"""
        parts = []
        if self.street:
            parts.append(self.street)
        if self.street_number:
            parts.append(self.street_number)
        if self.unit:
            parts.append(self.unit)
        return " ".join(parts)

    @property
    def city_state_postal(self) -> str:
        """City, state, postal code line"""
        parts = []
        if self.city:
            parts.append(self.city)
        if self.state:
            parts.append(self.state)
        if self.postal_code:
            parts.append(self.postal_code)
        return ", ".join(parts)

    @property
    def full_address(self) -> str:
        """Complete formatted address"""
        lines = []
        if self.street_address:
            lines.append(self.street_address)
        if self.neighborhood:
            lines.append(self.neighborhood)
        if self.district:
            lines.append(self.district)
        if self.subdistrict:
            lines.append(self.subdistrict)
        if self.city_state_postal:
            lines.append(self.city_state_postal)
        if self.country:
            lines.append(self.country)
        return "\n".join(lines)

    @property
    def single_line(self) -> str:
        """Single line address for display"""
        parts = []
        if self.street_address:
            parts.append(self.street_address)
        if self.neighborhood:
            parts.append(self.neighborhood)
        if self.district:
            parts.append(self.district)
        if self.subdistrict:
            parts.append(self.subdistrict)
        if self.city:
            parts.append(self.city)
        if self.state:
            parts.append(self.state)
        if self.postal_code:
            parts.append(self.postal_code)
        if self.country:
            parts.append(self.country)
        return ", ".join(parts)

    def to_dict(self) -> dict:
        """Return as dictionary"""
        return {
            "street": self.street,
            "street_number": self.street_number,
            "unit": self.unit,
            "city": self.city,
            "state": self.state,
            "postal_code": self.postal_code,
            "country": self.country,
            "neighborhood": self.neighborhood,
            "district": self.district,
            "subdistrict": self.subdistrict,
            "landmark": self.landmark,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Address":
        """Create from dictionary"""
        return cls(
            street=data.get("street", ""),
            street_number=data.get("street_number", ""),
            unit=data.get("unit", ""),
            city=data.get("city", ""),
            state=data.get("state", ""),
            postal_code=data.get("postal_code", ""),
            country=data.get("country", ""),
            neighborhood=data.get("neighborhood", ""),
            district=data.get("district", ""),
            subdistrict=data.get("subdistrict", ""),
            landmark=data.get("landmark", ""),
        )

    @classmethod
    def from_string(cls, address_str: str) -> "Address":
        """
        Parse address from string (basic parsing).
        For production, use a proper address parser like libpostal.
        """
        # Simple comma-separated parsing
        parts = [p.strip() for p in address_str.split(",")]

        address = cls()
        if len(parts) >= 1:
            object.__setattr__(address, 'street_address', parts[0])
        if len(parts) >= 2:
            object.__setattr__(address, 'city', parts[1])
        if len(parts) >= 3:
            object.__setattr__(address, 'state', parts[2])
        if len(parts) >= 4:
            object.__setattr__(address, 'postal_code', parts[3])
        if len(parts) >= 5:
            object.__setattr__(address, 'country', parts[4])

        return address

    def __str__(self) -> str:
        return self.single_line

    def __repr__(self) -> str:
        return f"Address(street='{self.street}', city='{self.city}', country='{self.country}')"


@dataclass(frozen=True, slots=True)
class PostalCode:
    """
    Postal code with validation for different countries.
    """
    code: str
    country: str = "US"

    def __post_init__(self) -> None:
        """Validate postal code format for country"""
        code = self.code.strip().upper()
        object.__setattr__(self, 'code', code)

        patterns = {
            "US": r'^\d{5}(-\d{4})?$',
            "CA": r'^[A-Z]\d[A-Z] \d[A-Z]\d$',
            "UK": r'^[A-Z]{1,2}\d[A-Z\d]? \d[A-Z]{2}$',
            "DE": r'^\d{5}$',
            "FR": r'^\d{5}$',
            "JP": r'^\d{3}-\d{4}$',
            "AU": r'^\d{4}$',
            "IN": r'^\d{6}$',
            "SG": r'^\d{6}$',
        }

        pattern = patterns.get(self.country.upper())
        if pattern and not re.match(pattern, code):
            raise ValueError(f"Invalid postal code format for {self.country}: {code}")

    def __str__(self) -> str:
        return self.code

    def __repr__(self) -> str:
        return f"PostalCode(code='{self.code}', country='{self.country}')"
