from db.database import SessionLocal
from models import User, UserRole, UserStatus
from security import hash_password


def _looks_like_bcrypt(hash_value: str | None) -> bool:
    # bcrypt zwykle zaczyna się od $2a$ / $2b$ / $2y$
    return bool(hash_value) and hash_value.startswith("$2")


def _get_or_create_or_fix_user(
    db,
    *,
    email: str,
    password: str,
    role: UserRole,
) -> None:
    existing = db.query(User).filter(User.email == email).first()

    if not existing:
        user = User(
            email=email,
            password_hash=hash_password(password),
            role=role.value,
            status=UserStatus.ACTIVE.value,
        )
        db.add(user)
        print(f"SEED ADD: {email}")
        return

    changed = False

    # role/status poprawiamy „do porządku”
    if existing.role != role.value:
        existing.role = role.value
        changed = True

    if existing.status != UserStatus.ACTIVE.value:
        existing.status = UserStatus.ACTIVE.value
        changed = True

    # jeśli hash nie wygląda jak bcrypt (np. TEST_HASH), to go naprawiamy
    if not _looks_like_bcrypt(existing.password_hash):
        existing.password_hash = hash_password(password)
        changed = True
        print(f"SEED FIX PASSWORD: {email}")

    if changed:
        db.add(existing)
        print(f"SEED UPDATE: {email}")
    else:
        print(f"SEED OK: {email}")


def run_seed() -> None:
    db = SessionLocal()
    try:
        _get_or_create_or_fix_user(
            db,
            email="admin@usly.dev",
            password="admin12345",
            role=UserRole.ADMIN,
        )

        _get_or_create_or_fix_user(
            db,
            email="user@test.com",
            password="test12345",
            role=UserRole.USER,
        )

        _get_or_create_or_fix_user(
            db,
            email="partner@test.com",
            password="test12345",
            role=UserRole.PARTNER,
        )

        db.commit()
        print("SEED DONE")
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
