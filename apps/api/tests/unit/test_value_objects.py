"""
Unit tests for Value Objects
"""
import pytest
from datetime import time, datetime

from ai_smart_city_concierge.domain.value_objects.address import Address
from ai_smart_city_concierge.domain.value_objects.coordinates import Coordinates
from ai_smart_city_concierge.domain.value_objects.money import Money, Currency
from ai_smart_city_concierge.domain.value_objects.rating import Rating
from ai_smart_city_concierge.domain.value_objects.opening_hours import OpeningHours, DayOfWeek
from ai_smart_city_concierge.domain.value_objects.accessibility import AccessibilityInfo
from ai_smart_city_concierge.domain.value_objects.transport_mode import TransportMode
from ai_smart_city_concierge.domain.value_objects.time_range import TimeRange as TimeRangeVO


class TestAddress:
    """Test Address value object"""
    
    def test_create_address(self):
        address = Address(
            street="123 Main St",
            city="New York",
            state="NY",
            postal_code="10001",
            country="USA"
        )
        
        assert address.street == "123 Main St"
        assert address.city == "New York"
        assert address.state == "NY"
        assert address.postal_code == "10001"
        assert address.country == "USA"
    
    def test_address_equality(self):
        addr1 = Address("123 Main St", "New York", "NY", "10001", "USA")
        addr2 = Address("123 Main St", "New York", "NY", "10001", "USA")
        addr3 = Address("456 Other St", "New York", "NY", "10001", "USA")
        
        assert addr1 == addr2
        assert addr1 != addr3
    
    def test_address_str(self):
        address = Address("123 Main St", "New York", "NY", "10001", "USA")
        str_repr = str(address)
        assert "123 Main St" in str_repr
        assert "New York" in str_repr
        assert "NY" in str_repr
        assert "10001" in str_repr
        assert "USA" in str_repr
    
    def test_address_full_address(self):
        address = Address("123 Main St", "New York", "NY", "10001", "USA")
        full = address.full_address
        assert "123 Main St" in full
        assert "New York" in full
        assert "NY" in full
        assert "10001" in full
        assert "USA" in full


class TestCoordinates:
    """Test Coordinates value object"""
    
    def test_create_coordinates(self):
        coords = Coordinates(latitude=40.7128, longitude=-74.0060)
        
        assert coords.latitude == 40.7128
        assert coords.longitude == -74.0060
    
    def test_coordinates_validation_latitude(self):
        with pytest.raises(ValueError):
            Coordinates(latitude=91.0, longitude=0.0)
        
        with pytest.raises(ValueError):
            Coordinates(latitude=-91.0, longitude=0.0)
    
    def test_coordinates_validation_longitude(self):
        with pytest.raises(ValueError):
            Coordinates(latitude=0.0, longitude=181.0)
        
        with pytest.raises(ValueError):
            Coordinates(latitude=0.0, longitude=-181.0)
    
    def test_coordinates_equality(self):
        coords1 = Coordinates(40.7128, -74.0060)
        coords2 = Coordinates(40.7128, -74.0060)
        coords3 = Coordinates(40.7580, -73.9855)
        
        assert coords1 == coords2
        assert coords1 != coords3
    
    def test_distance_to(self):
        # New York City coordinates
        nyc = Coordinates(40.7128, -74.0060)
        # Los Angeles coordinates
        la = Coordinates(34.0522, -118.2437)
        
        distance = nyc.distance_to(la)
        # Approximate distance: ~3940 km
        assert 3900 < distance < 4000
    
    def test_coordinates_str(self):
        coords = Coordinates(40.7128, -74.0060)
        str_repr = str(coords)
        assert "40.7128" in str_repr
        assert "-74.006" in str_repr


class TestMoney:
    """Test Money value object"""
    
    def test_create_money(self):
        money = Money(amount=1000, currency=Currency.USD)  # $10.00
        
        assert money.amount == 1000
        assert money.currency == Currency.USD
    
    def test_money_from_float(self):
        money = Money.from_float(10.50, Currency.USD)
        assert money.amount == 1050
    
    def test_money_to_float(self):
        money = Money(amount=1050, currency=Currency.USD)
        assert money.to_float() == 10.50
    
    def test_money_addition(self):
        money1 = Money(amount=1000, currency=Currency.USD)
        money2 = Money(amount=500, currency=Currency.USD)
        
        result = money1 + money2
        assert result.amount == 1500
        assert result.currency == Currency.USD
    
    def test_money_addition_different_currency_raises(self):
        money1 = Money(amount=1000, currency=Currency.USD)
        money2 = Money(amount=500, currency=Currency.EUR)
        
        with pytest.raises(ValueError):
            money1 + money2
    
    def test_money_subtraction(self):
        money1 = Money(amount=1000, currency=Currency.USD)
        money2 = Money(amount=300, currency=Currency.USD)
        
        result = money1 - money2
        assert result.amount == 700
    
    def test_money_multiplication(self):
        money = Money(amount=1000, currency=Currency.USD)
        
        result = money * 2
        assert result.amount == 2000
        
        result = money * 1.5
        assert result.amount == 1500
    
    def test_money_comparison(self):
        money1 = Money(amount=1000, currency=Currency.USD)
        money2 = Money(amount=500, currency=Currency.USD)
        money3 = Money(amount=1000, currency=Currency.USD)
        
        assert money1 > money2
        assert money2 < money1
        assert money1 == money3
        assert money1 >= money3
        assert money2 <= money1
    
    def test_money_str(self):
        money = Money(amount=1050, currency=Currency.USD)
        assert str(money) == "$10.50"
        
        money_eur = Money(amount=1000, currency=Currency.EUR)
        assert str(money_eur) == "€10.00"


class TestRating:
    """Test Rating value object"""
    
    def test_create_rating(self):
        rating = Rating(value=4.5, count=100)
        
        assert rating.value == 4.5
        assert rating.count == 100
    
    def test_rating_validation_value(self):
        with pytest.raises(ValueError):
            Rating(value=6.0, count=10)
        
        with pytest.raises(ValueError):
            Rating(value=-0.5, count=10)
    
    def test_rating_validation_count(self):
        with pytest.raises(ValueError):
            Rating(value=4.0, count=-1)
    
    def test_rating_equality(self):
        rating1 = Rating(4.5, 100)
        rating2 = Rating(4.5, 100)
        rating3 = Rating(4.0, 100)
        
        assert rating1 == rating2
        assert rating1 != rating3
    
    def test_rating_str(self):
        rating = Rating(4.5, 100)
        assert str(rating) == "4.5 (100 reviews)"


class TestOpeningHours:
    """Test OpeningHours value object"""
    
    def test_create_opening_hours(self):
        hours = OpeningHours(
            weekly_schedule={
                DayOfWeek.MONDAY: [TimeRange(time(9, 0), time(17, 0))],
                DayOfWeek.TUESDAY: [TimeRange(time(9, 0), time(17, 0))],
            }
        )
        
        assert DayOfWeek.MONDAY in hours.weekly_schedule
        assert DayOfWeek.TUESDAY in hours.weekly_schedule
        assert len(hours.weekly_schedule[DayOfWeek.MONDAY]) == 1
    
    def test_is_open_at(self):
        hours = OpeningHours(
            weekly_schedule={
                DayOfWeek.MONDAY: [TimeRange(time(9, 0), time(17, 0))],
            }
        )
        
        # Monday 10:00 - should be open
        monday_10am = datetime(2024, 1, 1, 10, 0)  # Monday
        assert hours.is_open_at(monday_10am) is True
        
        # Monday 18:00 - should be closed
        monday_6pm = datetime(2024, 1, 1, 18, 0)
        assert hours.is_open_at(monday_6pm) is False
        
        # Tuesday - should be closed (no hours defined)
        tuesday_10am = datetime(2024, 1, 2, 10, 0)
        assert hours.is_open_at(tuesday_10am) is False
    
    def test_is_open_now(self):
        hours = OpeningHours(
            weekly_schedule={
                DayOfWeek.MONDAY: [TimeRange(time(0, 0), time(23, 59))],
            }
        )
        
        # This will depend on current day/time, so just test it doesn't error
        result = hours.is_open_now()
        assert isinstance(result, bool)
    
    def test_get_today_hours(self):
        hours = OpeningHours(
            weekly_schedule={
                DayOfWeek.MONDAY: [TimeRange(time(9, 0), time(17, 0))],
            }
        )
        
        # Monday
        monday = datetime(2024, 1, 1)
        today_hours = hours.get_today_hours(monday)
        assert len(today_hours) == 1
        assert today_hours[0].start == time(9, 0)
        assert today_hours[0].end == time(17, 0)
        
        # Tuesday (no hours)
        tuesday = datetime(2024, 1, 2)
        today_hours = hours.get_today_hours(tuesday)
        assert today_hours == []
    
    def test_opening_hours_equality(self):
        hours1 = OpeningHours(
            weekly_schedule={
                DayOfWeek.MONDAY: [TimeRange(time(9, 0), time(17, 0))],
            }
        )
        hours2 = OpeningHours(
            weekly_schedule={
                DayOfWeek.MONDAY: [TimeRange(time(9, 0), time(17, 0))],
            }
        )
        hours3 = OpeningHours(
            weekly_schedule={
                DayOfWeek.TUESDAY: [TimeRange(time(9, 0), time(17, 0))],
            }
        )
        
        assert hours1 == hours2
        assert hours1 != hours3


class TestAccessibilityInfo:
    """Test AccessibilityInfo value object"""
    
    def test_create_accessibility(self):
        accessibility = AccessibilityInfo(
            wheelchair_accessible=True,
            wheelchair_accessible_entrance=True,
            wheelchair_accessible_parking=False,
            wheelchair_accessible_restroom=True,
            hearing_loop_available=False,
            visual_aids_available=True,
        )
        
        assert accessibility.wheelchair_accessible is True
        assert accessibility.wheelchair_accessible_entrance is True
        assert accessibility.wheelchair_accessible_parking is False
        assert accessibility.wheelchair_accessible_restroom is True
        assert accessibility.hearing_loop_available is False
        assert accessibility.visual_aids_available is True
    
    def test_accessibility_defaults(self):
        accessibility = AccessibilityInfo()
        
        assert accessibility.wheelchair_accessible is False
        assert accessibility.wheelchair_accessible_entrance is False
        assert accessibility.wheelchair_accessible_parking is False
        assert accessibility.wheelchair_accessible_restroom is False
        assert accessibility.hearing_loop_available is False
        assert accessibility.visual_aids_available is False
    
    def test_accessibility_equality(self):
        acc1 = AccessibilityInfo(wheelchair_accessible=True)
        acc2 = AccessibilityInfo(wheelchair_accessible=True)
        acc3 = AccessibilityInfo(wheelchair_accessible=False)
        
        assert acc1 == acc2
        assert acc1 != acc3


class TestTransportMode:
    """Test TransportMode value object"""
    
    def test_transport_modes(self):
        assert TransportMode.WALKING.value == "walking"
        assert TransportMode.CYCLING.value == "cycling"
        assert TransportMode.DRIVING.value == "driving"
        assert TransportMode.TRANSIT.value == "transit"
        assert TransportMode.RIDESHARE.value == "rideshare"
    
    def test_transport_mode_from_string(self):
        assert TransportMode.from_string("walking") == TransportMode.WALKING
        assert TransportMode.from_string("cycling") == TransportMode.CYCLING
        assert TransportMode.from_string("driving") == TransportMode.DRIVING
        assert TransportMode.from_string("transit") == TransportMode.TRANSIT
        assert TransportMode.from_string("rideshare") == TransportMode.RIDESHARE
        
        with pytest.raises(ValueError):
            TransportMode.from_string("invalid")
    
    def test_transport_mode_speed_kmh(self):
        assert TransportMode.WALKING.average_speed_kmh == 5
        assert TransportMode.CYCLING.average_speed_kmh == 15
        assert TransportMode.DRIVING.average_speed_kmh == 40
        assert TransportMode.TRANSIT.average_speed_kmh == 25
        assert TransportMode.RIDESHARE.average_speed_kmh == 35


class TestTimeRange:
    """Test TimeRange value object"""
    
    def test_create_time_range(self):
        tr = TimeRangeVO(start=time(9, 0), end=time(17, 0))
        
        assert tr.start == time(9, 0)
        assert tr.end == time(17, 0)
    
    def test_time_range_validation(self):
        with pytest.raises(ValueError):
            TimeRangeVO(start=time(17, 0), end=time(9, 0))  # End before start
    
    def test_contains(self):
        tr = TimeRangeVO(start=time(9, 0), end=time(17, 0))
        
        assert tr.contains(time(10, 0)) is True
        assert tr.contains(time(9, 0)) is True  # Inclusive start
        assert tr.contains(time(17, 0)) is False  # Exclusive end
        assert tr.contains(time(8, 0)) is False
        assert tr.contains(time(18, 0)) is False
    
    def test_overlaps(self):
        tr1 = TimeRangeVO(start=time(9, 0), end=time(17, 0))
        tr2 = TimeRangeVO(start=time(12, 0), end=time(20, 0))
        tr3 = TimeRangeVO(start=time(18, 0), end=time(22, 0))
        
        assert tr1.overlaps(tr2) is True
        assert tr1.overlaps(tr3) is False
    
    def test_duration_minutes(self):
        tr = TimeRangeVO(start=time(9, 0), end=time(17, 0))
        assert tr.duration_minutes == 480  # 8 hours
        
        tr2 = TimeRangeVO(start=time(9, 30), end=time(10, 15))
        assert tr2.duration_minutes == 45
    
    def test_time_range_equality(self):
        tr1 = TimeRangeVO(time(9, 0), time(17, 0))
        tr2 = TimeRangeVO(time(9, 0), time(17, 0))
        tr3 = TimeRangeVO(time(10, 0), time(18, 0))
        
        assert tr1 == tr2
        assert tr1 != tr3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])