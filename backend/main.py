# -*- coding: utf-8 -*-

import os
from dotenv import load_dotenv

load_dotenv()

import json


from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import List, Optional
from uuid import uuid4

from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    Request,
    status,
    UploadFile,
    File,
    Query,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr, Field

from api_response import ok, fail
from error_codes import ErrorCode
from db.database import SessionLocal
from models import (
    User,
    UserProfile,
    PartnerProfile,
    Event,
    AuditLog,
    EventSignup,
    UserStatus,
)

from schemas import EventCreate, EventUpdate, EventOut

from security import (
    hash_password,
    verify_password,
    get_current_user,
    require_role,
    create_access_token,
)

app = FastAPI()

# Healthcheck (for deploy / monitoring)
@app.get("/healthz")
def healthz():
    return {"status": "ok"}


# =========================
# MVP: JOIN EVENT
# =========================
@app.post("/events/{event_id}/join")
def join_event(
    event_id: int,
    request: Request,
    current_user: User = Depends(require_role("user")),
):
    db = SessionLocal()
    try:
        # 1) event musi istnieć
        event = db.query(Event).filter(Event.id == event_id).first()

        if not event:
            raise HTTPException(status_code=404, detail="EVENT_NOT_FOUND")

        # 2) musi być published
        if event.status != "published":
            raise HTTPException(status_code=409, detail="EVENT_NOT_PUBLISHED")

        # 3) capacity (jeśli ustawione)
        if event.capacity is not None:
            current_count = (
                db.query(EventSignup)
                .filter(EventSignup.event_id == event_id)
                .count()
            )

            if current_count >= event.capacity:
                raise HTTPException(status_code=409, detail="EVENT_FULL")

        # 4) czy user już zapisany
        existing = (
            db.query(EventSignup)
            .filter(
                EventSignup.event_id == event_id,
                EventSignup.user_id == current_user.id,
            )
            .first()
        )

        if existing:
            raise HTTPException(status_code=409, detail="ALREADY_JOINED")

        # 5) zapis
        signup = EventSignup(
            event_id=event_id,
            user_id=current_user.id,
        )

        db.add(signup)
        db.commit()

        # 6) audit
        _audit(
            db,
            action="EVENT_JOIN",
            request=request,
            user_id=current_user.id,
            details=f"event_id={event_id}",
        )

        return ok({"joined": True, "event_id": event_id})

    finally:
        db.close()
# =========================
# MVP: LEAVE EVENT
# =========================
@app.delete("/events/{event_id}/join")
def leave_event(
    event_id: int,
    request: Request,
    current_user: User = Depends(require_role("user")),
):
    db = SessionLocal()
    try:
        # 1) event musi istnieć
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise HTTPException(status_code=404, detail="EVENT_NOT_FOUND")

        # 2) tylko dla published (trzymamy spójnie z join)
        if event.status != "published":
            raise HTTPException(status_code=409, detail="EVENT_NOT_PUBLISHED")

        # 3) musi istnieć zapis
        signup = (
            db.query(EventSignup)
            .filter(
                EventSignup.event_id == event_id,
                EventSignup.user_id == current_user.id,
            )
            .first()
        )
        if not signup:
            raise HTTPException(status_code=409, detail="NOT_JOINED")

        # 4) usuń zapis
        db.delete(signup)
        db.commit()

        # 5) audit
        _audit(
            db,
            action="EVENT_LEAVE",
            request=request,
            user_id=current_user.id,
            details=f"event_id={event_id}",
        )

        return ok({"left": True, "event_id": event_id})

    finally:
        db.close()


# =========================
# Static uploads
# =========================
UPLOADS_DIR = Path("uploads")
UPLOADS_DIR.mkdir(exist_ok=True)
app.mount("/uploads/static", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")


# =========================
# Exceptions
# =========================
@dataclass
class ApiException(Exception):
    status_code: int
    code: ErrorCode
    message: str | None = None
    details: object | None = None


@app.exception_handler(ApiException)
async def api_exception_handler(request: Request, exc: ApiException):
    return JSONResponse(
        status_code=exc.status_code,
        content=fail(code=exc.code, message=exc.message, details=exc.details),
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content=fail(
            code=ErrorCode.INTERNAL_ERROR,
            message="Wystąpił nieoczekiwany błąd serwera",
        ),
    )


# =========================
# AUDIT HELPERS
# =========================
def _get_ip(request: Request) -> str | None:
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else None


def _get_user_agent(request: Request) -> str | None:
    return request.headers.get("user-agent")


def _audit(db, *, action: str, request: Request, user_id: int | None, details: str | None = None) -> None:
    log = AuditLog(
        user_id=user_id,
        action=action,
        ip=_get_ip(request),
        user_agent=_get_user_agent(request),
        details=details,
    )
    db.add(log)
    db.commit()


# =========================
# CORS
# =========================
allowed_origins = os.getenv(
    "CORS_ALLOWED_ORIGINS",
    ""
).split(",")
allowed_origins = [o.strip() for o in allowed_origins if o.strip()]


app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return ok({"status": "ok"})


@app.get("/crash-test")
def crash_test():
    1 / 0


def _is_at_least_16(dob: date) -> bool:
    today = date.today()
    years = today.year - dob.year
    if (today.month, today.day) < (dob.month, dob.day):
        years -= 1
    return years >= 16


# =========================
# AUTH – REGISTER
# =========================
# UWAGA: RegisterRequest/RegisterResponse muszą istnieć w Twoim projekcie.
# Jeśli masz je w innym pliku, zmień import tutaj.
from schemas import RegisterRequest, RegisterResponse  # <- jeśli masz gdzie indziej, podmień


@app.post("/auth/register", response_model=RegisterResponse)
def register(payload: RegisterRequest):
    # 16+
    if not _is_at_least_16(payload.dob):
        raise ApiException(status_code=403, code=ErrorCode.AGE_TOO_LOW)

    # LEGAL – wymagane zgody
    if not payload.accept_terms:
        raise ApiException(status_code=422, code=ErrorCode.TERMS_REQUIRED)

    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == str(payload.email)).first()
        if existing:
            raise ApiException(status_code=409, code=ErrorCode.EMAIL_ALREADY_EXISTS)

        # UWAGA: UserRole i UserStatus muszą istnieć w Twoim projekcie.
 

        role_value = UserRole.PARTNER.value if payload.role == "partner" else UserRole.USER.value

        user = User(
            email=str(payload.email),
            password_hash=hash_password(payload.password),
            dob=payload.dob,
            terms_accepted_at=datetime.utcnow(),
            terms_version="v1",
            privacy_version="v1",
            role=role_value,
            status=UserStatus.ACTIVE.value,
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        return ok(
            RegisterResponse(
                id=user.id,
                email=user.email,
                role=user.role,
                status=user.status,
            ).model_dump()
        )
    finally:
        db.close()


# =========================
# LEGAL – TERMS v1
# =========================
@app.get("/legal/terms")
def get_terms():
    return ok(
        {
            "type": "terms",
            "version": "v1",
            "content": (
                "Regulamin USLY v1\n\n"
                "1. Serwis przeznaczony jest wyłącznie dla osób, które ukończyły 16 lat.\n"
                "2. Użytkownik zobowiązuje się do podawania prawdziwych danych.\n"
                "3. Szczegółowe warunki korzystania zostaną uzupełnione.\n"
            ),
        }
    )


# =========================
# LEGAL – PRIVACY v1
# =========================
@app.get("/legal/privacy")
def get_privacy():
    return ok(
        {
            "type": "privacy",
            "version": "v1",
            "content": (
                "Polityka prywatności USLY v1\n\n"
                "1. Administratorem danych jest USLY (dane administratora do uzupełnienia).\n"
                "2. Przetwarzamy dane w celu założenia i obsługi konta oraz świadczenia usług.\n"
                "3. Podstawy prawne, odbiorcy danych, okres przechowywania i prawa użytkownika "
                "zostaną doprecyzowane w wersji produkcyjnej.\n"
            ),
        }
    )


# =========================
# AUTH – LOGIN
# =========================
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@app.post("/auth/login")
def login(payload: LoginRequest, request: Request):
    db = SessionLocal()
    try:
        email = str(payload.email).strip().lower()
        user = db.query(User).filter(User.email == email).first()

        if not user:
            _audit(db, action="LOGIN_FAIL", request=request, user_id=None, details=f"email={email}")
            raise ApiException(status_code=401, code=ErrorCode.INVALID_CREDENTIALS)

         
        if user.status != UserStatus.ACTIVE.value:
            raise ApiException(status_code=403, code=ErrorCode.ACCOUNT_INACTIVE)

        if not verify_password(payload.password, user.password_hash):
            _audit(db, action="LOGIN_FAIL", request=request, user_id=user.id, details=f"email={email}")
            raise ApiException(status_code=401, code=ErrorCode.INVALID_CREDENTIALS)

        access_token = create_access_token(user.id)

        _audit(db, action="LOGIN_SUCCESS", request=request, user_id=user.id, details=f"email={email}")

        return ok(
            {
                "access_token": access_token,
                "token_type": "bearer",
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "role": user.role,
                    "status": user.status,
                },
            }
        )
    finally:
        db.close()


# =========================
# AUTH – LOGOUT
# =========================
@app.post("/auth/logout")
def logout(request: Request, current_user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        _audit(db, action="LOGOUT", request=request, user_id=current_user.id, details=None)
        return ok({"ok": True})
    finally:
        db.close()


# =========================
# AUTH — /auth/me
# =========================
@app.get("/auth/me")
def auth_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "role": current_user.role,
    }


# =========================
# TEST: endpoint chroniony JWT
# =========================
@app.get("/protected")
def protected_route(current_user: User = Depends(get_current_user)):
    return {
        "ok": True,
        "user_id": current_user.id,
        "email": current_user.email,
        "role": current_user.role,
    }


# =========================
# TEST: endpoint tylko dla admina
# =========================
@app.get("/admin-only")
def admin_only(current_user: User = Depends(require_role("admin"))):
    return {"ok": True, "msg": "Witaj admin!", "user_id": current_user.id}


# =========================
# TEST: endpoint dla partner lub admin
# =========================
@app.get("/partner-or-admin")
def partner_or_admin(current_user: User = Depends(require_role("partner", "admin"))):
    return {"ok": True, "msg": "Witaj partner/admin!", "user_id": current_user.id, "role": current_user.role}


# =========================
# PROFILE — USER — GET /users/me
# =========================
@app.get("/users/me")
def users_me(current_user: User = Depends(require_role("user"))):
    db = SessionLocal()
    try:
        profile = (
            db.query(UserProfile)
            .filter(UserProfile.user_id == current_user.id)
            .first()
        )

        if not profile:
            profile = UserProfile(user_id=current_user.id)
            db.add(profile)
            db.commit()
            db.refresh(profile)

        zainteresowania = []
        if profile.zainteresowania_json:
            try:
                zainteresowania = json.loads(profile.zainteresowania_json) or []
            except Exception:
                zainteresowania = []

        return ok(
            {
                "user_id": current_user.id,
                "nick": profile.nick,
                "miasto": profile.miasto,
                "bio": profile.bio,
                "zainteresowania": zainteresowania,
                "age_min": profile.age_min,
                "age_max": profile.age_max,
                "avatar_url": profile.avatar_url,
            }
        )
    finally:
        db.close()


# =========================
# PROFILE — USER — PATCH /users/me
# =========================
class UserMePatch(BaseModel):
    nick: Optional[str] = Field(default=None)
    miasto: Optional[str] = Field(default=None)
    bio: Optional[str] = Field(default=None, max_length=300)
    zainteresowania: Optional[List[str]] = Field(default=None)
    age_min: Optional[int] = Field(default=None, ge=16, le=120)
    age_max: Optional[int] = Field(default=None, ge=16, le=120)
    avatar_url: Optional[str] = Field(default=None)


def _trim(s: Optional[str]) -> Optional[str]:
    if s is None:
        return None
    s2 = s.strip()
    return s2 if s2 != "" else None


@app.patch("/users/me")
def users_me_patch(
    payload: UserMePatch,
    current_user: User = Depends(require_role("user")),
):
    db = SessionLocal()
    try:
        profile = (
            db.query(UserProfile)
            .filter(UserProfile.user_id == current_user.id)
            .first()
        )

        if not profile:
            profile = UserProfile(user_id=current_user.id)
            db.add(profile)
            db.commit()
            db.refresh(profile)

        if payload.nick is not None:
            profile.nick = _trim(payload.nick)
        if payload.miasto is not None:
            profile.miasto = _trim(payload.miasto)
        if payload.bio is not None:
            profile.bio = _trim(payload.bio)

        new_min = payload.age_min if payload.age_min is not None else profile.age_min
        new_max = payload.age_max if payload.age_max is not None else profile.age_max
        if new_min is not None and new_max is not None and new_min > new_max:
            raise HTTPException(status_code=422, detail="age_min_must_be_lte_age_max")

        if payload.age_min is not None:
            profile.age_min = payload.age_min
        if payload.age_max is not None:
            profile.age_max = payload.age_max

        if payload.zainteresowania is not None:
            cleaned: list[str] = []
            for item in payload.zainteresowania:
                if item is None:
                    continue
                t = item.strip()
                if t == "":
                    continue
                if len(t) > 40:
                    raise HTTPException(status_code=422, detail="interest_too_long_max_40")
                cleaned.append(t)

            if len(cleaned) > 20:
                raise HTTPException(status_code=422, detail="too_many_interests_max_20")

            profile.zainteresowania_json = json.dumps(cleaned, ensure_ascii=False)

        if payload.avatar_url is not None:
            profile.avatar_url = _trim(payload.avatar_url)

        profile.updated_at = datetime.utcnow()

        db.add(profile)
        db.commit()
        db.refresh(profile)

        zainteresowania = []
        if profile.zainteresowania_json:
            try:
                zainteresowania = json.loads(profile.zainteresowania_json) or []
            except Exception:
                zainteresowania = []

        return ok(
            {
                "user_id": current_user.id,
                "nick": profile.nick,
                "miasto": profile.miasto,
                "bio": profile.bio,
                "zainteresowania": zainteresowania,
                "age_min": profile.age_min,
                "age_max": profile.age_max,
                "avatar_url": profile.avatar_url,
            }
        )
    finally:
        db.close()


# =========================
# PROFILE — PARTNER — GET /partners/me
# =========================
@app.get("/partners/me")
def partners_me(current_user: User = Depends(require_role("partner"))):
    db = SessionLocal()
    try:
        profile = (
            db.query(PartnerProfile)
            .filter(PartnerProfile.user_id == current_user.id)
            .first()
        )

        if not profile:
            profile = PartnerProfile(user_id=current_user.id)
            db.add(profile)
            db.commit()
            db.refresh(profile)

        return ok(
            {
                "user_id": current_user.id,
                "nazwa": profile.nazwa,
                "miasto": profile.miasto,
                "bio": profile.bio,
                "logo_url": profile.logo_url,
            }
        )
    finally:
        db.close()


# =========================
# PROFILE — PARTNER — PATCH /partners/me
# =========================
class PartnerMePatch(BaseModel):
    nazwa: Optional[str] = Field(default=None, max_length=120)
    miasto: Optional[str] = Field(default=None, max_length=80)
    bio: Optional[str] = Field(default=None, max_length=500)
    logo_url: Optional[str] = Field(default=None)


@app.patch("/partners/me")
def partners_me_patch(
    payload: PartnerMePatch,
    current_user: User = Depends(require_role("partner")),
):
    db = SessionLocal()
    try:
        profile = (
            db.query(PartnerProfile)
            .filter(PartnerProfile.user_id == current_user.id)
            .first()
        )

        if not profile:
            profile = PartnerProfile(user_id=current_user.id)
            db.add(profile)
            db.commit()
            db.refresh(profile)

        if payload.nazwa is not None:
            profile.nazwa = _trim(payload.nazwa)

        if payload.miasto is not None:
            profile.miasto = _trim(payload.miasto)

        if payload.bio is not None:
            profile.bio = _trim(payload.bio)

        if payload.logo_url is not None:
            profile.logo_url = _trim(payload.logo_url)

        profile.updated_at = datetime.utcnow()

        db.add(profile)
        db.commit()
        db.refresh(profile)

        return ok(
            {
                "user_id": current_user.id,
                "nazwa": profile.nazwa,
                "miasto": profile.miasto,
                "bio": profile.bio,
                "logo_url": profile.logo_url,
            }
        )
    finally:
        db.close()


# =========================
# UPLOADS (v1) — AVATAR (USER)
# POST /uploads/avatar
# =========================
AVATARS_DIR = Path("uploads") / "avatars"
AVATARS_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5MB


@app.post("/uploads/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(require_role("user")),
):
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=422, detail="invalid_file_type")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=422, detail="file_too_large_max_5mb")

    ext_map = {
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/webp": "webp",
    }
    ext = ext_map.get(file.content_type, "bin")

    filename = f"{uuid4().hex}.{ext}"
    path = AVATARS_DIR / filename

    with open(path, "wb") as f:
        f.write(content)

    avatar_url = f"/uploads/static/avatars/{filename}"

    db = SessionLocal()
    try:
        profile = (
            db.query(UserProfile)
            .filter(UserProfile.user_id == current_user.id)
            .first()
        )
        if not profile:
            profile = UserProfile(user_id=current_user.id)
            db.add(profile)
            db.commit()
            db.refresh(profile)

        profile.avatar_url = avatar_url
        profile.updated_at = datetime.utcnow()
        db.add(profile)
        db.commit()

        return ok({"avatar_url": avatar_url})
    finally:
        db.close()


# =========================
# UPLOADS (v1) — LOGO (PARTNER)
# POST /uploads/logo
# =========================
LOGOS_DIR = Path("uploads") / "logos"
LOGOS_DIR.mkdir(parents=True, exist_ok=True)


@app.post("/uploads/logo")
async def upload_logo(
    file: UploadFile = File(...),
    current_user: User = Depends(require_role("partner")),
):
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=422, detail="invalid_file_type")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=422, detail="file_too_large_max_5mb")

    ext_map = {
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/webp": "webp",
    }
    ext = ext_map.get(file.content_type, "bin")

    filename = f"{uuid4().hex}.{ext}"
    path = LOGOS_DIR / filename

    with open(path, "wb") as f:
        f.write(content)

    logo_url = f"/uploads/static/logos/{filename}"

    db = SessionLocal()
    try:
        profile = (
            db.query(PartnerProfile)
            .filter(PartnerProfile.user_id == current_user.id)
            .first()
        )
        if not profile:
            profile = PartnerProfile(user_id=current_user.id)
            db.add(profile)
            db.commit()
            db.refresh(profile)

        profile.logo_url = logo_url
        profile.updated_at = datetime.utcnow()
        db.add(profile)
        db.commit()

        return ok({"logo_url": logo_url})
    finally:
        db.close()


# =========================
# EVENTS — CORE
# PARTNER: CREATE + UPDATE EVENT
# =========================
def _ensure_utc(dt):
    """
    SQLite często zwraca datetime bez tzinfo (naive). Traktujemy je jako UTC,
    żeby nie było 500 przy porównaniach i żeby logika była spójna.
    """
    if dt is None:
        return None
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


@app.post("/partners/events")
def partner_create_event(
    payload: EventCreate,
    current_user: User = Depends(require_role("partner")),
):
    def _to_utc_naive(dt):
        if dt is None:
            return None
        if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
            return dt.replace(tzinfo=None)
        return dt.astimezone(timezone.utc).replace(tzinfo=None)

    def _to_str_or_none(v):
        if v is None:
            return None
        return str(v)

    db = SessionLocal()
    try:
        event = Event(
            partner_user_id=current_user.id,
            title=payload.title,
            description=payload.description,
            city=payload.city,
            start_at=_to_utc_naive(payload.start_at),
            end_at=_to_utc_naive(payload.end_at),
            capacity=payload.capacity,
            event_cover_url=payload.event_cover_url,
            pricing_type=payload.pricing_type,
            price_fixed=payload.price_fixed,
            price_min=payload.price_min,
            price_max=payload.price_max,
            payment_link=_to_str_or_none(payload.payment_link),
        )
        db.add(event)
        db.commit()
        db.refresh(event)

        return ok(
            EventOut(
                id=event.id,
                partner_user_id=event.partner_user_id,
                title=event.title,
                description=event.description,
                city=event.city,
                start_at=event.start_at,
                end_at=event.end_at,
                capacity=event.capacity,
                status=event.status,
                created_at=event.created_at,
                updated_at=event.updated_at,
                event_cover_url=event.event_cover_url,
                pricing_type=event.pricing_type,
                price_fixed=event.price_fixed,
                price_min=event.price_min,
                price_max=event.price_max,
                payment_link=event.payment_link,
            ).model_dump()
        )
    finally:
        db.close()


@app.patch("/partners/events/{event_id}")
def partner_update_event(
    event_id: int,
    payload: EventUpdate,
    current_user: User = Depends(require_role("partner")),
):
    db = SessionLocal()
    try:
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise HTTPException(status_code=404, detail="EVENT_NOT_FOUND")

        if event.partner_user_id != current_user.id:
            raise HTTPException(status_code=403, detail="FORBIDDEN_NOT_OWNER")

        current_start = _ensure_utc(event.start_at)
        current_end = _ensure_utc(event.end_at)

        new_start = _ensure_utc(payload.start_at) if payload.start_at is not None else current_start
        new_end = _ensure_utc(payload.end_at) if payload.end_at is not None else current_end

        if new_start is not None and new_end is not None and not (new_start < new_end):
            raise HTTPException(status_code=422, detail="INVALID_EVENT_DATES")

        def _to_utc_naive(dt):
            if dt is None:
                return None
            if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
                return dt.replace(tzinfo=None)
            return dt.astimezone(timezone.utc).replace(tzinfo=None)

        def _to_str_or_none(v):
            if v is None:
                return None
            return str(v)

        if payload.title is not None:
            event.title = payload.title
        if payload.description is not None:
            event.description = payload.description
        if payload.city is not None:
            event.city = payload.city
        if payload.start_at is not None:
            event.start_at = _to_utc_naive(payload.start_at)
        if payload.end_at is not None:
            event.end_at = _to_utc_naive(payload.end_at)
        if payload.capacity is not None:
            event.capacity = payload.capacity
        if payload.status is not None:
            event.status = payload.status

        if payload.event_cover_url is not None:
            event.event_cover_url = payload.event_cover_url

        if payload.pricing_type is not None:
            event.pricing_type = payload.pricing_type
        if payload.price_fixed is not None:
            event.price_fixed = payload.price_fixed
        if payload.price_min is not None:
            event.price_min = payload.price_min
        if payload.price_max is not None:
            event.price_max = payload.price_max
        if payload.payment_link is not None:
            event.payment_link = _to_str_or_none(payload.payment_link)

        event.updated_at = datetime.utcnow()

        db.add(event)
        db.commit()
        db.refresh(event)

        return ok(
            EventOut(
                id=event.id,
                partner_user_id=event.partner_user_id,
                title=event.title,
                description=event.description,
                city=event.city,
                start_at=event.start_at,
                end_at=event.end_at,
                capacity=event.capacity,
                status=event.status,
                created_at=event.created_at,
                updated_at=event.updated_at,
                event_cover_url=event.event_cover_url,
                pricing_type=event.pricing_type,
                price_fixed=event.price_fixed,
                price_min=event.price_min,
                price_max=event.price_max,
                payment_link=event.payment_link,
            ).model_dump()
        )
    finally:
        db.close()


# =========================
# EVENTS — PARTNER: DELETE EVENT
# =========================
@app.delete("/partners/events/{event_id}")
def partner_delete_event(
    event_id: int,
    current_user: User = Depends(require_role("partner")),
):
    db = SessionLocal()
    try:
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise HTTPException(status_code=404, detail="EVENT_NOT_FOUND")

        if event.partner_user_id != current_user.id:
            raise HTTPException(status_code=403, detail="FORBIDDEN_NOT_OWNER")

        db.delete(event)
        db.commit()

        return ok({"deleted": True, "id": event_id})
    finally:
        db.close()


# =========================
# EVENTS — STATUS FLOW
# =========================
@app.post("/partners/events/{event_id}/publish")
def partner_publish_event(
    event_id: int,
    current_user: User = Depends(require_role("partner")),
):
    db = SessionLocal()
    try:
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise HTTPException(status_code=404, detail="EVENT_NOT_FOUND")

        if event.partner_user_id != current_user.id:
            raise HTTPException(status_code=403, detail="FORBIDDEN_NOT_OWNER")

        if event.status != "draft":
            raise HTTPException(status_code=409, detail="INVALID_STATUS_TRANSITION")

        event.status = "published"
        event.updated_at = datetime.utcnow()

        db.add(event)
        db.commit()
        db.refresh(event)

        return ok({"id": event.id, "status": event.status})
    finally:
        db.close()


@app.post("/partners/events/{event_id}/archive")
def partner_archive_event(
    event_id: int,
    current_user: User = Depends(require_role("partner")),
):
    db = SessionLocal()
    try:
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise HTTPException(status_code=404, detail="EVENT_NOT_FOUND")

        if event.partner_user_id != current_user.id:
            raise HTTPException(status_code=403, detail="FORBIDDEN_NOT_OWNER")

        if event.status != "published":
            raise HTTPException(status_code=409, detail="INVALID_STATUS_TRANSITION")

        event.status = "archived"
        event.updated_at = datetime.utcnow()

        db.add(event)
        db.commit()
        db.refresh(event)

        return ok({"id": event.id, "status": event.status})
    finally:
        db.close()


# =========================
# EVENTS — USER: LISTA EVENTÓW
# =========================
@app.get("/events")
def list_events(
    city: Optional[str] = None,
    date: Optional[date] = None,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    db = SessionLocal()
    try:
        q = db.query(Event).filter(Event.status == "published")

        if city is not None and city.strip() != "":
            q = q.filter(Event.city == city.strip())

        if date is not None:
            start_dt = datetime(date.year, date.month, date.day, 0, 0, 0)
            end_dt = datetime(date.year, date.month, date.day, 23, 59, 59)
            q = q.filter(Event.start_at >= start_dt)
            q = q.filter(Event.start_at <= end_dt)

        total = q.count()

        events = (
            q.order_by(Event.start_at.asc())
            .limit(limit)
            .offset(offset)
            .all()
        )

        items = []
        for e in events:
            items.append(
                {
                    "id": e.id,
                    "partner_user_id": e.partner_user_id,
                    "title": e.title,
                    "description": e.description,
                    "city": e.city,
                    "start_at": e.start_at,
                    "end_at": e.end_at,
                    "capacity": e.capacity,
                    "status": e.status,
                    "created_at": e.created_at,
                    "updated_at": e.updated_at,
                    "event_cover_url": e.event_cover_url,
                    "pricing_type": e.pricing_type,
                    "price_fixed": e.price_fixed,
                    "price_min": e.price_min,
                    "price_max": e.price_max,
                    "payment_link": e.payment_link,
                }
            )

        return ok(
            {
                "items": items,
                "pagination": {
                    "limit": limit,
                    "offset": offset,
                    "total": total,
                },
            }
        )
    finally:
        db.close()


# =========================
# EVENTS — USER: SZCZEGÓŁY EVENTU
# =========================
@app.get("/events/{event_id}")
def get_event_details(event_id: int):
    db = SessionLocal()
    try:
        event = (
            db.query(Event)
            .filter(Event.id == event_id)
            .filter(Event.status == "published")
            .first()
        )
        if not event:
            raise HTTPException(status_code=404, detail="EVENT_NOT_FOUND")

        return ok(
            {
                "id": event.id,
                "partner_user_id": event.partner_user_id,
                "title": event.title,
                "description": event.description,
                "city": event.city,
                "start_at": event.start_at,
                "end_at": event.end_at,
                "capacity": event.capacity,
                "status": event.status,
                "created_at": event.created_at,
                "updated_at": event.updated_at,
                "event_cover_url": event.event_cover_url,
                "pricing_type": event.pricing_type,
                "price_fixed": event.price_fixed,
                "price_min": event.price_min,
                "price_max": event.price_max,
                "payment_link": event.payment_link,
            }
        )
    finally:
        db.close()


# =========================
# UPLOADS (v1) — EVENT COVER (PARTNER)
# =========================
EVENT_COVERS_DIR = Path("uploads") / "event-covers"
EVENT_COVERS_DIR.mkdir(parents=True, exist_ok=True)


@app.post("/uploads/event-cover")
async def upload_event_cover(
    file: UploadFile = File(...),
    current_user: User = Depends(require_role("partner")),
):
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=422, detail="invalid_file_type")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=422, detail="file_too_large_max_5mb")

    ext_map = {
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/webp": "webp",
    }
    ext = ext_map.get(file.content_type, "bin")

    filename = f"{uuid4().hex}.{ext}"
    path = EVENT_COVERS_DIR / filename

    with open(path, "wb") as f:
        f.write(content)

    event_cover_url = f"/uploads/static/event-covers/{filename}"

    return ok({"event_cover_url": event_cover_url})


# =========================
# EVENTS — PARTNER: LISTA SWOICH EVENTÓW
# =========================
@app.get("/partners/events")
def partner_list_events(
    status: Optional[str] = None,  # draft | published | archived
    city: Optional[str] = None,
    date: Optional[date] = None,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_role("partner")),
):
    db = SessionLocal()
    try:
        q = db.query(Event).filter(Event.partner_user_id == current_user.id)

        if status is not None and status.strip() != "":
            st = status.strip()
            if st not in {"draft", "published", "archived"}:
                raise HTTPException(status_code=422, detail="INVALID_STATUS_FILTER")
            q = q.filter(Event.status == st)

        if city is not None and city.strip() != "":
            q = q.filter(Event.city == city.strip())

        if date is not None:
            start_dt = datetime(date.year, date.month, date.day, 0, 0, 0)
            end_dt = datetime(date.year, date.month, date.day, 23, 59, 59)
            q = q.filter(Event.start_at >= start_dt)
            q = q.filter(Event.start_at <= end_dt)

        total = q.count()

        events = (
            q.order_by(Event.start_at.asc())
            .limit(limit)
            .offset(offset)
            .all()
        )

        items = []
        for e in events:
            items.append(
                {
                    "id": e.id,
                    "partner_user_id": e.partner_user_id,
                    "title": e.title,
                    "description": e.description,
                    "city": e.city,
                    "start_at": e.start_at,
                    "end_at": e.end_at,
                    "capacity": e.capacity,
                    "status": e.status,
                    "created_at": e.created_at,
                    "updated_at": e.updated_at,
                    "event_cover_url": e.event_cover_url,
                    "pricing_type": e.pricing_type,
                    "price_fixed": e.price_fixed,
                    "price_min": e.price_min,
                    "price_max": e.price_max,
                    "payment_link": e.payment_link,
                }
            )

        return ok(
            {
                "items": items,
                "pagination": {
                    "limit": limit,
                    "offset": offset,
                    "total": total,
                },
            }
        )
    finally:
        db.close()


# =========================
# EVENTS — PARTNER: SZCZEGÓŁY SWOJEGO EVENTU
# =========================
@app.get("/partners/events/{event_id}")
def partner_get_event_details(
    event_id: int,
    current_user: User = Depends(require_role("partner")),
):
    db = SessionLocal()
    try:
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise HTTPException(status_code=404, detail="EVENT_NOT_FOUND")

        if event.partner_user_id != current_user.id:
            raise HTTPException(status_code=403, detail="FORBIDDEN_NOT_OWNER")

        return ok(
            {
                "id": event.id,
                "partner_user_id": event.partner_user_id,
                "title": event.title,
                "description": event.description,
                "city": event.city,
                "start_at": event.start_at,
                "end_at": event.end_at,
                "capacity": event.capacity,
                "status": event.status,
                "created_at": event.created_at,
                "updated_at": event.updated_at,
                "event_cover_url": event.event_cover_url,
                "pricing_type": event.pricing_type,
                "price_fixed": event.price_fixed,
                "price_min": event.price_min,
                "price_max": event.price_max,
                "payment_link": event.payment_link,
            }
        )
    finally:
        db.close()
# =========================
# EVENTS — USER: MOJE ZAPISY
# GET /users/me/events?limit=10&offset=0&sort=created_at_desc
# =========================
@app.get("/users/me/events")
def my_event_signups(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort: str = "created_at_desc",  # created_at_desc | created_at_asc | start_at_asc | start_at_desc
    current_user: User = Depends(require_role("user")),
):
    db = SessionLocal()
    try:
        # sort
        if sort not in {"created_at_desc", "created_at_asc", "start_at_asc", "start_at_desc"}:
            raise HTTPException(status_code=422, detail="INVALID_SORT")

        q = (
            db.query(EventSignup, Event)
            .join(Event, Event.id == EventSignup.event_id)
            .filter(EventSignup.user_id == current_user.id)
        )

        total = q.count()

        # order by
        if sort == "created_at_desc":
            q = q.order_by(EventSignup.created_at.desc())
        elif sort == "created_at_asc":
            q = q.order_by(EventSignup.created_at.asc())
        elif sort == "start_at_asc":
            q = q.order_by(Event.start_at.asc())
        elif sort == "start_at_desc":
            q = q.order_by(Event.start_at.desc())

        rows = q.offset(offset).limit(limit).all()

        items = []
        for signup, event in rows:
            items.append(
                {
                    "signup": {
                        "event_id": signup.event_id,
                        "created_at": signup.created_at,
                    },
                    "event": {
                        "id": event.id,
                        "title": event.title,
                        "city": event.city,
                        "start_at": event.start_at,
                        "end_at": event.end_at,
                        "status": event.status,
                        "capacity": event.capacity,
                        "event_cover_url": event.event_cover_url,
                        "pricing_type": event.pricing_type,
                        "price_fixed": event.price_fixed,
                        "price_min": event.price_min,
                        "price_max": event.price_max,
                        "payment_link": event.payment_link,
                    },
                }
            )

        return ok(
            {
                "items": items,
                "pagination": {
                    "limit": limit,
                    "offset": offset,
                    "total": total,
                },
            }
        )
    finally:
        db.close()
# =========================
# EVENTS — PARTNER: PARTICIPANTS
# GET /partners/events/{id}/participants?limit=10&offset=0
# =========================
@app.get("/partners/events/{event_id}/participants")
def partner_event_participants(
    event_id: int,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_role("partner")),
):
    db = SessionLocal()
    try:
        # 1) event musi istnieć
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise HTTPException(status_code=404, detail="EVENT_NOT_FOUND")

        # 2) tylko właściciel
        if event.partner_user_id != current_user.id:
            raise HTTPException(status_code=403, detail="FORBIDDEN_NOT_OWNER")

        # 3) query zapisów + user
        q = (
            db.query(EventSignup, User)
            .join(User, User.id == EventSignup.user_id)
            .filter(EventSignup.event_id == event_id)
        )

        total = q.count()

        rows = (
            q.order_by(EventSignup.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        items = []
        for signup, user in rows:
            items.append(
                {
                    "user": {
                        "id": user.id,
                        "email": user.email,
                    },
                    "signup": {
                        "created_at": signup.created_at,
                    },
                }
            )

        return ok(
            {
                "event_id": event_id,
                "items": items,
                "pagination": {
                    "limit": limit,
                    "offset": offset,
                    "total": total,
                },
            }
        )
    finally:
        db.close()
# =========================
# EVENTS — PARTNER: STATS
# GET /partners/events/{id}/stats
# =========================
@app.get("/partners/events/{event_id}/stats")
def partner_event_stats(
    event_id: int,
    current_user: User = Depends(require_role("partner")),
):
    db = SessionLocal()
    try:
        # 1) event musi istnieć
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise HTTPException(status_code=404, detail="EVENT_NOT_FOUND")

        # 2) tylko właściciel
        if event.partner_user_id != current_user.id:
            raise HTTPException(status_code=403, detail="FORBIDDEN_NOT_OWNER")

        # 3) policz zapisy
        signups_count = (
            db.query(EventSignup)
            .filter(EventSignup.event_id == event_id)
            .count()
        )

        capacity = event.capacity  # może być None
        spots_left = None
        if capacity is not None:
            spots_left = max(capacity - signups_count, 0)

        return ok(
            {
                "event_id": event_id,
                "signups_count": signups_count,
                "capacity": capacity,
                "spots_left": spots_left,
            }
        )
    finally:
        db.close()
