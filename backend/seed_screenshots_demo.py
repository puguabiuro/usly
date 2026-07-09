from datetime import UTC, date, datetime, timedelta
import json
from pathlib import Path
import os

# Osobna baza demo — nie dotykamy codziennej developerskiej backend/usly.db
DEMO_DB = Path(__file__).resolve().parent / "usly_demo.db"
os.environ["DATABASE_URL"] = f"sqlite:///{DEMO_DB}"

from backend.db.database import Base, engine, SessionLocal
from backend.models import (
    Event,
    EventSave,
    EventSignup,
    EventStatus,
    Friendship,
    Group,
    GroupMembership,
    Message,
    PartnerProfile,
    User,
    UserNotification,
    UserProfile,
    UserRole,
    UserStatus,
)

PASSWORD_HASH = "$2b$12$IpdRlUxXLQACtZdPXvsgFuRuGRM6HygzPebXj3VWuzm/7XnH4QLkS"
PASSWORD = "UslyDemo2026!"

def now_utc():
    return datetime.now(UTC).replace(microsecond=0)

def js(items):
    return json.dumps(items, ensure_ascii=False)

def reset_demo_db():
    if DEMO_DB.exists():
        DEMO_DB.unlink()
    Base.metadata.create_all(bind=engine)

def add_user(db, email, role, dob):
    user = User(
        email=email,
        password_hash=PASSWORD_HASH,
        dob=dob,
        role=role.value,
        status=UserStatus.ACTIVE.value,
        email_verified_at=now_utc(),
        terms_accepted_at=now_utc(),
        terms_version="2026-07",
        privacy_version="2026-07",
        created_at=now_utc(),
    )
    db.add(user)
    db.flush()
    return user

def add_profile(db, user, nick, city, bio, interests, lat, lng, plan="free", trainer=None, radius=25, avatar=None):
    p = UserProfile(
        user_id=user.id,
        nick=nick,
        miasto=city,
        bio=bio,
        zainteresowania_json=js(interests),
        trainer_interests_json=js(trainer or []),
        age_min=24,
        age_max=45,
        nearby_radius_km=radius,
        avatar_url=avatar,
        location_lat=lat,
        location_lng=lng,
        plan=plan,
        plan_source="test",
        plan_status="active",
        plan_updated_at=now_utc(),
        updated_at=now_utc(),
    )
    db.add(p)
    return p

def add_partner_profile(db, user, name, city, category, bio, logo=None, plan="premium"):
    p = PartnerProfile(
        user_id=user.id,
        nazwa=name,
        miasto=city,
        kategoria=category,
        bio=bio,
        logo_url=logo,
        plan=plan,
        plan_source="test",
        plan_status="active",
        plan_updated_at=now_utc(),
        updated_at=now_utc(),
    )
    db.add(p)
    return p

def add_event(db, partner, title, desc, city, where, address, lat, lng, tags, days, hour, duration_h=2, capacity=20, price=None):
    start = now_utc() + timedelta(days=days)
    start = start.replace(hour=hour, minute=0, second=0)
    event = Event(
        partner_user_id=partner.id,
        title=title,
        description=desc,
        city=city,
        where=where,
        address=address,
        location_lat=lat,
        location_lng=lng,
        interest_tag=tags[0],
        interest_tags_json=js(tags),
        start_at=start,
        end_at=start + timedelta(hours=duration_h),
        capacity=capacity,
        pricing_type="paid_fixed" if price else "free",
        price_fixed=price,
        status=EventStatus.PUBLISHED.value,
        created_at=now_utc(),
        updated_at=now_utc(),
    )
    db.add(event)
    db.flush()
    return event

def safe_add(db, obj):
    db.add(obj)
    try:
        db.flush()
    except Exception:
        db.rollback()

def run():
    reset_demo_db()
    db = SessionLocal()
    try:
        users_data = [
            ("demo.towarzysz@uslydemo.pl", "Ola • góry i psy ��", "Warszawa", "Najchętniej spacer, kawa albo spontaniczny wypad za miasto. Szukam ludzi, z którymi łatwo złapać wspólny rytm.", ["góry","psy","spacer","kawa","fotografia"], 52.23, 21.01, "premium"),
            ("maja@uslydemo.pl", "Maja • joga i kawa", "Warszawa", "Poranki z jogą, wieczory z planszówkami. Lubię małe grupy i spokojne rozmowy.", ["joga","kawa","planszówki","wellbeing","spacer"], 52.25, 21.02, "vip"),
            ("bartek@uslydemo.pl", "Bartek • MTB 🚴", "Warszawa", "Rower, bieganie, outdoor. Chętnie dołączę do aktywnej ekipy po pracy.", ["rower","MTB","bieganie","outdoor","sport"], 52.21, 21.04, "premium"),
            ("kasia@uslydemo.pl", "Kasia • planszówki", "Warszawa", "Planszówki, escape roomy i dobra herbata. Bez presji, po prostu fajne spotkania.", ["planszówki","escape room","kawa","książki","spotkania"], 52.24, 20.98, "free"),
            ("michal@uslydemo.pl", "Michał • bieganie", "Warszawa", "Biegam rekreacyjnie, czasem siłownia. Szukam ludzi do wspólnych aktywności.", ["bieganie","siłownia","sport","outdoor","kawa"], 52.19, 21.00, "premium"),
            ("natalia@uslydemo.pl", "Natalia • fotografia", "Warszawa", "Spacer fotograficzny, wystawa albo koncert? Bardzo chętnie.", ["fotografia","sztuka","koncerty","spacer","podróże"], 52.27, 21.00, "vip"),
            ("tomek@uslydemo.pl", "Tomek • stand-up", "Warszawa", "Stand-up, kino i jedzenie na mieście. Lubię poznawać ludzi naturalnie, przez wspólne plany.", ["stand-up","kino","jedzenie","kawa","spotkania"], 52.22, 21.06, "free"),
            ("zuzia@uslydemo.pl", "Zuzia • książki ☕", "Warszawa", "Książki, kawiarnie, spacery i spokojne wydarzenia. Raczej kameralnie niż głośno.", ["książki","kawa","spacer","sztuka","planszówki"], 52.20, 20.96, "premium"),
            ("adam@uslydemo.pl", "Adam • wspinaczka", "Warszawa", "Ścianka, trekking, rower. Najlepsze znajomości zaczynają się od wspólnej aktywności.", ["wspinaczka","góry","rower","sport","outdoor"], 52.26, 21.08, "premium"),
            ("ania@uslydemo.pl", "Ania • taniec", "Warszawa", "Salsa, bachata i wydarzenia taneczne. Chętnie poznam ekipę na regularne wyjścia.", ["taniec","muzyka","koncerty","spotkania","kawa"], 52.18, 21.03, "free"),
            ("piotr@uslydemo.pl", "Piotr • gaming", "Warszawa", "Gaming, planszówki, quizy i luźne spotkania po pracy.", ["gaming","planszówki","quiz","kawa","spotkania"], 52.29, 21.03, "free"),
            ("ewa@uslydemo.pl", "Ewa • food spots", "Warszawa", "Testuję nowe miejsca, lubię warsztaty kulinarne i spontaniczne wyjścia.", ["gotowanie","jedzenie","kawa","podróże","spotkania"], 52.22, 20.93, "vip"),
            ("krakow1@uslydemo.pl", "Karolina • Kraków", "Kraków", "Fotografia, spacery i klimatyczne miejsca. Chętnie na wydarzenia w mieście.", ["fotografia","spacer","sztuka","kawa","podróże"], 50.06, 19.94, "premium"),
            ("krakow2@uslydemo.pl", "Marcin • ceramika", "Kraków", "Warsztaty, rękodzieło, kino i dobre rozmowy.", ["ceramika","sztuka","kino","kawa","warsztaty"], 50.05, 19.95, "free"),
            ("wroclaw1@uslydemo.pl", "Julia • Wrocław", "Wrocław", "Stand-up, koncerty i wydarzenia po pracy. Lubię ludzi z energią.", ["stand-up","koncerty","spotkania","kawa","muzyka"], 51.11, 17.03, "premium"),
            ("wroclaw2@uslydemo.pl", "Paweł • escape room", "Wrocław", "Escape roomy, planszówki i miejskie przygody.", ["escape room","planszówki","gaming","spotkania","kawa"], 51.10, 17.04, "free"),
            ("gdansk1@uslydemo.pl", "Magda • morze", "Gdańsk", "SUP, spacery nad morzem, kawa i zachody słońca.", ["SUP","spacer","kawa","podróże","outdoor"], 54.35, 18.65, "premium"),
            ("gdansk2@uslydemo.pl", "Kuba • koncerty", "Gdańsk", "Koncerty, gitara, food hall i poznawanie nowych miejsc.", ["koncerty","muzyka","jedzenie","spotkania","kawa"], 54.37, 18.61, "free"),
            ("poznan1@uslydemo.pl", "Monika • networking", "Poznań", "Lubię spotkania biznesowe, kawę i rozmowy z ludźmi, którzy coś budują.", ["networking","kawa","biznes","spotkania","podróże"], 52.41, 16.93, "premium"),
            ("poznan2@uslydemo.pl", "Szymon • rower", "Poznań", "Rower, jezioro, outdoor. Szukam aktywnej ekipy na weekendy.", ["rower","outdoor","sport","spacer","kawa"], 52.40, 16.90, "free"),
            ("lodz1@uslydemo.pl", "Iga • kulinaria", "Łódź", "Warsztaty kulinarne, street food i małe wydarzenia.", ["gotowanie","jedzenie","warsztaty","kawa","spotkania"], 51.76, 19.46, "premium"),
            ("katowice1@uslydemo.pl", "Robert • muzyka", "Katowice", "Koncerty, kultura i weekendowe wyjścia.", ["koncerty","muzyka","sztuka","spotkania","kawa"], 50.26, 19.02, "free"),
            ("lublin1@uslydemo.pl", "Nina • pikniki", "Lublin", "Spacery, pikniki, książki i luźne spotkania w plenerze.", ["piknik","spacer","książki","kawa","outdoor"], 51.25, 22.57, "premium"),
            ("szczecin1@uslydemo.pl", "Filip • kajaki", "Szczecin", "Kajaki, rower i wszystko, co dzieje się na zewnątrz.", ["kajaki","rower","outdoor","sport","podróże"], 53.43, 14.55, "free"),
        ]

        users = []
        for i, (email, nick, city, bio, interests, lat, lng, plan) in enumerate(users_data):
            u = add_user(db, email, UserRole.USER, date(1990 + (i % 12), (i % 12) + 1, min(25, 5 + i)))
            trainer = interests[:2] if plan in ("premium", "vip") else []
            add_profile(db, u, nick, city, bio, interests, lat, lng, plan, trainer=trainer)
            users.append(u)

        partners_data = [
            ("demo.organizator@uslydemo.pl", "Studio Motion Warszawa", "Warszawa", "Sport i zajęcia grupowe", "Kameralne treningi, joga i wydarzenia dla osób, które chcą poznawać ludzi przez wspólną aktywność."),
            ("joga@uslydemo.pl", "Luna Yoga Studio", "Warszawa", "Joga i wellbeing", "Spokojne zajęcia, oddech, ruch i dobra atmosfera po pracy."),
            ("planszowki@uslydemo.pl", "Dice & Coffee Club", "Warszawa", "Planszówki", "Spotkania przy grach, kawie i rozmowach bez presji."),
            ("krakow@uslydemo.pl", "Kraków Creative Walks", "Kraków", "Fotografia i warsztaty", "Spacery fotograficzne i kreatywne warsztaty w klimatycznych miejscach."),
            ("wroclaw@uslydemo.pl", "Wrocław Event Room", "Wrocław", "Rozrywka", "Stand-up, escape roomy i miejskie spotkania dla małych grup."),
            ("gdansk@uslydemo.pl", "Baltic Outdoor", "Gdańsk", "Outdoor", "SUP, spacery i wydarzenia nad morzem."),
            ("poznan@uslydemo.pl", "Poznań Connect", "Poznań", "Networking", "Kameralne spotkania dla osób, które chcą poznawać ludzi i projekty."),
            ("lodz@uslydemo.pl", "Łódź Food Lab", "Łódź", "Warsztaty kulinarne", "Gotowanie, degustacje i wspólne odkrywanie smaków."),
        ]

        partners = []
        for i, (email, name, city, cat, bio) in enumerate(partners_data):
            p = add_user(db, email, UserRole.PARTNER, date(1988 + i, 3, 10))
            add_partner_profile(db, p, name, city, cat, bio)
            partners.append(p)

        events = [
            add_event(db, partners[0], "Trening funkcjonalny w parku", "Energetyczny trening w małej grupie. Dla osób, które chcą ruszyć się po pracy i poznać ludzi z okolicy.", "Warszawa", "Park Skaryszewski", "Park Skaryszewski, Warszawa", 52.24, 21.06, ["sport","siłownia","outdoor"], 3, 18, 1.5, 14, 3900),
            add_event(db, partners[1], "Joga o zachodzie słońca", "Spokojne zajęcia dla początkujących i średniozaawansowanych. Po treningu chwila na rozmowę i herbatę.", "Warszawa", "Bulwary Wiślane", "Bulwary Wiślane, Warszawa", 52.24, 21.03, ["joga","wellbeing","spacer"], 4, 19, 1.5, 18, 4900),
            add_event(db, partners[2], "Planszówki i kawa", "Luźne spotkanie przy grach planszowych. Idealne, jeśli chcesz poznać nowych ludzi bez niezręcznego small talku.", "Warszawa", "Kawiarnia przy metrze Centrum", "Centrum, Warszawa", 52.23, 21.00, ["planszówki","kawa","spotkania"], 5, 17, 3, 12, None),
            add_event(db, partners[0], "Rowerem nad Wisłę", "Krótka, spokojna trasa dla osób, które chcą ruszyć się po pracy i pogadać po drodze.", "Warszawa", "Most Świętokrzyski", "Most Świętokrzyski, Warszawa", 52.24, 21.02, ["rower","outdoor","sport"], 8, 18, 2, 20, None),
            add_event(db, partners[3], "Spacer fotograficzny po Kazimierzu", "Klimatyczny spacer z aparatem lub telefonem. Dużo światła, detali i rozmów.", "Kraków", "Kazimierz", "Kazimierz, Kraków", 50.05, 19.95, ["fotografia","spacer","sztuka"], 6, 16, 2, 16, 5900),
            add_event(db, partners[3], "Ceramika przy kawie", "Warsztaty dla początkujących. Tworzymy, rozmawiamy i poznajemy się w spokojnej atmosferze.", "Kraków", "Pracownia na Podgórzu", "Podgórze, Kraków", 50.04, 19.96, ["ceramika","warsztaty","kawa"], 11, 12, 2, 10, 8900),
            add_event(db, partners[4], "Stand-up w małej sali", "Wieczór komedii bez wielkiego tłumu. Idealny pretekst, żeby wyjść i pogadać po występie.", "Wrocław", "Nadodrze", "Nadodrze, Wrocław", 51.12, 17.03, ["stand-up","spotkania","kultura"], 7, 20, 2, 30, 4500),
            add_event(db, partners[4], "Escape room: drużyna z USLY", "Zbieramy małą ekipę i rozwiązujemy zagadki. Nie trzeba nikogo znać wcześniej.", "Wrocław", "Rynek", "Rynek, Wrocław", 51.11, 17.03, ["escape room","planszówki","spotkania"], 13, 18, 1.5, 6, 6900),
            add_event(db, partners[5], "SUP o zachodzie słońca", "Spokojne pływanie dla początkujących i średniozaawansowanych. Po wszystkim herbata na plaży.", "Gdańsk", "Brzeźno", "Plaża Brzeźno, Gdańsk", 54.41, 18.63, ["SUP","outdoor","morze"], 9, 18, 2, 12, 7900),
            add_event(db, partners[5], "Spacer nad morzem + kawa", "Prosty plan: spacer, zachód słońca i kawa. Dobre dla nowych osób w mieście.", "Gdańsk", "Molo Brzeźno", "Molo Brzeźno, Gdańsk", 54.41, 18.62, ["spacer","kawa","morze"], 14, 17, 2, 18, None),
            add_event(db, partners[6], "Networking bez sztywnej atmosfery", "Małe spotkanie dla osób, które budują projekty, pracują kreatywnie albo po prostu chcą poznać ciekawych ludzi.", "Poznań", "Jeżyce", "Jeżyce, Poznań", 52.41, 16.91, ["networking","kawa","biznes"], 10, 18, 2, 20, 3900),
            add_event(db, partners[6], "Rowerem nad Maltę", "Lekka trasa, bez ścigania. Spotkanie dla osób, które chcą aktywnie spędzić weekend.", "Poznań", "Jezioro Maltańskie", "Jezioro Maltańskie, Poznań", 52.40, 16.98, ["rower","outdoor","sport"], 15, 10, 2, 18, None),
            add_event(db, partners[7], "Warsztaty kuchni włoskiej", "Gotujemy razem, jemy razem i poznajemy ludzi bez presji.", "Łódź", "Off Piotrkowska", "Off Piotrkowska, Łódź", 51.75, 19.46, ["gotowanie","warsztaty","jedzenie"], 12, 17, 3, 12, 9900),
            add_event(db, partners[4], "Koncert kameralny", "Mały koncert i rozmowy po wydarzeniu. Dla osób, które lubią muzykę na żywo.", "Katowice", "Strefa Kultury", "Strefa Kultury, Katowice", 50.26, 19.03, ["koncerty","muzyka","kultura"], 16, 19, 2, 40, 5900),
            add_event(db, partners[2], "Piknik i gry plenerowe", "Koc, przekąski i proste gry integracyjne. Lekko, bez presji, w przyjemnym miejscu.", "Lublin", "Ogród Saski", "Ogród Saski, Lublin", 51.25, 22.55, ["piknik","planszówki","spacer"], 18, 13, 3, 20, None),
            add_event(db, partners[5], "Kajaki po Odrze", "Spokojna trasa i mała grupa. Dobry sposób na aktywny weekend i poznanie nowych osób.", "Szczecin", "Bulwary", "Bulwary, Szczecin", 53.42, 14.56, ["kajaki","outdoor","sport"], 20, 11, 2, 14, 8500),
        ]

        groups_data = [
            ("Aktywna Warszawa", "Treningi, spacery, rower i spontaniczne wyjścia po pracy.", "sport"),
            ("Planszówki i kawa", "Spotkania bez presji, rozmowy i gry, przy których łatwiej zacząć znajomość.", "planszówki"),
            ("Kobiety na siłowni", "Wsparcie, motywacja i wspólne treningi dla osób na różnych poziomach.", "siłownia"),
            ("Weekendowe spacery", "Łazienki, Wisła, parki i małe odkrycia w mieście.", "spacer"),
            ("Fotografia miejska", "Spacery fotograficzne, światło, kadry i inspiracje.", "fotografia"),
            ("USLY po pracy", "Luźne wyjścia po pracy: kawa, wydarzenia, krótkie plany.", "spotkania"),
            ("Rower i outdoor", "Trasy rowerowe, weekendy i aktywność bez presji.", "rower"),
            ("Kultura i koncerty", "Koncerty, stand-up, kino i wydarzenia kulturalne.", "koncerty"),
        ]

        groups = []
        for idx, (title, desc, tag) in enumerate(groups_data):
            g = Group(
                creator_id=users[idx % len(users)].id,
                title=title,
                description=desc,
                interest_tag=tag,
                members_count=40 + idx * 17,
                created_at=now_utc() - timedelta(days=20 - idx),
                updated_at=now_utc() - timedelta(hours=idx),
            )
            db.add(g)
            db.flush()
            groups.append(g)

        # Członkostwa grup — demo konto jest w kilku grupach, reszta naturalnie rozłożona
        for i, u in enumerate(users):
            for g in groups:
                if i == 0 or (i + g.id) % 3 == 0:
                    safe_add(db, GroupMembership(user_id=u.id, group_id=g.id, role="member", joined_at=now_utc() - timedelta(days=(i % 10))))

        # Uczestnicy i zapisane wydarzenia
        for i, event in enumerate(events):
            for u in users:
                if (u.id + event.id) % 4 == 0:
                    safe_add(db, EventSignup(event_id=event.id, user_id=u.id, created_at=now_utc() - timedelta(days=i % 5)))
                if (u.id + event.id) % 5 == 0:
                    safe_add(db, EventSave(event_id=event.id, user_id=u.id, created_at=now_utc() - timedelta(days=i % 4)))

        # Znajomi demo użytkownika i kilka relacji między innymi
        for u in users[1:9]:
            safe_add(db, Friendship(requester_user_id=users[0].id, addressee_user_id=u.id, status="accepted", created_at=now_utc() - timedelta(days=7), responded_at=now_utc() - timedelta(days=6)))
        for a, b in [(1,2),(3,4),(5,6),(7,8),(9,10),(12,13),(14,15)]:
            safe_add(db, Friendship(requester_user_id=users[a].id, addressee_user_id=users[b].id, status="accepted", created_at=now_utc() - timedelta(days=5), responded_at=now_utc() - timedelta(days=4)))

        # Wiadomości prywatne
        private_messages = [
            (users[1], users[0], "Hej Ola! Widziałam, że zapisałaś się na jogę — idziemy razem?", False, 2),
            (users[0], users[1], "Tak! Super, że też idziesz 😊", True, 2),
            (users[2], users[0], "W sobotę robię krótką trasę rowerową nad Wisłę. Dołączasz?", False, 5),
            (users[5], users[0], "Mam kilka zdjęć z ostatniego spaceru, wysłać Ci później?", True, 8),
            (partners[0], users[0], "Cześć! Mamy jeszcze 3 miejsca na trening funkcjonalny w parku.", False, 4),
            (users[0], partners[0], "Brzmi dobrze. Czy poziom jest OK dla początkujących?", True, 4),
        ]
        for sender, recipient, content, unread, hours in private_messages:
            db.add(Message(sender_user_id=sender.id, recipient_user_id=recipient.id, content=content, is_read=not unread, created_at=now_utc() - timedelta(hours=hours)))

        # Wiadomości grupowe
        group_messages = [
            (groups[0], users[2], "Kto jutro idzie na trening w parku?"),
            (groups[0], users[4], "Ja będę, mogę być 10 minut wcześniej."),
            (groups[1], users[3], "Na piątek rezerwuję stolik na planszówki ☕"),
            (groups[4], users[5], "W sobotę fajne światło na spacer foto, ktoś chętny?"),
            (groups[6], users[8], "Robimy spokojną trasę, bez ścigania."),
        ]
        for g, sender, content in group_messages:
            db.add(Message(sender_user_id=sender.id, group_id=g.id, content=content, is_read=False, created_at=now_utc() - timedelta(hours=3)))

        # Powiadomienia dla głównego konta demo
        notifications = [
            ("friend_request", None, None, 2),
            ("event_reminder_2d", events[0], partners[0], 5),
            ("event_updated", events[1], partners[1], 10),
            ("group_invitation", None, None, 16),
            ("event_saved_updated", events[4], partners[3], 24),
        ]
        for typ, ev, partner, hours in notifications:
            db.add(UserNotification(
                user_id=users[0].id,
                event_id=ev.id if ev else None,
                partner_user_id=partner.id if partner else None,
                type=typ,
                created_at=now_utc() - timedelta(hours=hours),
                read_at=None if hours < 12 else now_utc() - timedelta(hours=hours-1),
            ))

        db.commit()

        print("")
        print("SCREENSHOTS DEMO READY")
        print(f"DB: {DEMO_DB}")
        print(f"Towarzysze: {len(users)}")
        print(f"Organizatorzy: {len(partners)}")
        print(f"Wydarzenia: {len(events)}")
        print(f"Grupy: {len(groups)}")
        print("")
        print(f"Towarzysz: demo.towarzysz@uslydemo.pl / {PASSWORD}")
        print(f"Organizator: demo.organizator@uslydemo.pl / {PASSWORD}")

    finally:
        db.close()

if __name__ == "__main__":
    run()
