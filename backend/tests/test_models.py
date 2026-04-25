"""Tests for the User model.

Covers: Encapsulation (private attrs + properties), Factory Method
(from_db_row), and serialisation (to_dict).

Run:  python -m unittest tests.test_models -v
"""

import unittest
from datetime import datetime, timezone

from app.models.user import User


class TestUserCreation(unittest.TestCase):
    """Basic construction and property access."""

    def setUp(self):
        self.user = User(
            user_id="abc-123",
            username="testuser",
            email="test@example.com",
            name="John",
            surname="Doe",
            avatar_url="/avatars/john.png",
            subscription="premium",
            hobbies=["coding", "chess"],
            created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )

    def test_properties_return_correct_values(self):
        self.assertEqual(self.user.id, "abc-123")
        self.assertEqual(self.user.username, "testuser")
        self.assertEqual(self.user.email, "test@example.com")
        self.assertEqual(self.user.name, "John")
        self.assertEqual(self.user.surname, "Doe")
        self.assertEqual(self.user.avatar_url, "/avatars/john.png")
        self.assertEqual(self.user.subscription, "premium")
        self.assertEqual(self.user.hobbies, ["coding", "chess"])

    def test_defaults(self):
        """Minimal constructor — optional fields get safe defaults."""
        user = User(user_id="x", username="minimal")
        self.assertIsNone(user.email)
        self.assertEqual(user.name, "")
        self.assertEqual(user.surname, "")
        self.assertEqual(user.avatar_url, "")
        self.assertEqual(user.subscription, "free")
        self.assertEqual(user.hobbies, [])
        self.assertIsNone(user.created_at)

    def test_repr(self):
        self.assertIn("testuser", repr(self.user))
        self.assertIn("abc-123", repr(self.user))


class TestUserEncapsulation(unittest.TestCase):
    """Encapsulation: attributes are private, properties are read-only."""

    def setUp(self):
        self.user = User(user_id="1", username="enc_test")

    def test_cannot_set_property(self):
        with self.assertRaises(AttributeError):
            self.user.username = "hacked"

    def test_cannot_set_id(self):
        with self.assertRaises(AttributeError):
            self.user.id = "new-id"

    def test_hobbies_returns_copy(self):
        """Mutating the returned list must NOT affect the internal state."""
        user = User(user_id="1", username="u", hobbies=["a", "b"])
        hobbies = user.hobbies
        hobbies.append("c")
        self.assertEqual(user.hobbies, ["a", "b"])


class TestUserFactoryMethod(unittest.TestCase):
    """Factory Method: User.from_db_row()."""

    def test_from_db_row_full(self):
        row = {
            "id": "uuid-456",
            "username": "dbuser",
            "email": "db@example.com",
            "name": "Jane",
            "surname": "Smith",
            "avatar_url": "/a.png",
            "subscription": "pro",
            "hobbies": ["reading"],
            "created_at": datetime(2026, 3, 15, tzinfo=timezone.utc),
        }
        user = User.from_db_row(row)
        self.assertEqual(user.id, "uuid-456")
        self.assertEqual(user.username, "dbuser")
        self.assertEqual(user.email, "db@example.com")
        self.assertEqual(user.hobbies, ["reading"])

    def test_from_db_row_missing_optional_fields(self):
        """DB row might have None for optional columns."""
        row = {
            "id": "uuid-789",
            "username": "sparse",
            "email": None,
            "name": None,
            "surname": None,
            "avatar_url": None,
            "subscription": None,
            "hobbies": None,
            "created_at": None,
        }
        user = User.from_db_row(row)
        self.assertEqual(user.name, "")
        self.assertEqual(user.subscription, "free")
        self.assertEqual(user.hobbies, [])


class TestUserToDict(unittest.TestCase):
    """Serialisation: to_dict() returns a JSON-safe dictionary."""

    def test_to_dict_keys(self):
        user = User(user_id="1", username="u")
        d = user.to_dict()
        expected_keys = {
            "id", "username", "email", "name", "surname",
            "avatar_url", "subscription", "is_admin", "hobbies", "created_at",
        }
        self.assertEqual(set(d.keys()), expected_keys)

    def test_to_dict_values(self):
        ts = datetime(2026, 6, 1, tzinfo=timezone.utc)
        user = User(user_id="1", username="u", created_at=ts)
        d = user.to_dict()
        self.assertEqual(d["id"], "1")
        self.assertEqual(d["created_at"], ts.isoformat())

    def test_to_dict_none_created_at(self):
        user = User(user_id="1", username="u")
        self.assertIsNone(user.to_dict()["created_at"])


if __name__ == "__main__":
    unittest.main()
