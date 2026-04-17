"""Tests for PasswordHasher and TokenManager.

Run:  python -m unittest tests.test_auth -v
"""

import unittest
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException

from app.models.auth_service import PasswordHasher, TokenManager


class TestPasswordHasher(unittest.TestCase):
    """Pure logic — no DB, no async."""

    def setUp(self):
        self.hasher = PasswordHasher()

    def test_hash_returns_string(self):
        hashed = self.hasher.hash("mypassword")
        self.assertIsInstance(hashed, str)

    def test_hash_is_not_plaintext(self):
        hashed = self.hasher.hash("mypassword")
        self.assertNotEqual(hashed, "mypassword")

    def test_verify_correct_password(self):
        hashed = self.hasher.hash("secret123")
        self.assertTrue(self.hasher.verify("secret123", hashed))

    def test_verify_wrong_password(self):
        hashed = self.hasher.hash("secret123")
        self.assertFalse(self.hasher.verify("wrongpass", hashed))

    def test_different_hashes_for_same_password(self):
        """bcrypt uses random salt — same input produces different hashes."""
        h1 = self.hasher.hash("same")
        h2 = self.hasher.hash("same")
        self.assertNotEqual(h1, h2)

    def test_both_still_verify(self):
        h1 = self.hasher.hash("same")
        h2 = self.hasher.hash("same")
        self.assertTrue(self.hasher.verify("same", h1))
        self.assertTrue(self.hasher.verify("same", h2))

    def test_empty_password(self):
        hashed = self.hasher.hash("")
        self.assertTrue(self.hasher.verify("", hashed))
        self.assertFalse(self.hasher.verify("notempty", hashed))


class TestTokenManager(unittest.TestCase):
    """JWT create / decode. Uses a test secret so it's self-contained."""

    def setUp(self):
        self.tm = TokenManager(
            secret="test-secret-key",
            algorithm="HS256",
            expire_minutes=30,
        )

    def test_create_returns_string(self):
        token = self.tm.create("user-id-1", "alice")
        self.assertIsInstance(token, str)

    def test_decode_roundtrip(self):
        """Create a token then decode it — payload should match."""
        token = self.tm.create("user-id-1", "alice")
        payload = self.tm.decode(token)
        self.assertEqual(payload["sub"], "user-id-1")
        self.assertEqual(payload["username"], "alice")

    def test_decode_contains_exp(self):
        token = self.tm.create("uid", "bob")
        payload = self.tm.decode(token)
        self.assertIn("exp", payload)

    def test_expired_token_raises(self):
        """Token with 0 minute expiry should fail immediately."""
        tm = TokenManager(
            secret="test-secret-key",
            algorithm="HS256",
            expire_minutes=0,
        )
        token = tm.create("uid", "bob")
        # The token is created with exp = now + 0 minutes = now,
        # which is already at or past expiry
        with self.assertRaises(HTTPException) as ctx:
            tm.decode(token)
        self.assertEqual(ctx.exception.status_code, 401)
        self.assertIn("expired", ctx.exception.detail.lower())

    def test_invalid_token_raises(self):
        with self.assertRaises(HTTPException) as ctx:
            self.tm.decode("not.a.real.token")
        self.assertEqual(ctx.exception.status_code, 401)
        self.assertIn("invalid", ctx.exception.detail.lower())

    def test_wrong_secret_raises(self):
        """Token signed with one secret can't be decoded with another."""
        token = self.tm.create("uid", "carol")
        other_tm = TokenManager(
            secret="different-secret",
            algorithm="HS256",
            expire_minutes=30,
        )
        with self.assertRaises(HTTPException):
            other_tm.decode(token)

    def test_different_users_get_different_tokens(self):
        t1 = self.tm.create("uid-1", "alice")
        t2 = self.tm.create("uid-2", "bob")
        self.assertNotEqual(t1, t2)


if __name__ == "__main__":
    unittest.main()
