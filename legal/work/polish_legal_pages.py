from pathlib import Path

def replace_between(text, start_marker, end_marker, replacement):
    start = text.index(start_marker)
    end = text.index(end_marker, start)
    return text[:start] + replacement.strip() + "\n" + text[end:]

pl = Path("frontend/regulamin.html")
en = Path("frontend/regulamin.en.html")

pl_text = pl.read_text(encoding="utf-8")
en_text = en.read_text(encoding="utf-8")

pl_text = pl_text.replace("<strong>16 czerwca 2026</strong>", "<strong>01.07.2026</strong>")
en_text = en_text.replace("<strong>16 June 2026</strong>", "<strong>01.07.2026</strong>")

pl_section = """
<h2 id="3-profil-u-ytkownika-i-plany-p-atno-ci">§ 3. Profil Użytkownika i Plany Płatności</h2>
<p class="clause">1. Użytkownik w procesie rejestracji zaznacza interesujący go Profil, który decyduje o dostępnych funkcjach korzystania z Aplikacji oraz Pakiety Płatności. Opcje te można zmienić w dowolnym czasie.</p>
<p class="clause">2. Użytkownik może założyć w Aplikacji następujący Profil:</p>
<p class="letter-item">a) Towarzysz — wybierając dostęp do konta „Poznaj Ludzi”,</p>
<p class="letter-item">b) Organizator — wybierając dostęp do konta „Twórz Wydarzenia”.</p>

<p class="clause">3. Po dokonaniu wyboru Profilu, Użytkownik dokonuje wyboru Planu Płatności. Aplikacja dostępna jest w wersji bezpłatnej oraz w formie płatnych Planów — subskrypcji, odnawianych comiesięcznie. Ceny poszczególnych Planów mogą być zmienne. Każdorazowo ceny podawane są w opisie danego Planu w funkcjach Aplikacji. Szczegółowy zakres funkcjonalności, ceny, okresy rozliczeniowe oraz ewentualne rabaty prezentowane są w Aplikacji przed dokonaniem zakupu.</p>
<p class="clause">Zakup planów płatnych realizowany jest za pośrednictwem sklepów Apple App Store oraz Google Play. Rozliczenia, odnawianie subskrypcji oraz anulowanie subskrypcji podlegają zasadom odpowiednio Apple App Store i Google Play.</p>

<div class="planSection">
  <h3>Plany Towarzysza</h3>
  <div class="planGrid">
    <section class="planCard"><h4>FREE</h4><ul><li>rozmowy 1:1 ze znajomymi</li><li>możliwość dołączania do jednej (1) grupy jednocześnie</li><li>brak możliwości tworzenia własnych grup</li><li>wybór do 5 zainteresowań w profilu</li><li>1 awatar AI miesięcznie</li></ul></section>
    <section class="planCard"><h4>PLUS</h4><ul><li>rozmowy 1:1 ze znajomymi</li><li>tworzenie jednej (1) własnej grupy</li><li>dołączanie do maksymalnie trzech (3) grup jednocześnie</li><li>wybór do 10 zainteresowań w profilu</li><li>5 awatarów AI miesięcznie</li></ul></section>
    <section class="planCard"><h4>PREMIUM</h4><ul><li>rozmowy 1:1 ze znajomymi</li><li>tworzenie do trzech (3) własnych grup</li><li>brak limitu dołączania do grup</li><li>możliwość dodawania znajomych do grup</li><li>wybór do 20 zainteresowań w profilu</li><li>15 awatarów AI miesięcznie</li><li>oznaczenie Trenera w maks. 2 zainteresowaniach</li></ul></section>
    <section class="planCard"><h4>VIP</h4><ul><li>rozmowy 1:1 ze znajomymi</li><li>tworzenie grup bez limitu</li><li>brak limitów w grupach i kontaktach</li><li>dodawanie znajomych do grup</li><li>nieograniczona liczba zainteresowań w profilu</li><li>30 awatarów AI miesięcznie</li><li>oznaczenie Trenera w maks. 5 zainteresowaniach</li></ul></section>
  </div>
</div>

<div class="planSection">
  <h3>Plany Organizatora</h3>
  <div class="planGrid">
    <section class="planCard"><h4>Free</h4><ul><li>maksymalnie 2 aktywne Wydarzenia jednocześnie</li><li>podstawowy podgląd panelu: aktywne Wydarzenia</li><li>brak wiadomości do uczestników Wydarzeń</li><li>brak broadcastu i brak wyróżnienia Wydarzeń</li><li>1 hashtag/kategoria na Wydarzenie</li></ul></section>
    <section class="planCard"><h4>PRO</h4><ul><li>maksymalnie 5 aktywnych Wydarzeń jednocześnie</li><li>rozszerzony podgląd panelu: aktywne Wydarzenia, szkice i zapisy łącznie</li><li>możliwość wysyłania wiadomości do uczestników Wydarzeń</li><li>brak broadcastu i brak wyróżnienia Wydarzeń</li><li>do 2 hashtagów/kategorii na Wydarzenie</li></ul></section>
    <section class="planCard"><h4>PREMIUM</h4><ul><li>nielimitowana liczba aktywnych Wydarzeń</li><li>pełny podgląd panelu: aktywne Wydarzenia, szkice, zapisy łącznie i frekwencja</li><li>możliwość wysyłki broadcastu do uczestników</li><li>wyróżnienie wydarzeń w aplikacji</li><li>do 5 hashtagów/kategorii na Wydarzenie</li></ul></section>
    <section class="planCard"><h4>ENTERPRISE</h4><ul><li>nielimitowana liczba aktywnych Wydarzeń</li><li>pełny podgląd panelu: aktywne Wydarzenia, szkice, zapisy łącznie i frekwencji</li><li>możliwość wysyłki broadcastu do uczestników</li><li>wyróżnienie wydarzeń w aplikacji</li><li>do 5 hashtagów/kategorii na Wydarzenie</li><li>obsługa wielu scenariuszy i działań niestandardowych</li><li>najpełniejszy zakres raportowania i komunikacji</li><li>zakres wdrożenia ustalany indywidualnie</li><li>indywidualny zakres hashtagów/kategorii wydarzeń</li></ul></section>
  </div>
</div>

<p class="clause">4. Administrator może okresowo oferować promocje, rabaty lub okresy próbne, których warunki będą każdorazowo określane w Aplikacji.</p>
<p class="clause">5. Rejestracja Konta: po wyborze Profilu i Planu Płatności oraz podaniu wymaganych informacji tworzone jest Konto Użytkownika.</p>
<p class="letter-item">a) Konto Organizatora wymaga podania następujących danych: adres email, nazwa miejsca / firmy, hasło, miasto.</p>
<p class="letter-item">b) Konto Towarzysza wymaga podania następujących danych: email, nick / imię publicznie widoczne, hasło, data urodzenia, lokalizacja / miasto.</p>
<p class="clause">6. Konto zostanie zarejestrowane po wyrażeniu zgody na warunki Regulaminu i Polityki Prywatności oraz zweryfikowaniu adresu email. Aktywacja konta następuje poprzez kliknięcie linku aktywacyjnego przesłanego na adres e-mail podany podczas rejestracji.</p>
<p class="clause">7. Funkcja resetu hasła wymaga potwierdzenia tożsamości za pomocą adresu e-mail przypisanego do konta.</p>
<p class="clause">8. Administrator rejestruje informacje o aktywacji Konta oraz operacjach związanych z bezpieczeństwem w zakresie niezbędnym do ochrony użytkowników i systemu.</p>
<p class="clause">9. Kolejne użycie Aplikacji wymagać będzie zalogowania w Aplikacji poprzez podanie Nazwy (nicku) i hasła.</p>
<p class="clause">10. Dane Profilu: Użytkownik może dobrowolnie uzupełnić swój Profil o dane, które ułatwiają innym Użytkownikom nawiązać interakcję tj. logo, miasto, charakterystyka miejsca, klimat, kategoria i opis miejsca (w przypadku Organizatora) lub informacje dotyczące zainteresowań (w przypadku Towarzysza). Profil może zawierać w szczególności:</p>
<p class="letter-item">a) zdjęcie profilowe,</p>
<p class="letter-item">b) avatar wygenerowany przez narzędzia AI na podstawie opisu Użytkownika,</p>
<p class="letter-item">c) automatycznie wygenerowany znak graficzny zawierający pierwszą literę imienia lub nazwy użytkownika,</p>
<p class="letter-item">d) opis BIO o długości do 250 znaków,</p>
<p class="letter-item">e) zainteresowania,</p>
<p class="letter-item">f) dodatkowe informacje udostępniane przez Użytkownika.</p>
<p>Użytkownik może w dowolnym momencie edytować opisy swojego Profilu. Wskazanie zainteresowań jest opcjonalne, lecz rekomendowane w celu poprawy jakości dopasowań i rekomendacji.</p>
<p class="clause">11. Użytkownik może przełączać się pomiędzy dostępnymi Profilami Towarzysza i Organizatora w zakresie przewidzianym przez funkcjonalności Aplikacji. Szczegółowy zakres funkcji przypisanych do poszczególnych ról określany jest w interfejsie Aplikacji.</p>
"""

en_section = """
<h2 id="3-user-profile-and-payment-plans">§ 3. User Profile and Payment Plans</h2>
<p class="clause">1. During the registration process, the User selects the Profile they are interested in, which determines the available features for using the App and the Payment Packages. These options may be changed at any time.</p>
<p class="clause">2. Users may create the following Profile within the App:</p>
<p class="letter-item">a) Companion — by selecting access to the “Meet People” account,</p>
<p class="letter-item">b) Organiser — by selecting access to the “Create Events” account.</p>

<p class="clause">3. After selecting a Profile, the User selects a Payment Plan. The App is available in a free version and as paid Plans — subscriptions, renewed on a monthly basis. Prices for individual Plans may vary. Prices are always stated in the description of the relevant Plan within the App’s features. The detailed scope of functionality, prices, billing periods and any discounts are displayed in the App before a purchase is made.</p>
<p class="clause">Purchases of paid plans are made via the Apple App Store and Google Play. Billing, subscription renewal and cancellation are subject to the terms and conditions of the Apple App Store and Google Play respectively.</p>

<div class="planSection">
  <h3>Companion Plans</h3>
  <div class="planGrid">
    <section class="planCard"><h4>FREE</h4><ul><li>1:1 chats with friends</li><li>the ability to join one (1) group at a time</li><li>cannot create your own groups</li><li>choice of up to 5 interests on your profile</li><li>1 AI avatar per month</li></ul></section>
    <section class="planCard"><h4>PLUS</h4><ul><li>1:1 chats with friends</li><li>the ability to create one (1) group of your own</li><li>join up to three (3) groups at the same time</li><li>selection of up to 10 interests on your profile</li><li>5 AI avatars per month</li></ul></section>
    <section class="planCard"><h4>PREMIUM</h4><ul><li>1:1 chats with friends</li><li>create up to three (3) of your own groups</li><li>no limit on joining groups</li><li>the ability to add friends to groups</li><li>choose up to 20 interests on your profile</li><li>15 AI avatars per month</li><li>tag a Coach in up to 2 interests</li></ul></section>
    <section class="planCard"><h4>VIP</h4><ul><li>1:1 chats with friends</li><li>Unlimited group creation</li><li>no limits on groups or contacts</li><li>adding friends to groups</li><li>unlimited interests on your profile</li><li>30 AI avatars per month</li><li>tag the Coach in up to 5 interests</li></ul></section>
  </div>
</div>

<div class="planSection">
  <h3>Organiser Plans</h3>
  <div class="planGrid">
    <section class="planCard"><h4>Free</h4><ul><li>a maximum of 2 active Events at any one time</li><li>basic dashboard view: active Events</li><li>no messages to Event participants</li><li>No broadcasts and no featured Events</li><li>1 hashtag/category per Event</li></ul></section>
    <section class="planCard"><h4>PRO</h4><ul><li>up to 5 active Events at the same time</li><li>extended dashboard view: active Events, drafts and registrations combined</li><li>ability to send messages to Event participants</li><li>no broadcast feature and no Event highlights</li><li>up to 2 hashtags/categories per Event</li></ul></section>
    <section class="planCard"><h4>PREMIUM</h4><ul><li>Unlimited number of active Events</li><li>full dashboard overview: active Events, drafts, total registrations and attendance</li><li>ability to send broadcasts to participants</li><li>event highlights in the app</li><li>up to 5 hashtags/categories per Event</li></ul></section>
    <section class="planCard"><h4>ENTERPRISE</h4><ul><li>Unlimited number of active Events</li><li>full dashboard overview: active Events, drafts, total registrations and attendance</li><li>ability to send a broadcast to participants</li><li>Event highlights in the app</li><li>up to 5 hashtags/categories per Event</li><li>support for multiple scenarios and custom actions</li><li>the most comprehensive scope of reporting and communication</li><li>scope of implementation determined on a case-by-case basis</li><li>customisable range of hashtags/event categories</li></ul></section>
  </div>
</div>

<p class="clause">4. The Administrator may periodically offer promotions, discounts or trial periods, the terms and conditions of which will be specified in the App on each occasion.</p>
<p class="clause">5. Account Registration: once a Profile and Payment Plan have been selected and the required information has been provided, a User Account is created.</p>
<p class="letter-item">a) An Organiser’s Account requires the following details: email address, venue/company name, password, town.</p>
<p class="letter-item">b) A Companion account requires the following details: email, nickname / first name publicly visible, password, date of birth, location / town.</p>
<p class="clause">6. Your account will be registered once you have agreed to the Terms and Conditions and Privacy Policy and verified your email address. To activate your account, click on the activation link sent to the email address you provided during registration.</p>
<p class="clause">7. The password reset function requires identity verification via the email address associated with the account.</p>
<p class="clause">8. The administrator records information regarding account activation and security-related operations to the extent necessary to protect users and the system.</p>
<p class="clause">9. Subsequent use of the App will require you to log in by entering your username (nickname) and password.</p>
<p class="clause">10. Profile details: Users may voluntarily add details to their Profile to help other Users interact with them, such as a logo, city, location characteristics, atmosphere, category and description of the venue (in the case of an Organiser) or information regarding interests (in the case of a Companion). The profile may include, in particular:</p>
<p class="letter-item">a) a profile photo,</p>
<p class="letter-item">b) an avatar generated by AI tools based on the User’s description,</p>
<p class="letter-item">c) an automatically generated graphic symbol containing the first letter of the User’s first name or username,</p>
<p class="letter-item">d) a BIO description of up to 250 characters,</p>
<p class="letter-item">e) interests,</p>
<p class="letter-item">f) additional information provided by the User.</p>
<p>The User may edit their Profile descriptions at any time. Specifying interests is optional, but recommended to improve the quality of matches and recommendations.</p>
<p class="clause">11. The User may switch between the available Companion and Organiser Profiles to the extent permitted by the App’s functionality. The detailed scope of functions assigned to each role is specified within the App’s interface.</p>
"""

pl_text = replace_between(pl_text, '<h2 id="3-profil-u-ytkownika-i-plany-p-atno-ci">', '<h2 id="4-lokalizacja-i-zasi-g-wyszukiwania">', pl_section)
en_text = replace_between(en_text, '<h2 id="3-user-profile-and-payment-plans">', '<h2 id="4-location-and-search-range">', en_section)

pl.write_text(pl_text, encoding="utf-8")
en.write_text(en_text, encoding="utf-8")
print("OK polished §3 PL/EN")
