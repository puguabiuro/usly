# USLY — Local Development


## Backend (lokalnie)

### Wymagania
- Python 3.11
- virtualenv

### Uruchomienie

1. Przejdź do katalogu backend:
   
   cd backend

2. Utwórz i aktywuj środowisko (jeśli jeszcze nie istnieje):

   python3 -m venv .venv
   . .venv/bin/activate
   pip install -r requirements.txt

3. Skopiuj plik środowiskowy:

   cp .env.example .env

4. Uruchom backend:

   ./dev.sh

5. Sprawdź healthcheck:

   curl http://localhost:8000/healthz

## Frontend (lokalnie)

### Uruchomienie

1. Przejdź do katalogu frontend:

   cd frontend

2. Uruchom serwer:

   ./dev.sh

3. Otwórz w przeglądarce:

   http://localhost:5173

## Scenariusze testowe (MVP)

### A. Wspólne (Towarzysz + Organizator)

1. Rejestracja (bez social)
   - Utwórz konto e-mail + hasło (bez Google/Apple/Facebook).
   - Sprawdź: poprawne komunikaty przy błędach (np. zajęty e-mail, za krótkie hasło).
   - Sprawdź: wiek <16 nie pozwala na rejestrację.

2. Logowanie
   - Zaloguj się poprawnymi danymi.
   - Spróbuj błędnym hasłem → komunikat „nieprawidłowy email lub hasło” (lub odpowiednik).

3. Sesja / odświeżenie
   - Po zalogowaniu odśwież stronę (F5).
   - Sprawdź: użytkownik nadal jest zalogowany, dane profilu się wczytują.

4. Wylogowanie
   - Wyloguj się.
   - Sprawdź: brak dostępu do ekranów wymagających logowania.

5. Ustawienia profilu
   - Zmień podstawowe dane profilu (np. imię/opis/zainteresowania – jeśli są).
   - Zapisz i odśwież stronę.
   - Sprawdź: zmiany są zachowane.

6. Upload zdjęcia / avatara (bez AI)
   - Wgraj obrazek jako avatar/zdjęcie profilu.
   - Sprawdź: obrazek zapisuje się i jest widoczny po odświeżeniu.

7. „W okolicy” (lokalizacja)
   - Wejdź w ekran „w okolicy”.
   - Zezwól na lokalizację.
   - Sprawdź: aplikacja pokazuje wyniki dla bieżącej lokalizacji.

8. Brak zgody na lokalizację (edge-case)
   - Zablokuj lokalizację w przeglądarce.
   - Sprawdź: aplikacja pokazuje czytelny komunikat i nie crashuje.

9. Osoby w pobliżu + podobne zainteresowania
   - Sprawdź: lista pokazuje osoby w pobliżu.
   - Sprawdź: widoczne są dopasowania po zainteresowaniach (jeśli mechanizm istnieje).

10. Błędy API / 401 (edge-case)
   - Gdy pojawi się 401/403, aplikacja pokazuje jeden spójny komunikat i nie wysypuje UI.

### B. Towarzysz — dodatkowe

1. Zainteresowania → wpływ na dopasowania
   - Zmień zainteresowania i sprawdź, czy sekcja „osoby w pobliżu” reaguje (jeśli tak ma działać).

2. Widoczność profilu
   - Sprawdź, czy profil Towarzysza jest poprawnie widoczny po zapisie (np. w podglądzie profilu).

### C. Organizator — dodatkowe

1. Profil organizatora
   - Uzupełnij/edytuj dane profilu organizatora (opis, kategorie, lokalizacja – jeśli dostępne).
   - Sprawdź: zapis + odświeżenie zachowuje dane.

2. Widoczność organizatora w „okolicy”
   - Jeśli organizator ma się pojawiać w listach w okolicy: sprawdź, czy jest widoczny i ma poprawne dane.
