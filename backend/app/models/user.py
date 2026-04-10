"""User model — demonstrates Encapsulation and Factory Method pattern.

Encapsulation: private attributes with read-only property accessors.
Factory Method: `from_db_row()` creates User instances from database records.
"""

from datetime import datetime
from typing import Optional


class User:
    """Domain model representing an application user.

    All attributes are private (_prefixed) and exposed through
    read-only properties, preventing uncontrolled mutation.
    """

    def __init__(
        self,
        user_id: str,
        username: str,
        email: Optional[str] = None,
        name: str = "",
        surname: str = "",
        avatar_url: str = "",
        subscription: str = "free",
        hobbies: Optional[list[str]] = None,
        created_at: Optional[datetime] = None,
    ) -> None:
        self._id = user_id
        self._username = username
        self._email = email
        self._name = name
        self._surname = surname
        self._avatar_url = avatar_url
        self._subscription = subscription
        self._hobbies = list(hobbies or [])
        self._created_at = created_at

    # --- Properties (Encapsulation) ---

    @property
    def id(self) -> str:
        return self._id

    @property
    def username(self) -> str:
        return self._username

    @property
    def email(self) -> Optional[str]:
        return self._email

    @property
    def name(self) -> str:
        return self._name

    @property
    def surname(self) -> str:
        return self._surname

    @property
    def avatar_url(self) -> str:
        return self._avatar_url

    @property
    def subscription(self) -> str:
        return self._subscription

    @property
    def hobbies(self) -> list[str]:
        return list(self._hobbies)

    @property
    def created_at(self) -> Optional[datetime]:
        return self._created_at

    # --- Factory Method ---

    @classmethod
    def from_db_row(cls, row) -> "User":
        """Factory Method: create a User from an asyncpg Record."""
        return cls(
            user_id=str(row["id"]),
            username=row["username"],
            email=row.get("email"),
            name=row.get("name") or "",
            surname=row.get("surname") or "",
            avatar_url=row.get("avatar_url") or "",
            subscription=row.get("subscription") or "free",
            hobbies=list(row.get("hobbies") or []),
            created_at=row.get("created_at"),
        )

    # --- Serialisation ---

    def to_dict(self) -> dict:
        """Convert to a JSON-safe dictionary for API responses."""
        return {
            "id": self._id,
            "username": self._username,
            "email": self._email,
            "name": self._name,
            "surname": self._surname,
            "avatar_url": self._avatar_url,
            "subscription": self._subscription,
            "hobbies": self.hobbies,
            "created_at": (
                self._created_at.isoformat() if self._created_at else None
            ),
        }

    def __repr__(self) -> str:
        return f"User(id={self._id!r}, username={self._username!r})"