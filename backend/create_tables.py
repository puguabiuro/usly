from backend.db.database import engine, Base
import models  # noqa: F401  (ważne: rejestruje modele)

def main() -> None:
    Base.metadata.create_all(bind=engine)
    print("Tables created/updated")

if __name__ == "__main__":
    main()
