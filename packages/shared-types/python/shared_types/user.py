"""
User Types

Type definitions for user-related entities.
"""
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from enum import Enum


class UserRole(str, Enum):
    """User roles."""
    USER = "user"
    PREMIUM = "premium"
    ADMIN = "admin"
    MODERATOR = "moderator"
    SERVICE = "service"


class UserStatus(str, Enum):
    """User account status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"
    DELETED = "deleted"


class BudgetLevel(str, Enum):
    """Budget preference levels."""
    BUDGET = "budget"
    MODERATE = "moderate"
    LUXURY = "luxury"


class AccessibilityNeed(str, Enum):
    """Accessibility needs."""
    WHEELCHAIR = "wheelchair"
    VISUAL = "visual"
    HEARING = "hearing"
    MOBILITY = "mobility"
    COGNITIVE = "cognitive"


class DietaryRestriction(str, Enum):
    """Dietary restrictions."""
    VEGETARIAN = "vegetarian"
    VEGAN = "vegan"
    GLUTEN_FREE = "gluten_free"
    HALAL = "halal"
    KOSHER = "kosher"
    NUT_FREE = "nut_free"
    DAIRY_FREE = "dairy_free"


class TransportMode(str, Enum):
    """Transportation modes."""
    WALKING = "walking"
    CYCLING = "cycling"
    PUBLIC_TRANSPORT = "public_transport"
    CAR = "car"
    TAXI = "taxi"
    RIDESHARE = "rideshare"
    SCOOTER = "scooter"


class Language(str, Enum):
    """Supported languages."""
    EN = "en"
    ES = "es"
    FR = "fr"
    DE = "de"
    IT = "it"
    PT = "pt"
    ZH = "zh"
    JA = "ja"
    KO = "ko"
    AR = "ar"
    HI = "hi"
    RU = "ru"


class Currency(str, Enum):
    """Supported currencies."""
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    JPY = "JPY"
    CNY = "CNY"
    INR = "INR"
    CAD = "CAD"
    AUD = "AUD"


class UserPreferences(BaseModel):
    """User preferences."""
    interests: List[str] = Field(default_factory=list)
    budget_level: BudgetLevel = BudgetLevel.MODERATE
    accessibility_needs: List[AccessibilityNeed] = Field(default_factory=list)
    dietary_restrictions: List[DietaryRestriction] = Field(default_factory=list)
    preferred_transport_modes: List[TransportMode] = Field(default_factory=list)
    locale: Language = Language.EN
    timezone: str = "UTC"
    currency: Currency = Currency.USD
    notifications_enabled: bool = True
    marketing_emails: bool = False


class UserProfile(BaseModel):
    """User profile information."""
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = None


class UserCreate(BaseModel):
    """User creation request."""
    email: EmailStr
    password: Optional[str] = Field(None, min_length=8, max_length=128)
    display_name: Optional[str] = None
    firebase_uid: Optional[str] = None
    google_id: Optional[str] = None
    locale: Language = Language.EN
    timezone: str = "UTC"
    interests: List[str] = Field(default_factory=list)
    budget_level: BudgetLevel = BudgetLevel.MODERATE
    accessibility_needs: List[AccessibilityNeed] = Field(default_factory=list)
    dietary_restrictions: List[DietaryRestriction] = Field(default_factory=list)
    preferred_transport_modes: List[TransportMode] = Field(default_factory=list)


class UserUpdate(BaseModel):
    """User update request."""
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    locale: Optional[Language] = None
    timezone: Optional[str] = None


class UserPreferencesUpdate(BaseModel):
    """User preferences update request."""
    interests: Optional[List[str]] = None
    budget_level: Optional[BudgetLevel] = None
    accessibility_needs: Optional[List[AccessibilityNeed]] = None
    dietary_restrictions: Optional[List[DietaryRestriction]] = None
    preferred_transport_modes: Optional[List[TransportMode]] = None


class UserResponse(BaseModel):
    """User response."""
    id: UUID
    email: EmailStr
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    role: UserRole
    status: UserStatus
    locale: Language
    timezone: str
    preferences: UserPreferences
    profile: UserProfile
    email_verified: bool
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)