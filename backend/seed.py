from datetime import datetime, timedelta, UTC

from backend.db.database import SessionLocal
from backend.models import User, UserRole, UserStatus, UserProfile, Event, EventStatus
from backend.security import hash_password


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




def _seed_user_profiles(db):
    profiles = [
        {
            "email": "user@test.com",
            "nick": "Maja",
            "miasto": "Warszawa",
            "bio": "Lubie kawe i spacery",
            "zainteresowania_json": '["kawa","joga","muzyka"]',
        },
        {
            "email": "user2@test.com",
            "nick": "Kasia",
            "miasto": "Warszawa",
            "bio": "Lubie psy i fotografie",
            "zainteresowania_json": '["psy","fotografia","spacer"]',
        },
    ]

    for item in profiles:
        user = db.query(User).filter(User.email == item["email"]).first()
        if not user:
            print(f'SEED PROFILE: user not found: {item["email"]}')
            continue

        existing = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
        if existing:
            print(f'SEED PROFILE: already present: {item["email"]}')
            continue

        profile = UserProfile(
            user_id=user.id,
            nick=item["nick"],
            miasto=item["miasto"],
            bio=item["bio"],
            zainteresowania_json=item["zainteresowania_json"],
        )

        db.add(profile)
        print(f'SEED PROFILE: added: {item["email"]}')


def _seed_events(db):
    if db.query(Event).count() > 0:
        print("SEED EVENTS: already present")
        return

    partner = db.query(User).filter(User.email == "partner@test.com").first()
    if not partner:
        print("SEED EVENTS: partner not found")
        return

    now = datetime.now(UTC)

    e1 = Event(
        partner_user_id=partner.id,
        title="City walk",
        description="Walk and coffee",
        city="Warszawa",
        start_at=now + timedelta(days=2),
        end_at=now + timedelta(days=2, hours=2),
        capacity=20,
        status=EventStatus.PUBLISHED.value,
        pricing_type="free",
    )

    e2 = Event(
        partner_user_id=partner.id,
        title="Yoga in the park",
        description="Morning yoga for beginners",
        city="Warszawa",
        start_at=now + timedelta(days=5),
        end_at=now + timedelta(days=5, hours=1),
        capacity=15,
        status=EventStatus.PUBLISHED.value,
        pricing_type="free",
    )

    db.add_all([e1, e2])
    print("SEED EVENTS: added")

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
            email="user2@test.com",
            password="test12345",
            role=UserRole.USER,
        )

        _get_or_create_or_fix_user(
            db,
            email="partner@test.com",
            password="test12345",
            role=UserRole.PARTNER,
        )

        _seed_events(db)
        _seed_user_profiles(db)

        db.commit()
        print("SEED DONE")
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
