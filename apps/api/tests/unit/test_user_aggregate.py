"""
Unit tests for User Aggregate
"""
import pytest
from uuid import uuid4
from datetime import datetime, timedelta

from ai_smart_city_concierge.domain.aggregates.user_aggregate import User, UserRole, UserStatus
from ai_smart_city_concierge.domain.value_objects.address import Address


class TestUser:
    """Test User aggregate"""
    
    def test_create_user_minimal(self):
        """Test creating a user with minimal required fields"""
        user = User.create(
            email="test@example.com",
            username="testuser",
            password_hash="hashed_password_123",
        )
        
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.password_hash == "hashed_password_123"
        assert user.id is not None
        assert user.created_at is not None
        assert user.updated_at is not None
        assert user.role == UserRole.USER
        assert user.status == UserStatus.ACTIVE
        assert user.is_verified is False
        assert user.preferences == {}
    
    def test_create_user_with_all_fields(self):
        """Test creating a user with all optional fields"""
        user = User.create(
            email="admin@example.com",
            username="adminuser",
            password_hash="hashed_password_456",
            first_name="Admin",
            last_name="User",
            phone="+1-555-0123",
            date_of_birth=datetime(1990, 1, 15),
            role=UserRole.ADMIN,
            address=Address(
                street="123 Admin St",
                city="New York",
                state="NY",
                postal_code="10001",
                country="USA"
            ),
            preferences={"theme": "dark", "language": "en", "notifications": True},
        )
        
        assert user.email == "admin@example.com"
        assert user.username == "adminuser"
        assert user.first_name == "Admin"
        assert user.last_name == "User"
        assert user.phone == "+1-555-0123"
        assert user.date_of_birth == datetime(1990, 1, 15)
        assert user.role == UserRole.ADMIN
        assert user.address is not None
        assert user.preferences["theme"] == "dark"
        assert user.preferences["language"] == "en"
        assert user.preferences["notifications"] is True
    
    def test_update_profile(self):
        """Test updating user profile"""
        user = User.create(
            email="test@example.com",
            username="testuser",
            password_hash="hashed_password",
        )
        
        original_updated_at = user.updated_at
        
        user.update_profile(
            first_name="John",
            last_name="Doe",
            phone="+1-555-9999",
        )
        
        assert user.first_name == "John"
        assert user.last_name == "Doe"
        assert user.phone == "+1-555-9999"
        assert user.updated_at > original_updated_at
    
    def test_update_preferences(self):
        """Test updating user preferences"""
        user = User.create(
            email="test@example.com",
            username="testuser",
            password_hash="hashed_password",
            preferences={"theme": "light"},
        )
        
        user.update_preferences({"theme": "dark", "language": "es"})
        
        assert user.preferences["theme"] == "dark"
        assert user.preferences["language"] == "es"
        # Original preference should be preserved if not updated
        # (but in this case we replaced the whole dict)
    
    def test_verify_email(self):
        """Test email verification"""
        user = User.create(
            email="test@example.com",
            username="testuser",
            password_hash="hashed_password",
        )
        
        assert user.is_verified is False
        assert user.email_verified_at is None
        
        user.verify_email()
        
        assert user.is_verified is True
        assert user.email_verified_at is not None
        assert user.status == UserStatus.ACTIVE
    
    def test_change_password(self):
        """Test changing password"""
        user = User.create(
            email="test@example.com",
            username="testuser",
            password_hash="old_hash",
        )
        
        user.change_password("new_hashed_password")
        
        assert user.password_hash == "new_hashed_password"
        assert user.updated_at is not None
    
    def test_activate_deactivate(self):
        """Test activating and deactivating user"""
        user = User.create(
            email="test@example.com",
            username="testuser",
            password_hash="hashed_password",
        )
        
        assert user.status == UserStatus.ACTIVE
        
        user.deactivate()
        assert user.status == UserStatus.INACTIVE
        
        user.activate()
        assert user.status == UserStatus.ACTIVE
    
    def test_suspend_user(self):
        """Test suspending user"""
        user = User.create(
            email="test@example.com",
            username="testuser",
            password_hash="hashed_password",
        )
        
        user.suspend("Violation of terms")
        
        assert user.status == UserStatus.SUSPENDED
        assert user.suspension_reason == "Violation of terms"
        assert user.suspended_at is not None
    
    def test_unsuspend_user(self):
        """Test unsuspending user"""
        user = User.create(
            email="test@example.com",
            username="testuser",
            password_hash="hashed_password",
        )
        
        user.suspend("Violation of terms")
        assert user.status == UserStatus.SUSPENDED
        
        user.unsuspend()
        
        assert user.status == UserStatus.ACTIVE
        assert user.suspension_reason is None
        assert user.suspended_at is None
    
    def test_update_last_login(self):
        """Test updating last login timestamp"""
        user = User.create(
            email="test@example.com",
            username="testuser",
            password_hash="hashed_password",
        )
        
        assert user.last_login_at is None
        
        before_login = datetime.utcnow()
        user.update_last_login()
        after_login = datetime.utcnow()
        
        assert user.last_login_at is not None
        assert before_login <= user.last_login_at <= after_login
    
    def test_add_remove_favorite_poi(self):
        """Test adding and removing favorite POIs"""
        user = User.create(
            email="test@example.com",
            username="testuser",
            password_hash="hashed_password",
        )
        
        poi_id1 = uuid4()
        poi_id2 = uuid4()
        
        assert user.favorite_poi_ids == []
        
        user.add_favorite_poi(poi_id1)
        assert poi_id1 in user.favorite_poi_ids
        
        user.add_favorite_poi(poi_id2)
        assert poi_id2 in user.favorite_poi_ids
        assert len(user.favorite_poi_ids) == 2
        
        # Adding duplicate should not create duplicate
        user.add_favorite_poi(poi_id1)
        assert user.favorite_poi_ids.count(poi_id1) == 1
        
        user.remove_favorite_poi(poi_id1)
        assert poi_id1 not in user.favorite_poi_ids
        assert len(user.favorite_poi_ids) == 1
        
        # Removing non-existent should not error
        user.remove_favorite_poi(uuid4())
    
    def test_add_remove_saved_itinerary(self):
        """Test adding and removing saved itineraries"""
        user = User.create(
            email="test@example.com",
            username="testuser",
            password_hash="hashed_password",
        )
        
        itinerary_id1 = uuid4()
        itinerary_id2 = uuid4()
        
        assert user.saved_itinerary_ids == []
        
        user.add_saved_itinerary(itinerary_id1)
        assert itinerary_id1 in user.saved_itinerary_ids
        
        user.add_saved_itinerary(itinerary_id2)
        assert itinerary_id2 in user.saved_itinerary_ids
        
        user.remove_saved_itinerary(itinerary_id1)
        assert itinerary_id1 not in user.saved_itinerary_ids
    
    def test_user_equality(self):
        """Test user equality based on ID"""
        user1 = User.create(
            email="test1@example.com",
            username="testuser1",
            password_hash="hash1",
        )
        
        user2 = User.create(
            email="test2@example.com",
            username="testuser2",
            password_hash="hash2",
        )
        
        assert user1 != user2
        assert user1 == user1
        
        # Same ID should be equal
        user3 = User(
            id=user1.id,
            email="different@example.com",
            username="different",
            password_hash="different_hash",
            created_at=user1.created_at,
            updated_at=user1.updated_at,
        )
        assert user1 == user3
    
    def test_full_name_property(self):
        """Test full_name property"""
        user = User.create(
            email="test@example.com",
            username="testuser",
            password_hash="hashed_password",
            first_name="John",
            last_name="Doe",
        )
        
        assert user.full_name == "John Doe"
        
        # Test with only first name
        user2 = User.create(
            email="test2@example.com",
            username="testuser2",
            password_hash="hashed_password",
            first_name="Jane",
        )
        assert user2.full_name == "Jane"
        
        # Test with no names
        user3 = User.create(
            email="test3@example.com",
            username="testuser3",
            password_hash="hashed_password",
        )
        assert user3.full_name == "testuser3"  # Falls back to username
    
    def test_is_admin_property(self):
        """Test is_admin property"""
        user = User.create(
            email="user@example.com",
            username="user",
            password_hash="hash",
            role=UserRole.USER,
        )
        assert user.is_admin is False
        
        admin = User.create(
            email="admin@example.com",
            username="admin",
            password_hash="hash",
            role=UserRole.ADMIN,
        )
        assert admin.is_admin is True
        
        moderator = User.create(
            email="mod@example.com",
            username="mod",
            password_hash="hash",
            role=UserRole.MODERATOR,
        )
        assert moderator.is_admin is False  # Only ADMIN is admin
    
    def test_can_access_admin_panel(self):
        """Test can_access_admin_panel method"""
        user = User.create(
            email="user@example.com",
            username="user",
            password_hash="hash",
            role=UserRole.USER,
        )
        assert user.can_access_admin_panel() is False
        
        admin = User.create(
            email="admin@example.com",
            username="admin",
            password_hash="hash",
            role=UserRole.ADMIN,
        )
        assert admin.can_access_admin_panel() is True
        
        moderator = User.create(
            email="mod@example.com",
            username="mod",
            password_hash="hash",
            role=UserRole.MODERATOR,
        )
        assert moderator.can_access_admin_panel() is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])