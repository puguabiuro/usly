
function avatarInitial(name){
  return String(name || "U").trim().charAt(0).toUpperCase() || "U";
}

function getAvatarGradient(name){
  const colors = [
    "linear-gradient(145deg,#2a2f3a,#3b4252)",
    "linear-gradient(145deg,#2c2c34,#444455)",
    "linear-gradient(145deg,#2b313c,#3f4a5a)",
    "linear-gradient(145deg,#2d2f36,#4a4f5c)",
    "linear-gradient(145deg,#2a2d33,#3e4452)"
  ];
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }
  return colors[Math.abs(hash) % colors.length];
}

function premiumAvatarStyle(bg){
  return `background:${bg};color:#f8fbff;border:1px solid rgba(255,255,255,.22);box-shadow:0 12px 30px rgba(0,0,0,.28),0 0 18px rgba(180,205,255,.16),inset 0 1px 0 rgba(255,255,255,.22),inset 0 -10px 22px rgba(255,255,255,.06);text-shadow:0 1px 10px rgba(255,255,255,.22);`;
}

function premiumBadge(label, seed){
  const safeLabel = escapeHtml(String(label || "•").slice(0, 2).toUpperCase());
  const bg = getAvatarGradient(seed || label || "USLY");
  return `<div class="userAvatarFallback" style="${premiumAvatarStyle(bg)}font-weight:900;letter-spacing:-0.04em;" data-name="${safeLabel}">${safeLabel}</div>`;
}

function premiumIcon(kind, seed){
  const bg = getAvatarGradient(seed || kind || "USLY");
  const icons = {
    group: `<circle cx="12" cy="12" r="4.2" fill="currentColor" opacity=".96"/><circle cx="21" cy="13.5" r="3.5" fill="currentColor" opacity=".72"/><path d="M6.5 24c1.4-4.2 4.2-6.3 8.1-6.3s6.7 2.1 8.1 6.3" stroke="currentColor" stroke-width="3" stroke-linecap="round" opacity=".96"/>`,
    chat: `<path d="M8 10.5c0-2 1.7-3.7 3.8-3.7h8.4c2.1 0 3.8 1.7 3.8 3.7v5.8c0 2-1.7 3.7-3.8 3.7h-4.4l-5.2 4.1v-4.1C9.1 19.6 8 18.1 8 16.3v-5.8z" fill="currentColor" opacity=".95"/>`,
    mail: `<path d="M7 10.5c0-1.4 1.1-2.5 2.5-2.5h13c1.4 0 2.5 1.1 2.5 2.5v10c0 1.4-1.1 2.5-2.5 2.5h-13A2.5 2.5 0 0 1 7 20.5v-10z" fill="currentColor" opacity=".94"/><path d="M9 11l7 5 7-5" stroke="#111827" stroke-opacity=".35" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>`,
    calendar: `<rect x="7" y="8.5" width="18" height="16" rx="4" fill="currentColor" opacity=".94"/><path d="M11 6.5v4M21 6.5v4M10 14h12" stroke="#111827" stroke-opacity=".35" stroke-width="2.2" stroke-linecap="round"/>`,
    org: `<path d="M9 24V9.5c0-1.2 1-2.2 2.2-2.2h9.6c1.2 0 2.2 1 2.2 2.2V24" fill="currentColor" opacity=".94"/><path d="M12 12h2.2M17.8 12H20M12 16h2.2M17.8 16H20M14 24v-4h4v4" stroke="#111827" stroke-opacity=".35" stroke-width="2.1" stroke-linecap="round"/>
`
  };
  return `<div class="userAvatarFallback" style="${premiumAvatarStyle("linear-gradient(145deg,rgba(255,255,255,.20),rgba(255,255,255,.07))")}backdrop-filter:blur(10px);"><svg width="28" height="28" viewBox="0 0 32 32" fill="none" aria-hidden="true">${icons[kind] || icons.chat}</svg></div>`;
}

/* =========================================================
USLY — JS FINAL (v11) — SPÓJNY Z HTML v11 (PL ONLY)
CEL: UI + przygotowanie pod backend (spójne ID, stan, hooki)
========================================================= */

/* ------------------------- API Config -------------------------- */
// Prod: ustawimy na URL backendu z Render (osobna domena)
// Local: http://127.0.0.1:8001 (jak dziś uruchamiasz uvicorn)
const IS_CAPACITOR_APP = !!window.Capacitor;

const API_BASE_URL =
  window.USLY_API_BASE_URL ||
  (IS_CAPACITOR_APP || location.hostname.includes("onrender.com") || location.hostname === "uslyapp.pl" || location.hostname === "www.uslyapp.pl"
    ? "https://api.uslyapp.pl"
    : "http://127.0.0.1:8000");

// expose for api.js (plain scripts)
window.API_BASE_URL = API_BASE_URL;


/* ------------------------- i18n -------------------------- */
const I18N = {
  pl: {
    "login.title": "Zaloguj się",
    "login.subtitle": "Zaloguj się, aby wejść do swojego konta.",
    "login.mode": "Tryb",
    "login.user": "Towarzysz",
    "login.partner": "Organizator",
    "login.email": "Email / nick",
    "login.password": "Hasło",
    "login.submit": "Zaloguj się",
    "login.or": "albo",
    "login.apple": "Kontynuuj z Apple",
    "login.google": "Kontynuuj z Google",
    "login.facebook": "Kontynuuj z Facebook",
    "login.email_placeholder": "np. ola_88 / ola@email.com",
    "login.no_account": "Nie masz konta? Zarejestruj się",
    "login.forgot_password": "Nie pamiętasz hasła?",
    "plans.title": "Plany",
    "plans.user.title": "Plany Towarzysza",
    "plans.user.subtitle": "Wybierz poziom dostępu dopasowany do tego, jak chcesz korzystać z USLY.",
    "plans.partner.title": "Plany Organizatora",
    "plans.partner.subtitle": "Wybierz poziom widoczności, raportów i narzędzi dla swojego miejsca lub marki.",
    "plans.choose": "Wybierz",
    "plans.continueFree": "Kontynuuj z FREE",
    "plans.continuePlus": "Kontynuuj z PLUS",
    "plans.continuePremium": "Kontynuuj z PREMIUM",
    "plans.continueVip": "Kontynuuj z VIP",
    "plans.continuePro": "Kontynuuj z PRO",
    "plans.recommendedStart": "✨ Polecany na start",
    "plans.recommendedOrganizer": "⭐ Polecany wybór",
    "plans.defaultStart": "✔ Polecany na początek",
    "plans.onboarding.topTitle": "Prawie gotowe!",
    "plans.onboarding.title": "Wybierz plan",
    "plans.onboarding.userSubtitle": "Wybierz plan, od którego chcesz rozpocząć korzystanie z USLY. Zawsze możesz go zmienić później.",
    "plans.onboarding.partnerSubtitle": "Wybierz plan, od którego chcesz rozpocząć tworzenie wydarzeń w USLY. Zawsze możesz go zmienić później.",
    "plans.promo.label": "Kod promocyjny",
    "plans.promo.placeholder": "Wpisz kod",
    "plans.promo.apply": "Zastosuj",
    "plans.restore.title": "Masz już aktywną subskrypcję?",
    "plans.restore.subtitle": "Zmieniasz telefon lub instalujesz aplikację ponownie? Odśwież zakup z App Store lub Google Play.",
    "plans.restore.button": "Przywróć zakup",
    "plans.restore.checking": "Sprawdzamy aktywne subskrypcje...",
    "plans.restore.notFound": "Nie znaleziono aktywnych zakupów dla tego konta.",
    "plans.restore.success": "Subskrypcja została odświeżona.",
    "plans.restore.failed": "Nie udało się przywrócić zakupów. Spróbuj ponownie.",
    "plans.promo.applied": "Kod zastosowany",
    "plans.promo.invalid": "Nie udało się zastosować kodu.",
    "plans.promo.notActive": "Ten kod nie jest już aktywny.",
    "plans.promo.expired": "Ten kod wygasł.",
    "plans.promo.limitReached": "Limit użyć tego kodu został osiągnięty.",
    "plans.promo.wrongRole": "Ten kod nie jest dostępny dla tej roli.",
    "plans.promo.discount": "Zniżka {{value}}% przez {{months}} mies.",
    "plans.contact_us": "Napisz do nas",
    "plans.payment.storeComingSoon": "Płatności sklepowe są w przygotowaniu. Ten plan będzie aktywowany po zakupie przez App Store lub Google Play.",
    "plans.payment.cancelled": "Zakup został anulowany.",
    "plans.payment.notConfigured": "Płatności sklepowe nie są jeszcze skonfigurowane.",
    "plans.payment.nativeOnly": "Przywracanie zakupów jest dostępne tylko w aplikacji mobilnej USLY.",
    "plans.payment.pluginMissing": "Moduł płatności nie jest dostępny w tej wersji aplikacji.",
    "plans.payment.productUnavailable": "Ten produkt nie jest jeszcze dostępny w sklepie.",
    "plans.payment.transactionMissing": "Sklep nie zwrócił identyfikatora transakcji. Spróbuj ponownie.",
    "plans.payment.verifyNotConfigured": "Weryfikacja płatności nie jest jeszcze skonfigurowana.",
    "plans.payment.networkError": "Nie udało się połączyć ze sklepem. Spróbuj ponownie.",
    "plans.payment.failed": "Nie udało się zakończyć płatności. Spróbuj ponownie.",
    "plans.payment.success": "Plan został aktywowany.",
    "plans.current": "Aktualny plan",
    "plans.user.free.desc": "Podstawowe korzystanie z USLY i poznawanie ludzi w Twojej okolicy.",
    "plans.user.plus.desc": "Większa swoboda w poznawaniu ludzi i korzystaniu z grup.",
    "plans.user.premium.desc": "Pełniejsze korzystanie z USLY i rozwijanie swojej sieci znajomości.",
    "plans.user.vip.desc": "Maksymalne możliwości i pełna swoboda w USLY.",
    "plans.partner.free.desc": "Plan na start dla organizatorów, którzy chcą sprawdzić USLY i uruchomić pierwsze działania bez kosztu stałego.",
    "plans.partner.pro.desc": "Dla organizatorów, którzy prowadzą wydarzenia regularnie i chcą sprawniej zarządzać relacją z uczestnikami.",
    "plans.partner.premium.desc": "Dla organizatorów, którzy chcą skalować działania, pracować na pełnych danych i mocniej promować swoje wydarzenia.",
    "plans.partner.enterprise.desc": "Dla większych partnerów, sieci i marek, które potrzebują indywidualnego zakresu działań, raportowania i wdrożenia.",
    "plans.user.free.feature1": "Rozmowy 1:1 ze znajomymi",
    "plans.user.free.feature2": "Dołączanie do 1 grupy jednocześnie",
    "plans.user.free.feature3": "Brak możliwości tworzenia własnych grup",
    "plans.user.free.feature4": "Do 5 zainteresowań w profilu",
    "plans.user.free.feature5": "1 awatar AI miesięcznie",
    "plans.user.plus.feature1": "Tworzenie 1 własnej grupy",
    "plans.user.plus.feature2": "Dołączanie do maks. 3 grup",
    "plans.user.plus.feature3": "Do 10 zainteresowań w profilu",
    "plans.user.plus.feature4": "Lepsza swoboda korzystania z aplikacji na co dzień",
    "plans.user.plus.feature5": "5 awatarów AI miesięcznie",
    "plans.user.premium.feature1": "Tworzenie do 3 własnych grup",
    "plans.user.premium.feature2": "Brak limitu dołączania do grup",
    "plans.user.premium.feature3": "Dodawanie znajomych do grup",
    "plans.user.premium.feature4": "Do 20 zainteresowań w profilu",
    "plans.user.premium.feature5": "15 awatarów AI miesięcznie",
    "plans.user.premium.feature6": "Oznaczenie trenera w maks. 2 zainteresowaniach",
    "plans.user.vip.feature1": "Tworzenie grup bez limitu",
    "plans.user.vip.feature2": "Brak limitów w grupach i kontaktach",
    "plans.user.vip.feature3": "Dodawanie znajomych do grup",
    "plans.user.vip.feature4": "Nieograniczona liczba zainteresowań",
    "plans.user.vip.feature5": "30 awatarów AI miesięcznie",
    "plans.user.vip.feature6": "Oznaczenie trenera w maks. 5 zainteresowaniach",
    "plans.price.free": "0 zł",
    "plans.partner.free.price": "0 zł",
    "plans.partner.pro.price": "129 zł / miesiąc",
    "plans.partner.premium.price": "259 zł / miesiąc",
    "plans.partner.enterprise.price": "Indywidualnie",
    "plans.partner.free.feature1": "Maksymalnie 2 aktywne wydarzenia jednocześnie",
    "plans.partner.free.feature2": "Podstawowy podgląd panelu: aktywne wydarzenia",
    "plans.partner.free.feature3": "Brak wiadomości do uczestników",
    "plans.partner.free.feature4": "Brak broadcastu i brak wyróżnienia wydarzeń",
    "plans.partner.free.feature5": "1 hashtag/kategoria na wydarzenie",
    "plans.partner.pro.feature1": "Maksymalnie 5 aktywnych wydarzeń jednocześnie",
    "plans.partner.pro.feature2": "Rozszerzony podgląd panelu: aktywne, szkice i zapisy łącznie",
    "plans.partner.pro.feature3": "Możliwość pisania do uczestników",
    "plans.partner.pro.feature4": "Bez broadcastu i bez wyróżnienia wydarzeń",
    "plans.partner.pro.feature5": "Do 2 hashtagów/kategorii na wydarzenie",
    "plans.partner.premium.feature1": "Nielimitowana liczba aktywnych wydarzeń",
    "plans.partner.premium.feature2": "Pełny podgląd panelu: aktywne, szkice, zapisy łącznie i frekwencja",
    "plans.partner.premium.feature3": "Możliwość wysyłki broadcastu do uczestników",
    "plans.partner.premium.feature4": "Wyróżnienie wydarzeń w aplikacji",
    "plans.partner.premium.feature5": "Do 5 hashtagów/kategorii na wydarzenie",
    "plans.partner.enterprise.feature1": "Wszystko z planu PREMIUM",
    "plans.partner.enterprise.feature2": "Obsługa wielu scenariuszy i działań niestandardowych",
    "plans.partner.enterprise.feature3": "Najpełniejszy zakres raportowania i komunikacji",
    "plans.partner.enterprise.feature4": "Zakres wdrożenia ustalany indywidualnie",
    "plans.partner.enterprise.feature5": "Indywidualny zakres hashtagów/kategorii wydarzeń",
    "enterprise.modal.title": "Plan Enterprise",
    "enterprise.modal.heading": "Porozmawiajmy o pakiecie dla Twojej marki",
    "enterprise.modal.subtitle": "Zostaw kontakt i zaznacz, czego potrzebujesz. Przygotujemy indywidualną propozycję dla Twojego miejsca, wydarzeń lub sieci lokalizacji.",
    "enterprise.company.label": "Nazwa firmy / marki",
    "enterprise.company.placeholder": "np. klub, restauracja, sieć miejsc",
    "enterprise.city.label": "Miasto / zasięg działania",
    "enterprise.city.placeholder": "np. Warszawa, kilka miast, cała Polska",
    "enterprise.contact.label": "Email lub telefon do kontaktu",
    "enterprise.contact.placeholder": "np. kontakt@firma.pl lub numer telefonu",
    "enterprise.interests.label": "Czym jesteście zainteresowani?",
    "enterprise.message.label": "Krótka wiadomość",
    "enterprise.message.placeholder": "Napisz krótko, czego potrzebujesz albo jaki efekt chcesz osiągnąć.",
    "enterprise.submit": "Wyślij zapytanie",
    "enterprise.need.visibility": "Większa widoczność wydarzeń",
    "enterprise.need.locations": "Promocja kilku lokalizacji",
    "enterprise.need.campaign": "Kampania lub event specjalny",
    "enterprise.need.long_term": "Współpraca długoterminowa",
    "enterprise.need.network": "Oferta dla sieci lub franczyzy",
    "enterprise.need.other": "Inne",
    "common.email": "Email",
    "common.remove": "Usuń",
    "common.block": "Zablokuj",
    "profileEdit.title": "Edytuj profil",
    "profileEdit.photoTitle": "Zdjęcie profilowe",
    "profileEdit.photoSubtitle": "Dodaj swoje zdjęcie albo wygeneruj awatar AI.",
    "profileEdit.photoBtn": "Zdjęcie",
    "profileEdit.aiAvatarBtn": "Awatar AI",
    "profileEdit.nick": "Nick",
    "profileEdit.nick_placeholder": "np. Ola_88",
    "profileEdit.bio": "BIO",
    "profileEdit.bio_placeholder": "Krótko, lekko, z charakterem",
    "profileEdit.location": "Aktualna lokalizacja",
    "profileEdit.radius": "Zasięg okolicy",
    "profileEdit.radius5": "Do 5 km",
    "profileEdit.radius10": "Do 10 km",
    "profileEdit.radius25": "Do 25 km",
    "profileEdit.radius50": "Do 50 km",
    "profileEdit.radius100": "Do 100 km",
    "profileEdit.ageRangeTitle": "Preferowany zakres wieku",
    "profileEdit.ageRangeText": "Dopasuj preferowany wiek osób, które chcesz widzieć.",
    "profileEdit.ageFrom": "Od",
    "profileEdit.ageTo": "Do",
    "profileEdit.ageAny": "Wiek bez znaczenia",
    "profileEdit.save": "Zapisz zmiany",
    "profileInterests.title": "Zainteresowania",
    "profileInterests.subtitle": "Jedna wspólna baza tagów dla profilu, grup i wydarzeń.",
    "profileInterests.tags": "Twoje tagi",
    "profileInterests.placeholder": "np. kawa, joga, koncerty...",
    "profileInterests.limitPlaceholder": "Limit osiągnięty • Odblokuj więcej w PLUS",
    "profileInterests.limitToast": "Odblokuj więcej zainteresowań w planie PLUS",
    "profileInterests.trainerTitle": "Prowadzisz zajęcia lub warsztaty?",
    "profileInterests.trainerSubtitle": "Wyróżnij zainteresowania, w których prowadzisz zajęcia, warsztaty lub pomagasz innym rozwijać umiejętności.",
    "profileInterests.trainerPremiumLimit": "Premium: maks. 2 oznaczenia prowadzącego",
    "profileInterests.trainerVipLimit": "VIP: maks. 5 oznaczeń prowadzącego",
    "profileInterests.trainerLocked": "Opcja dostępna w planach Premium i VIP",
    "profileInterests.trainerBadge": "Prowadzący",
    "profileInterests.leadsClassesTitle": "Prowadzi zajęcia w:",
    "profileInterests.leadsNearbyLabel": "Prowadzi zajęcia",
    "profileInterests.trainerLimitToast": "Osiągnięto limit oznaczeń prowadzącego w Twoim planie",
    "profileInterests.alreadyAdded": "To zainteresowanie już jest dodane",
    "profileInterests.addedToast": "Dodano #{{tag}}",
    "profileInterests.removedToast": "Usunięto #{{tag}}",
    "profileInterests.removeTitle": "Kliknij, aby usunąć",
    "geo.unavailable": "Geolokalizacja niedostępna w tej przeglądarce",
    "geo.fetching": "Pobieram lokalizację…",
    "geo.fetchingCity": "Pobieramy miasto...",
    "geo.locationFetched": "Lokalizacja pobrana",
    "geo.locationSet": "Lokalizacja ustawiona",
    "geo.enableLocation": "Włącz lokalizację, aby kontynuować",
    "geo.failed": "Nie udało się pobrać lokalizacji (brak zgody?)",
    "profileFriends.title": "Znajomi",
    "profileFriends.search_placeholder": "Szukaj znajomego...",
    "profileInvites.title": "Zaproszenia",
    "profileInvites.subtitle": "Przychodzące i wysłane zaproszenia w czytelnym układzie.",
    "friends.selfAccount": "To Twoje konto",
    "friends.friend": "Znajomy",
    "friends.pending": "Zaproszenie wysłane",
    "friends.add": "Dodaj do znajomych",
    "friends.message": "Napisz",
    "friends.messagesPro": "Wiadomości od planu PRO",
    "friends.toastNoProfile": "Nie wybrano profilu",
    "friends.toastLogin": "Najpierw się zaloguj",
    "friends.toastSendFailed": "Nie udało się wysłać zaproszenia",
    "friends.toastSent": "Zaproszenie do znajomych zostało wysłane",
    "friends.toastChatAfterAccept": "Prywatny czat będzie dostępny po akceptacji znajomości",
    "friends.toastAddFirst": "Najpierw dodaj tę osobę do znajomych",
    "friends.toastProfileUnavailable": "Profil tej osoby nie jest teraz dostępny",
    "friends.emptyInvites": "Brak oczekujących zaproszeń.",
    "friends.defaultUser": "Użytkownik #{{id}}",
    "friends.pendingDecision": "Zaproszenie oczekuje na decyzję.",
    "friends.pendingAccept": "Zaproszenie wysłane — oczekuje na akceptację.",
    "friends.accept": "Akceptuj",
    "friends.reject": "Odrzuć",
    "friends.sentPill": "Wysłane",
    "friends.defaultGroup": "Grupa",
    "friends.groupInviteLine": "{{user}} zaprasza Cię do grupy",
    "friends.emptyFriends": "Nie masz jeszcze znajomych.",
    "friends.friendFallback": "Znajomy w USLY",
    "friends.viewProfile": "Zobacz profil",
    "friends.groupInviteMissing": "Brak danych zaproszenia do grupy",
    "friends.groupInviteUpdateFailed": "Nie udało się zaktualizować zaproszenia do grupy",
    "friends.groupInviteAccepted": "Zaproszenie do grupy zaakceptowane",
    "friends.groupInviteRejected": "Zaproszenie do grupy odrzucone",
    "friends.groupInviteConnectionFailed": "Błąd połączenia przy aktualizacji zaproszenia do grupy",
    "friends.inviteUpdateFailed": "Nie udało się zaktualizować zaproszenia",
    "friends.inviteAccepted": "Zaproszenie zaakceptowane",
    "friends.inviteRejected": "Zaproszenie odrzucone",
    "friends.inviteConnectionFailed": "Błąd połączenia przy aktualizacji zaproszenia",
    "profileSetup.topbar": "Profil",
    "profileSetup.title": "Uzupełnij profil",
    "profileSetup.subtitle": "To ostatni krok po rejestracji. Sprawdź dane startowe i dodaj brakujące informacje do dopasowań.",
    "profileSetup.startProfile": "Twój profil startowy",
    "profileSetup.addPhoto": "Dodaj zdjęcie",
    "profileSetup.createAvatar": "Stwórz awatar",
    "profileSetup.removePhoto": "Usuń zdjęcie",
    "profileSetup.nickPlaceholder": "Twój nick",
    "profileSetup.interestsPlaceholder": "np. kawa, koncerty...",
    "profileSetup.addInterest": "Dodaj",
    "profileSetup.bioLabel": "BIO (max 250)",
    "profileSetup.ageRangeText": "Ustaw, w jakim wieku mają być osoby sugerowane przez aplikację. Możesz to później zmienić w ustawieniach.",
    "profileSetup.finish": "Zapisz i przejdź dalej",
    "partnerSetup.topbar": "Profil",
    "partnerSetup.title": "Uzupełnij profil",
    "partnerSetup.subtitle": "Logo, miasto i charakter miejsca.",
    "partnerSetup.identityTitle": "Tożsamość miejsca",
    "partnerSetup.addLogo": "Dodaj logo",
    "partnerSetup.city": "Miasto działania",
    "partnerSetup.cityPlaceholder": "np. Warszawa",
    "partnerSetup.vibeTitle": "Klimat miejsca",
    "partnerSetup.vibeSubtitle": "Pokaż użytkownikom, czego mogą się spodziewać.",
    "partnerSetup.category": "Kategoria",
    "partnerCategory.gastro": "Gastro / restauracja / kawiarnia",
    "partnerCategory.bar_nocne": "Bar / klub / nightlife",
    "partnerCategory.kultura": "Kultura / koncerty / sztuka",
    "partnerCategory.fitness": "Fitness / sport / wellness",
    "partnerCategory.beauty": "Beauty / uroda",
    "partnerCategory.hotel_event": "Hotel / event / konferencje",
    "partnerCategory.rozrywka": "Rozrywka / atrakcje / gaming",
    "partnerCategory.zakupy": "Sklep / showroom / zakupy",
    "partnerCategory.edukacja": "Edukacja / warsztaty",
    "partnerCategory.cowork": "Cowork / biznes / networking",
    "partnerCategory.plener": "Plener / turystyka / rekreacja",
    "partnerCategory.inne": "Inne / trudno powiedzieć",
    "partnerSetup.about": "Krótki opis",
    "partnerSetup.aboutPlaceholder": "Co warto wiedzieć o tym miejscu?",
    "nearby.title": "W okolicy",
    "nearby.mapSub": "Kliknij znacznik, aby podejrzeć osobę lub wydarzenie.",
    "nearby.peopleTitle": "Ludzie w okolicy",
    "nearby.peopleSub": "Lista na podstawie lokalizacji.",
    "nearby.peoplePlaceholder": "np. Alex / Maja",
    "nearby.eventsTitle": "Wydarzenia w okolicy",
    "nearby.eventsSub": "Kliknij kartę, aby wejść w szczegóły.",
    "nearby.emptyPeople": "Nie widzimy jeszcze osób z wspólnymi zainteresowaniami w Twojej okolicy.",
    "nearby.emptyEvents": "Nie widzimy jeszcze wydarzeń zgodnych z Twoimi zainteresowaniami w Twojej okolicy.",
    "nearby.distanceUnder1": "< 1 km od Ciebie",
    "nearby.distanceKm": "{{km}} km od Ciebie",
    "nearby.inArea": "W okolicy",
    "personProfile.bioTitle": "O mnie",
    "personProfile.partnerCategory": "Kategoria",
    "personProfile.organizer": "Organizator",
    "personProfile.organizerAboutTitle": "O organizatorze",
    "personProfile.emptyOrganizerBio": "Ten organizator nie dodał jeszcze opisu.",
    "personProfile.defaultEvent": "Wydarzenie",
    "personProfile.eventSoon": "Termin wkrótce",
    "personProfile.noPartnerEvents": "Ten organizator nie ma jeszcze widocznych wydarzeń.",
    "personProfile.userProfileFallback": "Profil użytkownika",
    "personProfile.ageYears": "{{age}} lat",
    "personProfile.match": "{{score}}% dopasowania",
    "personProfile.message": "Napisz",
    "personProfile.messagesPro": "Wiadomości od planu PRO",
    "personProfile.options": "Opcje",
    "personProfile.report": "Zgłoś",
    "personProfile.block": "Zablokuj",
    "personProfile.toastMissingUser": "Brak danych użytkownika",
    "personProfile.toastBlockFailed": "Nie udało się zablokować użytkownika",
    "personProfile.toastBlocked": "Użytkownik został zablokowany",
    "personProfile.toastConnectionError": "Błąd połączenia",
    "userReport.modalTitle": "Zgłoś użytkownika",
    "userReport.reasonTitle": "Powód zgłoszenia",
    "userReport.subtitle": "Zgłoszenie trafi do moderacji USLY.",
    "userReport.reasonLabel": "Wybierz powód",
    "userReport.reasonSpam": "Spam / scam",
    "userReport.reasonHarassment": "Nękanie lub obraźliwe treści",
    "userReport.reasonProfile": "Nieodpowiedni profil lub bio",
    "userReport.reasonImpersonation": "Podszywanie się",
    "userReport.reasonOther": "Inne",
    "userReport.descriptionLabel": "Opis opcjonalny",
    "userReport.descriptionPlaceholder": "Dodaj szczegóły, które pomogą moderacji.",
    "userReport.submit": "Wyślij zgłoszenie",
    "userReport.toastNoUser": "Nie wybrano użytkownika",
    "userReport.toastNoReason": "Wybierz powód zgłoszenia",
    "userReport.toastFailed": "Nie udało się wysłać zgłoszenia",
    "userReport.toastSent": "Zgłoszenie wysłane • #{{ticket}}",
    "personProfile.emptyBio": "Ta osoba nie dodała jeszcze bio.",
    "personProfile.organizerEvents": "Wydarzenia organizatora",
    "personProfile.write": "Napisz",
    "personProfile.addFriend": "Dodaj do znajomych",
    "chats.title": "Czaty",
    "chats.searchTitle": "Szukaj czatów",
    "chats.searchSub": "Po nazwie rozmowy",
    "chats.searchPlaceholder": "np. Alex",
    "chatThread.placeholder": "Napisz wiadomość.",
    "chatThread.newMessages": "Nowe wiadomości",
    "chat.menu.title": "Menu czatu",
    "chat.menu.notificationsOn": "Włącz powiadomienia",
    "chat.menu.notificationsOff": "Wycisz rozmowę",
    "chat.toast.notificationsOn": "Powiadomienia dla rozmowy zostały włączone",
    "chat.toast.notificationsMuted": "Rozmowa została wyciszona",
    "chat.toast.sendFailed": "Nie udało się wysłać wiadomości",
    "chat.blocked.link": "Linki są obecnie blokowane ze względów bezpieczeństwa USLY. Wiadomość nie została dostarczona.",
    "chat.blocked.content": "Treść została zablokowana przez moderację USLY i nie została dostarczona.",
    "chat.avatarMine": "Twój awatar",
    "chat.openProfile": "Otwórz profil",
    "chat.defaultUser": "Użytkownik",
    "chat.organizerMessage": "Wiadomość od organizatora",
    "chat.organizerMessageMarker": "— wiadomość od organizatora —",
    "chat.defaultEventTitle": "📣 Wydarzenie",
    "chat.checkingContent": "Sprawdzamy treść wiadomości…",
    "groups.menu.title": "Menu grupy",
    "groups.menu.notificationsOn": "Włącz powiadomienia",
    "groups.menu.notificationsOff": "Wycisz grupę",
    "groups.menu.people": "Ludzie w grupie",
    "groups.menu.close": "Zamknij grupę",
    "groups.menu.leave": "Opuść grupę",
    "groups.toast.notificationsOn": "Powiadomienia dla grupy zostały włączone",
    "groups.toast.notificationsMuted": "Grupa została wyciszona",
    "groups.toast.joined": "Dołączono do grupy",
    "groups.toast.joinFailed": "Nie udało się dołączyć do grupy",
    "groups.toast.joinConnectionFailed": "Błąd dołączania do grupy",
    "groups.toast.closed": "Grupa została zamknięta",
    "groups.toast.closeFailed": "Nie udało się zamknąć grupy",
    "groups.toast.closeConnectionFailed": "Błąd zamykania grupy",
    "groups.toast.left": "Opuszczono grupę",
    "groups.toast.leaveFailed": "Nie udało się opuścić grupy",
    "groups.toast.leaveConnectionFailed": "Błąd opuszczania grupy",
    "groups.toast.inviteMissing": "Brak danych zaproszenia",
    "groups.toast.inviteSent": "Zaproszenie do grupy zostało wysłane",
    "groups.toast.inviteFailed": "Nie udało się wysłać zaproszenia do grupy",
    "groupThread.placeholder": "Napisz w grupie.",
    "groupThread.sendAria": "Wyślij wiadomość do grupy",
    "groupThread.join": "Dołącz do grupy",
    "groupThread.defaultDesc": "Grupa oparta na wspólnych zainteresowaniach.",
    "groupThread.joinToRead": "Dołącz do grupy, aby zobaczyć rozmowę i napisać wiadomość.",
    "groupThread.loading": "Ładowanie wiadomości...",
    "groupThread.empty": "Nie ma jeszcze wiadomości w tej grupie. Napisz jako pierwsza osoba.",
    "groupThread.newMessages": "Nowe wiadomości",
    "groupThread.me": "Ty",
    "groupThread.loadFailed": "Nie udało się załadować wiadomości grupy.",
    "groupThread.joinToWrite": "Dołącz do grupy, aby pisać wiadomości",
    "groupThread.limitReached": "Limit grup dla Twojego planu został osiągnięty",
    "events.title": "Wydarzenia",
    "events.forYou": "Dla Ciebie",
    "events.myEvents": "Moje wydarzenia",
    "events.searchPlaceholder": "Szukaj po nazwie / # (np. muzyka)",
    "events.emptyForYou": "Na razie nie ma nowych wydarzeń dopasowanych do Twoich zainteresowań.",
    "events.emptyFollowed": "Nie masz jeszcze zapisanych ani obserwowanych wydarzeń.",
    "eventDetail.kicker": "Wydarzenie",
    "eventDetail.description": "Opis wydarzenia",
    "eventDetail.emptyDescription": "Organizator nie dodał jeszcze opisu wydarzenia.",
    "eventDetail.place": "Miejsce",
    "eventDetail.mapPlaceholder": "Dokładny adres pojawi się tutaj.",
    "eventDetail.organizer": "Organizator",
    "eventDetail.tickets": "Bilety",
    "eventDetail.ticketLink": "Przejdź do zakupu / rezerwacji",
    "eventDetail.ticketLegal": "USLY nie sprzedaje biletów i nie jest organizatorem tego wydarzenia. Link przenosi do zewnętrznej strony, na której organizator prowadzi sprzedaż lub rezerwacje.",
    "eventDetail.locationSaved": "Lokalizacja wydarzenia zapisana na mapie",
    "eventDetail.locationMissing": "Dokładna lokalizacja nie została jeszcze wybrana",
    "eventCapacity.signed": "{{count}} zapisanych",
    "eventCapacity.used": "{{taken}} z {{capacity}} miejsc zajętych",
    "eventCapacity.full": "Komplet miejsc",
    "eventCapacity.lastOne": "Zostało ostatnie miejsce",
    "eventCapacity.lastFew": "Zostały ostatnie {{count}} miejsca",
    "eventDetail.organizer": "Organizator",
    "eventDetail.organizerMeta": "Organizator wydarzenia",
    "eventDetail.ticketFree": "Bezpłatne",
    "eventDetail.ticketFixed": "Płatne — cena stała",
    "eventDetail.ticketRange": "Płatne — przedział",
    "eventDetail.ticketPaid": "Płatne",
    "eventDetail.savedChip": "Obserwowane",
    "eventDetail.interestedChip": "Biorę udział",
    "eventDetail.priceLine": "Cena: {{price}} zł (zakup / rezerwacja poza aplikacją).",
    "eventDetail.priceRangeLine": "Cena: {{from}}–{{to}} zł (zakup / rezerwacja poza aplikacją).",
    "eventDetail.noDateToast": "To wydarzenie nie ma jeszcze daty.",
    "eventDetail.calendarDesc": "Dodano z aplikacji USLY.",
    "eventDetail.defaultSummary": "Wydarzenie USLY",
    "eventDetail.calendarDownloaded": "Pobrano plik kalendarza.",
    "eventDetail.calendarNativeOpened": "Otworzono kalendarz. Zapisz wydarzenie, aby dodać je do swojego kalendarza.",
    "eventDetail.saveRemoveFailed": "Nie udało się usunąć z obserwowanych",
    "eventDetail.saveRemoved": "Usunięto z obserwowanych",
    "eventDetail.saveAddFailed": "Nie udało się dodać do obserwowanych",
    "eventDetail.saveAdded": "Dodano do obserwowanych",
    "eventDetail.saveToggleFailed": "Nie udało się zmienić obserwowanych wydarzeń",
    "eventDetail.joinRemoveFailed": "Nie udało się wycofać zapisu",
    "eventDetail.joinRemoved": "Wycofano zapis na wydarzenie",
    "eventDetail.joinAddFailed": "Nie udało się zapisać na wydarzenie",
    "eventDetail.joinAdded": "Jesteś zapisany na wydarzenie",
    "eventDetail.joinToggleFailed": "Nie udało się zmienić zapisu na wydarzenie",
    "eventDetail.shareTitle": "Udostępnij",
    "eventDetail.shareHeading": "Udostępnianie",
    "eventDetail.shareSub": "Skopiuj link i prześlij go dalej.",
    "eventDetail.copyLink": "Skopiuj link",
    "eventDetail.copyToast": "Skopiowano link",
    "eventDetail.copyFailed": "Nie udało się skopiować linku",
    "eventReport.modalTitle": "Zgłoś wydarzenie",
    "eventReport.reasonTitle": "Powód zgłoszenia",
    "eventReport.chooseReason": "Wybierz powód",
    "eventReport.reasonSpam": "Spam / scam",
    "eventReport.reasonMisleading": "Fałszywe lub mylące wydarzenie",
    "eventReport.reasonInappropriate": "Nieodpowiednia treść",
    "eventReport.reasonUnsafe": "Podejrzane lub niebezpieczne wydarzenie",
    "eventReport.reasonOther": "Inne",
    "eventReport.descriptionPlaceholder": "Dodatkowe informacje (opcjonalnie)",
    "eventReport.submit": "Wyślij zgłoszenie",
    "eventReport.noEvent": "Brak wydarzenia",
    "eventReport.toastNoReason": "Wybierz powód zgłoszenia",
    "eventReport.toastFailed": "Nie udało się wysłać zgłoszenia",
    "eventReport.toastSent": "Zgłoszenie wysłane • #{{ticket}}",
    "eventReport.toastConnection": "Błąd połączenia",
    "eventMenu.title": "Opcje wydarzenia",
    "eventMenu.report": "Zgłoś",
    "eventMenu.hide": "Ukryj",
    "eventMenu.hideSoon": "Ukrywanie wydarzeń będzie dostępne w kolejnej aktualizacji.",
    "eventDetail.observe": "Obserwuj",
    "eventDetail.observed": "Obserwowane",
    "eventDetail.cancelInterest": "Zrezygnuj z udziału",
    "eventDetail.interested": "Wezmę udział",
    "eventDetail.addCalendar": "Dodaj do kalendarza",
    "eventDetail.share": "Udostępnij",
    "eventDetail.interestedNote": "Jeśli zaznaczysz „Wezmę udział”, organizator zobaczy Cię na liście zainteresowanych.",
    "eventDetail.writeOrganizer": "Napisz do organizatora",
    "groups.searchPlaceholder": "Szukaj grupy (np. #kino)",
    "groups.yourGroups": "Twoje grupy",
    "groups.suggestedGroups": "Proponowane grupy",
    "groups.yourGroupsSub": "Grupy, do których już należysz.",
    "groups.suggestedGroupsSub": "Dopasowane do Twoich zainteresowań i wykluczające grupy, w których już jesteś.",
    "groups.noSuggestedGroups": "Brak proponowanych grup",
    "groups.memberOne": "1 osoba",
    "groups.memberFew": "{{count}} osoby",
    "groups.memberMany": "{{count}} osób",
    "groups.createdByYouHtml": "Założona<br>przez Ciebie",
    "groups.create": "Utwórz grupę",
    "groupThread.placeholder": "Napisz w grupie.",
    "groupPeople.title": "Ludzie w grupie",
    "groupPeople.subtitle": "Zarządzaj zaproszeniami i sprawdź, kto już jest w grupie.",
    "groupPeople.premiumOnly": "Zapraszanie do grup jest dostępne od planu PREMIUM.",
    "groupPeople.inviteTab": "Do zaproszenia",
    "groupPeople.membersTab": "Grupowicze",
    "groupPeople.invitedTab": "Zaproszeni",
    "groupPeople.shared": "Wspólne: {{tags}}",
    "groupPeople.invite": "Zaproś",
    "groupPeople.emptyInvite": "Brak osób do zaproszenia.",
    "groupPeople.memberFallback": "Grupowicz w USLY",
    "groupPeople.founder": "Założyciel",
    "groupPeople.yourProfile": "Twój profil",
    "groupPeople.viewProfile": "Zobacz profil",
    "groupPeople.emptyMembers": "Brak grupowiczów.",
    "groupPeople.invitePending": "Zaproszenie oczekuje",
    "groupPeople.emptyInvited": "Brak oczekujących zaproszeń.",
    "groupPeople.toastPremium": "Dodawanie znajomych do grup jest dostępne od planu PREMIUM",
    "groupPeople.addFriend": "Dodaj znajomego",
    "groupPeople.availablePremium": "Dostępne od PREMIUM",
    "groupPeople.inviteFriendModalTitle": "Dodaj znajomego do grupy",
    "groupPeople.pickFriend": "Wybierz znajomego",
    "groupPeople.pickFriendSub": "Wybierz znajomego, którego chcesz zaprosić do tej grupy.",
    "partnerDash.title": "Panel organizatora",
    "partnerDash.yourPlace": "Twoje miejsce",
    "partnerDash.meta": "Uzupełnij profil organizatora, aby pokazać markę i ofertę w lepszy sposób.",
    "partnerDash.yourPlan": "Twój plan",
    "partnerDash.upgradeHint": "Zwiększ zasięg swoich wydarzeń i odblokuj dodatkowe możliwości z wyższym planem.",
    "partnerDash.metricEvents": "Wydarzenia",
    "partnerDash.metricTotal": "Łącznie",
    "partnerDash.metricViews": "Wyświetlenia profilu",
    "partnerDash.metricClicks": "Kliknięcia",
    "partnerDash.metricConversions": "Konwersje",
    "partnerDash.shortcuts": "Skróty",
    "partnerDash.shortcutsSub": "Najczęściej używane akcje.",
    "partnerDash.addEvent": "Dodaj wydarzenie",
    "partnerDash.myEvents": "Moje wydarzenia",
    "partnerCreate.title": "Nowe wydarzenie",
    "partnerCreate.name": "Nazwa *",
    "partnerCreate.namePlaceholder": "np. Kameralny wieczór muzyczny",
    "partnerCreate.city": "Miasto *",
    "partnerCreate.cityPlaceholder": "np. Warszawa",
    "partnerCreate.when": "Kiedy *",
    "partnerCreate.dateHint": "DD.MM.RRRR",
    "partnerCreate.timeHint": "GG:MM",
    "partnerCreate.where": "Gdzie odbywa się wydarzenie? *",
    "partnerCreate.addressPlaceholder": "np. Studio Aurora albo ul. Słoneczna 12",
    "partnerCreate.findPlace": "Znajdź miejsce na mapie",
    "partnerCreate.interest": "Zainteresowanie / hashtag *",
    "partnerCreate.interestPlaceholder": "np. muzyka",
    "partnerCreate.description": "Opis",
    "partnerCreate.descriptionPlaceholder": "Krótki opis wydarzenia (max 600)",
    "partnerCreate.capacityTitle": "Liczba miejsc",
    "partnerCreate.capacityText": "Możesz zostawić wydarzenie bez limitu albo podać maksymalną liczbę uczestników.",
    "partnerCreate.unlimitedCapacity": "Bez limitu miejsc",
    "partnerCreate.maxCapacity": "Maksymalna liczba miejsc",
    "partnerCreate.ticketsTitle": "Bilety (opcjonalnie)",
    "partnerCreate.ticketsText": "USLY nie sprzedaje biletów — podajesz link do zewnętrznej sprzedaży / rezerwacji.",
    "partnerCreate.ticketType": "Rodzaj",
    "partnerCreate.ticketFree": "Bezpłatne",
    "partnerCreate.ticketFixed": "Płatne — cena stała",
    "partnerCreate.ticketRange": "Płatne — przedział",
    "partnerCreate.price": "Cena (zł)",
    "partnerCreate.priceFrom": "Od (zł)",
    "partnerCreate.priceTo": "Do (zł)",
    "partnerCreate.ticketLink": "Link do biletów / rezerwacji",
    "partnerCreate.saveDraft": "Zapisz szkic",
    "partnerCreate.publish": "Utwórz wydarzenie",
    "partnerCreate.resume": "Wznów wydarzenie",
    "partnerCreate.publishExisting": "Opublikuj",
    "partnerEvent.featured": "Wyróżnione",
    "partnerEvent.signupsShort": "{{count}} zapisów",
    "partnerEvent.observersShort": "{{count}} obserwacji",
    "partnerEvent.capacityShort": "{{used}}/{{capacity}} miejsc",
    "partnerEvent.noCapacityLimit": "Bez limitu miejsc",
    "partnerEvent.freeSpotsShort": "Wolne: {{count}}",
    "partnerEvent.participantsAction": "Uczestnicy",
    "partnerEvent.closeShort": "Zamknij",
    "partnerEvent.archiveShort": "Zarchiwizuj",
    "partnerEvent.emptySection": "Brak wydarzeń w tej sekcji",
    "partnerEvent.loading": "Ładowanie wydarzeń...",
    "partnerEvents.title": "Twoje wydarzenia",
    "partnerParticipants.title": "Uczestnicy wydarzenia",
    "partnerParticipants.notifyAll": "Powiadom wszystkich uczestników",
    "partnerParticipants.notifyText": "Wyślij jedną wiadomość do wszystkich zapisanych osób. Idealne na przypomnienia i ważne informacje.",
    "partnerEvents.saveFailed": "Nie udało się zapisać wydarzenia",
    "tabbar.userAria": "Dolna nawigacja — Towarzysz",
    "tabbar.partnerAria": "Dolna nawigacja — Organizator",
    "tabbar.nearby": "Okolica",
    "tabbar.chats": "Czaty",
    "tabbar.events": "Wydarzenia",
    "tabbar.eventsShort": "Eventy",
    "tabbar.partner.dashboardShort": "Panel",
    "tabbar.partner.messagesShort": "Chat",
    "tabbar.partner.settingsShort": "Ustaw.",
    "tabbar.groups": "Grupy",
    "tabbar.profile": "Profil",
    "tabbar.add": "Dodaj",
    "tabbar.messages": "Wiadomości",
    "tabbar.settings": "Ustawienia",
    "partnerMessages.aria": "Wiadomości organizatora",
    "partnerMessages.title": "Wiadomości",
    "partnerMessages.searchPlaceholder": "Szukaj rozmowy...",
    "partnerMessages.defaultUser": "Użytkownik",
    "partnerMessages.empty": "Brak rozmów",
    "partnerMessages.loading": "Ładowanie rozmów...",
    "partnerMessages.loadFailed": "Nie udało się załadować rozmów",
    "notifications.title": "Powiadomienia",
    "notifications.empty": "Brak powiadomień",
    "notifications.loadMore": "Wczytaj więcej",
    "notifications.defaultUser": "Użytkownik",
    "notifications.defaultNewPerson": "Nowa osoba",
    "notifications.defaultEvent": "Wydarzenie",
    "notifications.defaultGroup": "Grupa",
    "notifications.partner.newObserverTitle": "Nowe obserwowanie wydarzenia",
    "notifications.partner.newSignupTitle": "Nowy zapis na wydarzenie",
    "notifications.partner.newObserverBody": "{{user}} obserwuje: {{event}}",
    "notifications.partner.newSignupBody": "{{user}} zapisał(a) się na: {{event}}",
    "notifications.friendRequestTitle": "Zaproszenie do znajomych",
    "notifications.friendRequestBody": "{{user}} chce dodać Cię do znajomych",
    "notifications.groupInviteTitle": "Zaproszenie do grupy",
    "notifications.groupInviteBody": "{{user}} zaprasza Cię do grupy: {{group}}",
    "notifications.admin.userReportInReview": "Twoje zgłoszenie jest sprawdzane",
    "notifications.admin.userReportResolved": "Twoje zgłoszenie zostało uznane",
    "notifications.admin.userReportRejected": "Twoje zgłoszenie zostało odrzucone",
    "notifications.admin.eventReportInReview": "Zgłoszenie wydarzenia jest sprawdzane",
    "notifications.admin.eventReportResolved": "Zgłoszenie wydarzenia zostało uznane",
    "notifications.admin.eventReportRejected": "Zgłoszenie wydarzenia zostało odrzucone",
    "notifications.admin.warningProfile": "Ostrzeżenie dotyczące profilu",
    "notifications.admin.warningContent": "Ostrzeżenie dotyczące treści",
    "notifications.admin.warningBehavior": "Ostrzeżenie dotyczące zachowania",
    "notifications.admin.bugAccepted": "Przyjęliśmy Twoje zgłoszenie błędu",
    "notifications.admin.bugInProgress": "Pracujemy nad Twoim zgłoszeniem",
    "notifications.admin.bugFixed": "Zgłoszony błąd został poprawiony",
    "notifications.admin.bugResolved": "Twoje zgłoszenie błędu zostało rozwiązane",
    "notifications.admin.bugNotReproducible": "Nie udało się odtworzyć zgłoszonego błędu",
    "notifications.admin.warningBody": "Administracja wysłała ostrzeżenie dotyczące zasad USLY. Sprawdź swój profil i aktywność w aplikacji. W razie pytań możesz skontaktować się z supportem USLY.",
    "notifications.admin.bugBody": "Dziękujemy za zgłoszenie. Aktualizujemy status, żeby było jasne, co dzieje się z Twoją sprawą.",
    "notifications.admin.reportBody": "Administracja zaktualizowała status Twojego zgłoszenia. Dziękujemy za pomoc w dbaniu o bezpieczeństwo społeczności.",
    "notifications.admin.eventReportBody": "Administracja zaktualizowała status Twojego zgłoszenia wydarzenia. Dziękujemy za pomoc w dbaniu o bezpieczeństwo społeczności.",
    "notifications.event.reminder2dTitle": "Wydarzenie już za 2 dni",
    "notifications.event.reminder1dTitle": "Wydarzenie już jutro",
    "notifications.event.timeAndLocationChangedTitle": "Zmiana godziny i miejsca wydarzenia",
    "notifications.event.timeChangedTitle": "Zmiana godziny wydarzenia",
    "notifications.event.locationChangedTitle": "Zmiana miejsca wydarzenia",
    "notifications.event.underReviewTitle": "Sprawdzamy to wydarzenie",
    "notifications.event.safetyNoticeTitle": "Ważna informacja o wydarzeniu",
    "notifications.event.archivedTitle": "Wydarzenie nie jest już dostępne",
    "notifications.event.updatedTitle": "Zmiana w zapisanym wydarzeniu",
    "notifications.event.reminder2dBody": "Przypominamy: {{event}} odbędzie się za 2 dni.{{context}}",
    "notifications.event.reminder1dBody": "Przypominamy: {{event}} odbędzie się jutro.{{context}}",
    "notifications.event.underReviewBody": "Otrzymaliśmy zgłoszenie dotyczące wydarzenia {{event}} i właśnie je weryfikujemy. Do czasu zakończenia sprawy zachowaj ostrożność.{{context}}",
    "notifications.event.safetyNoticeBody": "Mamy ważną informację dotyczącą wydarzenia {{event}}. Sprawdzamy zgłoszenie związane z bezpieczeństwem lub zasadami USLY.{{context}}",
    "notifications.event.archivedBody": "Wydarzenie {{event}} zostało ukryte przez administrację i nie jest już dostępne dla uczestników.{{context}}",
    "notifications.event.updatedBody": "{{event}} zostało zaktualizowane",
    "partnerParticipants.messagePlaceholder": "Napisz wiadomość do uczestników...",
    "partnerParticipants.send": "Wyślij do uczestników",
    "partnerParticipants.savedUsers": "Zapisani uczestnicy",
    "partnerParticipants.savedUsersSub": "Osoby, które kliknęły „wezmę udział” dla tego wydarzenia.",
    "partnerParticipants.empty": "Na razie nikt się nie zapisał.",
    "partnerParticipants.loading": "Ładowanie uczestników...",
    "settings.title": "Ustawienia",
    "settings.profile": "Twój profil",
    "settings.profileSub": "Uzupełnij profil, aby poprawić dopasowania.",
    "settings.ageLabel": "Wiek: {{age}} lat",
    "bugReport.modalTitle": "Zgłoś błąd",
    "bugReport.heading": "Zgłoszenie błędu",
    "bugReport.subtitle": "Opisz krótko problem. To trafia do zespołu (na testach).",
    "bugReport.label": "Co nie działa?",
    "bugReport.placeholder": "Np. Po kliknięciu Zapisz zmiany nic się nie dzieje...",
    "bugReport.submit": "Wyślij",
    "bugReport.toast.empty": "Opisz proszę problem",
    "bugReport.toast.sent": "Dzięki! Zgłoszenie wysłane.",
    "bugReport.toast.failed": "Nie udało się wysłać",
    "bugReport.toast.saved": "Dzięki! Zgłoszenie zapisane",
    "settings.interests": "Zainteresowania",
    "settings.friendsSub": "Lista kontaktów",
    "settings.open": "Otwórz",
    "settings.invitesSub": "Zaproszenia",
    "settings.accountHelp": "Konto i pomoc",
    "settings.reportBug": "Zgłoś błąd",
    "settings.changePassword": "Zmień hasło",
    "password.modalTitle": "Zmień hasło",
    "password.heading": "Zmiana hasła",
    "password.subtitle": "Wpisz obecne hasło i ustaw nowe hasło do konta.",
    "password.current": "Obecne hasło",
    "password.currentPlaceholder": "Wpisz obecne hasło",
    "password.new": "Nowe hasło",
    "password.newPlaceholder": "Wpisz nowe hasło",
    "password.repeat": "Powtórz nowe hasło",
    "password.repeatPlaceholder": "Powtórz nowe hasło",
    "password.save": "Zapisz nowe hasło",
    "password.toastMismatch": "Nowe hasła nie są takie same",
    "password.toastMin": "Nowe hasło musi mieć co najmniej 8 znaków",
    "password.toastCurrentInvalid": "Obecne hasło jest nieprawidłowe",
    "password.toastSame": "Nowe hasło musi być inne niż obecne",
    "delete.modalTitle": "Usuń konto",
    "delete.heading": "Usuń konto",
    "delete.subtitle": "Ta akcja jest nieodwracalna. Wpisz hasło, aby potwierdzić usunięcie konta.",
    "delete.password": "Hasło",
    "delete.placeholder": "Wpisz hasło, aby potwierdzić",
    "delete.confirm": "Usuń konto",
    "delete.toastFill": "Wpisz hasło, aby potwierdzić usunięcie konta",
    "delete.toastInvalid": "Hasło jest nieprawidłowe",
    "delete.toastSuccess": "Konto zostało usunięte",
    "delete.toastFailed": "Nie udało się usunąć konta",
    "settings.toast.saveFailed": "Nie udało się zapisać ustawień",
    "partnerSettings.toastSaveFailed": "Nie udało się zapisać ustawień organizatora",
    "partnerSettings.toastSaved": "Zapisano ustawienia organizatora",
    "partnerLogo.toastUploadFailed": "Nie udało się wgrać logo",
    "partnerLogo.toastSaved": "Logo zapisane",
    "partnerLogo.toastRemoveFailed": "Nie udało się usunąć logo",
    "partnerLogo.toastRemoved": "Logo usunięte",
    "partnerParticipants.defaultUser": "Użytkownik #{{id}}",
    "partnerParticipants.signupLabel": "Zapis: {{when}}",
    "partnerParticipants.write": "Napisz",
    "partnerParticipants.loadFailed": "Nie udało się załadować zapisanych.",
    "partnerParticipants.messageLocked": "Wiadomości do uczestników są dostępne od planu PRO",
    "partnerParticipants.modalTitle": "Napisz do uczestnika",
    "partnerParticipants.conversationWith": "Rozmowa z:",
    "partnerParticipants.defaultParticipant": "Uczestnik",
    "partnerParticipantMessage.placeholder": "Napisz wiadomość...",
    "partnerParticipantMessage.send": "Wyślij",
    "partnerParticipantMessage.blockedLink": "Linki są obecnie blokowane ze względów bezpieczeństwa USLY. Wiadomość nie została dostarczona.",
    "partnerParticipantMessage.blockedContent": "Treść została zablokowana przez moderację USLY i nie została dostarczona.",
    "partnerBroadcast.locked": "Ta funkcja jest dostępna od planu PREMIUM",
    "partnerBroadcast.noParticipants": "Brak zapisanych uczestników",
    "partnerBroadcast.organizerMarker": "— wiadomość od organizatora —",
    "partnerBroadcast.sent": "Wysłano do {{count}} uczestników",
    "partnerBroadcast.failed": "Nie udało się wysłać wiadomości do uczestników",
    "partnerPlace.enterQuery": "Wpisz nazwę miejsca lub adres",
    "partnerPlace.notFound": "Nie znaleziono miejsca. Doprecyzuj adres lub nazwę.",
    "partnerPlace.searchFailed": "Nie udało się wyszukać miejsca.",
    "partnerPlace.defaultPlace": "Miejsce",
    "partnerPlace.selectedLabel": "Wybrano:",
    "partnerPlace.defaultLower": "miejsce",
    "partnerPlace.selectedToast": "Miejsce wydarzenia zostało wybrane",
    "partnerEvent.editorOpened": "Otwarto wydarzenie do edycji",
    "partnerEvent.partnerOnly": "To jest dostępne tylko dla organizatora",
    "partnerEvent.draftRequired": "Aby zapisać szkic, uzupełnij: nazwa, miasto, kiedy, gdzie, hashtag",
    "partnerEvent.invalidDate": "Podaj poprawną datę wydarzenia",
    "partnerEvent.interestLimitReached": "Ten plan pozwala dodać maks. {{limit}} hashtagów do wydarzenia.",
    "partnerEvent.invalidCapacity": "Podaj poprawną liczbę miejsc",
    "partnerEvent.ticketRequired": "Dodaj link do biletów / rezerwacji",
    "partnerEvent.invalidPrice": "Podaj poprawną cenę",
    "partnerEvent.invalidPriceRange": "Podaj poprawny zakres cen",
    "partnerEvent.priceRangeOrder": "Cena od nie może być większa niż cena do",
    "partnerEvent.draftSaveFailed": "Nie udało się zapisać szkicu",
    "partnerEvent.draftSaved": "Zapisano szkic wydarzenia",
    "partnerEvent.createdAsDraft": "Zapisano wydarzenie jako szkic",
    "partnerEvent.publishRequiredExisting": "Uzupełnij: nazwa, miasto, kiedy",
    "partnerEvent.publishRequiredNew": "Uzupełnij: nazwa, miasto, kiedy, gdzie, hashtag",
    "partnerEvent.saveChangesFailed": "Nie udało się zapisać zmian wydarzenia",
    "partnerEvent.updated": "Zaktualizowano wydarzenie",
    "partnerEvent.draftSavedPublishFailed": "Zapisano szkic, ale nie udało się go opublikować",
    "partnerEvent.resumed": "Wznowiono wydarzenie",
    "partnerEvent.published": "Opublikowano wydarzenie",
    "partnerEvent.createFailed": "Nie udało się utworzyć wydarzenia",
    "partnerEvent.createdMissingId": "Utworzono wydarzenie, ale brakuje ID do publikacji",
    "partnerEvent.createdPublishFailed": "Wydarzenie utworzono, ale nie udało się go opublikować",
    "partnerEvent.createdAndPublished": "Utworzono i opublikowano wydarzenie",
    "partnerEvent.publishLimitReached": "Plan {{plan}} pozwala na maksymalnie {{limit}} aktywne wydarzenia. Zapisz kolejne jako szkic albo przejdź na wyższy plan.",
    "partnerSetup.cityRequired": "Podaj miasto działania",
    "partnerSetup.profileSaved": "Profil organizatora zapisany",
    "partnerSetup.profileSaveFailed": "Nie udało się zapisać profilu organizatora",
    "profileSetup.profileSaved": "Profil zapisany",
    "profileSetup.profileSaveFailed": "Nie udało się zapisać profilu",
    "partnerEvent.publishFailed": "Nie udało się opublikować wydarzenia",
    "partnerEvent.quickPublished": "Wydarzenie opublikowane",
    "partnerEvent.archiveFailed": "Nie udało się zarchiwizować wydarzenia",
    "partnerEvent.archived": "Wydarzenie przeniesiono do archiwum",
    "partnerEvent.statusDraft": "Szkic",
    "partnerEvent.sectionActiveTitle": "Aktywne",
    "partnerEvent.sectionActiveDesc": "Wydarzenia, które są teraz widoczne dla użytkowników.",
    "partnerEvent.sectionDraftsTitle": "Szkice",
    "partnerEvent.sectionDraftsDesc": "Robocze wydarzenia przed publikacją.",
    "partnerEvent.sectionFinishedTitle": "Zakończone",
    "partnerEvent.sectionFinishedDesc": "Wydarzenia, których termin już minął.",
    "partnerEvent.sectionArchivedTitle": "Archiwalne",
    "partnerEvent.sectionArchivedDesc": "Zamknięte lub przeniesione do archiwum.",
    "partnerEvent.countOne": "1 wydarzenie",
    "partnerEvent.countFew": "{{count}} wydarzenia",
    "partnerEvent.countMany": "{{count}} wydarzeń",
    "partnerDash.metricActive": "Aktywne",
    "partnerDash.metricActiveSub": "Opublikowane teraz",
    "partnerDash.metricDrafts": "Szkice",
    "partnerDash.metricDraftsSub": "Robocze",
    "partnerDash.metricSignupsTotal": "Zapisy (łącznie)",
    "admin.toastStatusSaved": "Status zgłoszenia zapisany",
    "admin.toastStatusSaveFailed": "Nie udało się zapisać statusu",
    "admin.toastBugNotFound": "Nie znaleziono zgłoszenia błędu",
    "admin.toastBugPreviewFailed": "Nie udało się otworzyć podglądu błędu",
    "app.viewMissing": "Brak widoku: {{view}}",
    "bugReport.ticketSent": "Zgłoszenie wysłane • #{{ticket}}",
    "bugReport.ticketSaved": "Zgłoszenie zapisane • #{{ticket}}",
    "partnerParticipants.sent": "Wiadomość została wysłana",
    "settings.toast.saved": "Zapisano ustawienia",
    "photo.modalTitle": "Dodaj zdjęcie",
    "photo.heading": "Upload zdjęcia",
    "photo.subtitle": "Dodaj zdjęcie profilowe albo zostaw puste pole i używaj placeholdera.",
    "photo.save": "Zapisz zdjęcie",
    "photo.toast.pickFile": "Wybierz plik ze zdjęciem",
    "photo.toast.uploadFailed": "Nie udało się wgrać zdjęcia",
    "photo.toast.saved": "Zdjęcie zapisane",
    "photo.toast.removeFailed": "Nie udało się usunąć zdjęcia",
    "photo.toast.removed": "Zdjęcie usunięte",
    "avatar.modalTitle": "Stwórz awatar AI",
    "avatar.heading": "Awatar AI",
    "avatar.subtitle": "Opisz styl, a USLY wygeneruje ilustracyjny awatar profilowy. Generowanie może chwilę potrwać.",
    "avatar.statusChecking": "Sprawdzam limit...",
    "avatar.styleLabel": "Styl awatara",
    "avatar.placeholder": "np. minimalistyczny, ciepły, elegancki, pastelowy",
    "avatar.generate": "Generuj awatar",
    "avatar.generating": "Generuję...",
    "avatar.limitReached": "Limit wykorzystany",
    "avatar.toastDescribe": "Opisz krótko styl awatara",
    "avatar.toastLimitReached": "Limit awatarów AI w Twoim planie został wykorzystany",
    "avatar.toastFailed": "Nie udało się wygenerować awatara",
    "avatar.toastReady": "Awatar gotowy",
    "avatar.toastReadyRemaining": "Awatar gotowy. Pozostało: {{remaining}}",
    "avatar.statusFailed": "Nie udało się sprawdzić limitu awatarów AI.",
    "avatar.statusLine": "Twój plan: <b>{{plan}}</b> • Awatary AI: <b>{{used}}/{{limit}}</b> w tym miesiącu • Pozostało: <b>{{remaining}}</b>",
    "avatar.statusLimitLine": "Twój plan: <b>{{plan}}</b> • Wykorzystałaś limit <b>{{used}}/{{limit}}</b> awatarów AI w tym miesiącu. Zmień plan, aby wygenerować więcej.",
    "settings.deleteAccount": "Usuń konto",
    "settings.partnerProfileSub": "Uzupełnij profil organizatora.",
    "settings.logoTitle": "Logo miejsca",
    "settings.logoSub": "Dodaj, podmień albo usuń logo organizatora.",
    "settings.removeLogo": "Usuń logo",
    "settings.dashboard": "Panel",
    "settings.placeData": "Dane miejsca",
    "settings.industry": "Branża",
    "settings.orgAboutPlaceholder": "Krótko opisz miejsce, klimat i ofertę.",
    "settings.partnerAccountSub": "Najważniejsze akcje konta Organizatora.",
    "settings.languageTitle": "Język aplikacji",
    "settings.languageSub": "Zmienisz język od razu, bez wylogowywania.",
    "settings.documents": "Dokumenty",
    "settings.documentsSub": "Regulamin i Polityka prywatności.",
    "settings.logout": "Wyloguj",
    "common.back": "Wróć",
    "forgot.modal.title": "Odzyskiwanie hasła",
    "forgot.heading": "Reset hasła",
    "forgot.subtitle": "Podaj adres e-mail przypisany do konta. Wyślemy link do ustawienia nowego hasła.",
    "forgot.email.label": "Email",
    "forgot.email.placeholder": "np. ola@email.com",
    "forgot.submit": "Wyślij link",
    "forgot.toast.email_required": "Podaj adres e-mail",
    "forgot.toast.success": "Jeśli konto istnieje, wyślemy link do ustawienia nowego hasła.",
    "forgot.toast.error": "Nie udało się wysłać linku. Spróbuj ponownie.",
    "reset.title": "Reset hasła",
    "reset.heading": "Ustaw nowe hasło",
    "reset.subtitle": "Potwierdź konto i ustaw nowe hasło do aplikacji.",
    "reset.email": "Email",
    "reset.email_placeholder": "Adres e-mail",
    "reset.new_password": "Nowe hasło",
    "reset.new_password_placeholder": "Wpisz nowe hasło",
    "reset.repeat_password": "Powtórz nowe hasło",
    "reset.repeat_password_placeholder": "Powtórz nowe hasło",
    "reset.submit": "Zapisz nowe hasło",
    "reset.toast.fill_passwords": "Uzupełnij wszystkie pola hasła",
    "reset.toast.passwords_mismatch": "Hasła nie są takie same",
    "reset.toast.password_too_short": "Hasło musi mieć co najmniej 8 znaków",
    "reset.toast.missing_token": "Brak tokenu resetu hasła",
    "reset.toast.success": "Hasło zostało zmienione",
    "reset.toast.change_error": "Nie udało się zmienić hasła",
    "reset.toast.generic_error": "Błąd resetu hasła",
    "reset.toast.missing_link": "Brak linku do resetu hasła",
    "reset.toast.invalid_link": "Link do resetu hasła jest nieprawidłowy",
    "register.title": "Załóż konto",
    "register.subtitle": "Utwórz konto i przejdź do profilu.",
    "register.account.title": "Konto",
    "register.email": "Email *",
    "register.email_placeholder": "np. ola@email.com",
    "register.nick": "Nick / imię (publiczne) *",
    "register.nick_placeholder": "np. Ola / ola_88",
    "register.company": "Oficjalna nazwa miejsca / firmy *",
    "register.company_placeholder": "np. Studio Miejsce",
    "register.password": "Hasło *",
    "register.password_placeholder": "Minimum 8 znaków",
    "register.repeat_password": "Powtórz hasło *",
    "register.repeat_password_placeholder": "Powtórz hasło",
    "register.user.location_title": "Wiek i lokalizacja",
    "register.birthdate": "Data urodzenia *",
    "register.birthdate_hint": "Format: DD.MM.RRRR",
    "register.age_required": "Wymagane 18+.",
    "register.location": "Lokalizacja *",
    "register.location_placeholder": "Pobieramy miasto...",
    "register.location_note": "📍 Twoja okolica, lepsze dopasowania.",
    "register.partner.place_title": "Twoje miejsce",
    "register.partner.city": "Miasto *",
    "register.partner.city_placeholder": "np. Warszawa",
    "register.partner.plan_title": "Plan organizatora",
    "register.partner.plan_subtitle": "Wybierz dostęp dla miejsca.",
    "register.partner.plan.free": "FREE • 0 zł / mies.",
    "register.partner.plan.pro": "PRO • 129 zł / mies.",
    "register.partner.plan.premium": "PREMIUM • 259 zł / mies.",
    "register.partner.plan.enterprise": "ENTERPRISE • indywidualnie",
    "register.user.plan_title": "Plan",
    "register.user.plan_subtitle": "Wybierz startowy dostęp.",
    "register.user.plan.free": "FREE • 0 zł / mies.",
    "register.user.plan.plus": "PLUS • 29 zł / mies.",
    "register.user.plan.premium": "PREMIUM • 49 zł / mies.",
    "register.user.plan.vip": "VIP • 89 zł / mies.",
    "register.plan_details": "Zobacz szczegóły planów",
    "register.accept_terms": "Akceptuję Regulamin*",
    "register.accept_privacy": "Akceptuję Politykę prywatności*",
    "register.submit": "Zarejestruj",
    "register.legal.title": "Zgody",
    "register.accept_terms_prefix": "Akceptuję",
    "register.terms_link": "Regulamin*",
    "register.accept_privacy_prefix": "Akceptuję",
    "register.privacy_link": "Politykę prywatności*",
    "register.toast.consents_required": "Zaznacz wymagane zgody (*)",
    "register.toast.account_required": "Uzupełnij email, hasło i powtórzenie hasła (min. 8 znaków)",
    "register.toast.birthdate_required": "Podaj datę urodzenia.",
    "register.toast.birthdate_invalid": "Nieprawidłowa data urodzenia.",
    "register.toast.age_under_18": "Nie możesz się zarejestrować – wymagane jest ukończone 18 lat.",
    "register.toast.nick_required": "Uzupełnij datę urodzenia i nick",
    "register.toast.location_required": "Włącz lokalizację, aby kontynuować",
    "register.toast.partner_required": "Uzupełnij nazwę i miasto organizatora",
    "register.toast.create_error": "Nie udało się utworzyć konta",
    "register.toast.auto_login_error": "Konto utworzone, ale nie udało się zalogować automatycznie",
    "register.toast.created_logged_in": "Konto utworzone i zalogowano",
    "register.toast.create_error": "Nie udało się utworzyć konta",
    "login.toast.missing": "Podaj email i hasło",
    "login.toast.error": "Błąd logowania",
    "login.toast.roleMismatch": "To konto należy do innej roli. Wybierz właściwy typ konta i spróbuj ponownie.",
    "login.toast.success": "Zalogowano",
    "logout.toast.success": "Wylogowano",
    "social.loginSoon": "Logowanie społecznościowe będzie dostępne wkrótce",
    "social.signupSoon": "Rejestracja społecznościowa będzie dostępna wkrótce",
    "role.user": "Towarzysz",
    "role.partner": "Organizator",
    "auth.registerChoice.title": "Jak chcesz korzystać z USLY?",
    "auth.registerChoice.subtitle": "Wybierz rolę i metodę rejestracji.",
    "auth.loginChoice.title": "Jak chcesz się zalogować?",
    "auth.loginChoice.subtitle": "Wybierz rolę i metodę logowania.",
    "auth.role.userDesc": "Dla osób, które chcą poznawać ludzi, dołączać do wydarzeń i budować lokalną społeczność.",
    "auth.role.partnerDesc": "Dla miejsc, marek i osób, które tworzą wydarzenia, zajęcia lub lokalne inicjatywy.",
    "auth.role.userLoginDesc": "Poznawaj ludzi, odkrywaj wydarzenia i buduj swoją lokalną społeczność.",
    "auth.role.partnerLoginDesc": "Twórz wydarzenia, docieraj do nowych uczestników i rozwijaj swoją społeczność.",
    "auth.method.email": "Adres e-mail",
    "auth.method.google": "Google",
    "auth.method.apple": "Apple",
    "auth.methodLabel.email": "adres e-mail",
    "auth.methodLabel.google": "Google",
    "auth.methodLabel.apple": "Apple",
    "auth.loginMethodTitle": "Logowanie przez {{method}}",
    "auth.registerMethodTitle": "Rejestracja przez {{method}}",
    "register.user.subtitleDynamic": "Stwórz konto Towarzysza i ustaw profil.",
    "register.partner.subtitleDynamic": "Stwórz konto Organizatora i ustaw profil.",
    "plans.toast.saveFailed": "Nie udało się zapisać planu",
    "plans.toast.partnerSaveFailed": "Nie udało się zapisać planu organizatora",
    "plans.toast.selected": "Wybrano plan: {{plan}}",
    "enterprise.toast.contactRequired": "Podaj email lub telefon do kontaktu",
    "enterprise.toast.sending": "Wysyłam...",
    "enterprise.toast.failed": "Nie udało się wysłać zapytania",
    "enterprise.toast.sent": "Zapytanie wysłane. Odezwę się do Ciebie z propozycją.",
    "groups.create.availablePlus": "Dostępne od PLUS",
    "groups.create.limitReached": "Limit wykorzystany",
    "groups.create.button": "Utwórz grupę",
    "groups.create.hintLocked": "Tworzenie własnych grup jest dostępne od planu PLUS.",
    "groups.create.hintUnlimited": "Utworzone grupy: {{count}} • Na planie VIP możesz tworzyć grupy bez limitu.",
    "groups.create.hintReached": "Utworzone grupy: {{count}} / {{limit}} • Wykorzystałaś cały limit dla tego planu.",
    "groups.create.hintLeft": "Utworzone grupy: {{count}} / {{limit}} • Możesz utworzyć jeszcze {{left}}.",
    "groups.create.toastLocked": "Tworzenie grup jest dostępne od planu PLUS",
    "groups.create.modalTitle": "Utwórz grupę",
    "groups.create.title": "Tytuł grupy *",
    "groups.create.titlePlaceholder": "np. Kawosze Warszawa",
    "groups.create.interest": "Hashtag / zainteresowanie *",
    "groups.create.interestPlaceholder": "np. kawa",
    "groups.create.description": "Opis",
    "groups.create.descriptionPlaceholder": "Krótki opis grupy (opcjonalnie)",
    "groups.create.planUnlimited": "Tworzysz grupy bez limitu.",
    "groups.create.planLimited": "Ten plan pozwala tworzyć do {{limit}} własnych grup.",
    "groups.create.submit": "Utwórz",
    "groups.create.cancel": "Anuluj",
    "groups.create.toastTitle": "Podaj nazwę grupy (min. 3 znaki)",
    "groups.create.toastInterest": "Podaj hashtag grupy",
    "groups.create.toastFailed": "Nie udało się utworzyć grupy",
    "groups.create.toastSuccess": "Grupa została utworzona",
    "plans.user.plus.price": "29 zł / miesiąc",
    "plans.user.premium.price": "49 zł / miesiąc",
    "plans.user.vip.price": "89 zł / miesiąc",
    "plans.subtitle": "Zobacz różnice funkcji przed zalogowaniem.",
    "plans.preview": "Podgląd planów",
    "login.no_account": "Nie masz konta? Zarejestruj się",
    "login.forgot_password": "Nie pamiętasz hasła?",
    "welcome.title": "Twoje miasto. Twoi ludzie.",
    "welcome.claim.line1": "Twoje miasto.",
    "welcome.claim.line2": "Twoi ludzie.",
    "welcome.value.line1": "Poznawaj ludzi.",
    "welcome.value.line2": "Twórz wydarzenia.",
    "welcome.value.line3": "Buduj społeczność.",
    "welcome.micro": "Jeden #. Tysiące możliwości.",
    "welcome.tag.sport": "#sport",
    "welcome.tag.coffee": "#kawa",
    "welcome.tag.concert": "#koncert",
    "welcome.tag.boardgames": "#planszówki",
    "welcome.tag.fitness": "#fitness",
    "welcome.tag.startup": "#startup",
    "welcome.subtitle": "Ludzie, rozmowy i wydarzenia oparte na zainteresowaniach — nie na przypadku.",
    "welcome.tagline": "Poznawaj ludzi przez zainteresowania, nie wygląd.",
    "welcome.langAria": "Wybór języka",
    "welcome.choose_account": "Wybierz konto",
    "welcome.user": "Poznaj ludzi",
    "welcome.partner": "Twórz wydarzenia",
    "welcome.start": "Zacznij",
    "welcome.have_account": "Zaloguj się",
    "welcome.promo": "Poznawaj miasto przez ludzi, z którymi naprawdę masz flow.",
    "landing.pill.interests": "Poznawaj po zainteresowaniach",
    "landing.pill.vibe": "Spotykaj ludzi w swoim klimacie",
    "landing.pill.places": "Wychodź do miejsc, które czujesz",
    "welcome.plans_subtitle": "Wybierz tryb, który najlepiej pasuje do Ciebie.",
    "welcome.see_plans": "Zobacz plany",
  },
  en: {
    "login.title": "Log in",
    "login.subtitle": "Log in to access your account.",
    "login.mode": "Mode",
    "login.user": "Companion",
    "login.partner": "Organizer",
    "login.email": "Email / nickname",
    "login.password": "Password",
    "login.submit": "Log in",
    "login.or": "or",
    "login.apple": "Continue with Apple",
    "login.google": "Continue with Google",
    "login.facebook": "Continue with Facebook",
    "login.email_placeholder": "e.g. ola_88 / ola@email.com",
    "login.no_account": "Don’t have an account? Register",
    "login.forgot_password": "Forgot password?",
    "plans.title": "Plans",
    "plans.user.title": "Companion Plans",
    "plans.user.subtitle": "Choose the access level that matches how you want to use USLY.",
    "plans.partner.title": "Organizer Plans",
    "plans.partner.subtitle": "Choose the visibility, reporting and tools level for your venue or brand.",
    "plans.choose": "Choose",
    "plans.continueFree": "Continue with FREE",
    "plans.continuePlus": "Continue with PLUS",
    "plans.continuePremium": "Continue with PREMIUM",
    "plans.continueVip": "Continue with VIP",
    "plans.continuePro": "Continue with PRO",
    "plans.recommendedStart": "✨ Recommended to start",
    "plans.recommendedOrganizer": "⭐ Recommended choice",
    "plans.defaultStart": "✔ Recommended to start",
    "plans.onboarding.topTitle": "Almost ready!",
    "plans.onboarding.title": "Choose a plan",
    "plans.onboarding.userSubtitle": "Choose the plan you want to start using USLY with. You can change it later anytime.",
    "plans.onboarding.partnerSubtitle": "Choose the plan you want to start creating events with. You can change it later anytime.",
    "plans.promo.label": "Promo code",
    "plans.promo.placeholder": "Enter code",
    "plans.promo.apply": "Apply",
    "plans.restore.title": "Already have an active subscription?",
    "plans.restore.subtitle": "Changed phones or reinstalled the app? Refresh your purchase from the App Store or Google Play.",
    "plans.restore.button": "Restore purchase",
    "plans.restore.checking": "Checking active subscriptions...",
    "plans.restore.notFound": "No active purchases were found for this account.",
    "plans.restore.success": "Your subscription has been refreshed.",
    "plans.restore.failed": "Could not restore purchases. Please try again.",
    "plans.promo.applied": "Code applied",
    "plans.promo.invalid": "Could not apply the code.",
    "plans.promo.notActive": "This code is no longer active.",
    "plans.promo.expired": "This code has expired.",
    "plans.promo.limitReached": "This code usage limit has been reached.",
    "plans.promo.wrongRole": "This code is not available for this role.",
    "plans.promo.discount": "{{value}}% off for {{months}} months",
    "plans.contact_us": "Contact us",
    "plans.payment.storeComingSoon": "Store payments are being prepared. This plan will be activated after purchase through the App Store or Google Play.",
    "plans.payment.cancelled": "The purchase was cancelled.",
    "plans.payment.notConfigured": "Store payments are not configured yet.",
    "plans.payment.nativeOnly": "Restoring purchases is available only in the USLY mobile app.",
    "plans.payment.pluginMissing": "The payments module is not available in this app version.",
    "plans.payment.productUnavailable": "This product is not available in the store yet.",
    "plans.payment.transactionMissing": "The store did not return a transaction identifier. Please try again.",
    "plans.payment.verifyNotConfigured": "Payment verification is not configured yet.",
    "plans.payment.networkError": "Could not connect to the store. Please try again.",
    "plans.payment.failed": "Could not complete the payment. Please try again.",
    "plans.payment.success": "Your plan has been activated.",
    "plans.current": "Current plan",
    "plans.user.free.desc": "Basic access to USLY and meeting people in your area.",
    "plans.user.plus.desc": "More freedom to meet people and use groups.",
    "plans.user.premium.desc": "A fuller USLY experience and growing your network of connections.",
    "plans.user.vip.desc": "Maximum possibilities and complete freedom in USLY.",
    "plans.partner.free.desc": "A starter plan for organizers who want to try USLY and launch their first activities without fixed costs.",
    "plans.partner.pro.desc": "For organizers who run events regularly and want to manage participant relationships more efficiently.",
    "plans.partner.premium.desc": "For organizers who want to scale operations, work with full analytics and promote their events more strongly.",
    "plans.partner.enterprise.desc": "For larger partners, networks and brands that require a custom scope of operations, reporting and implementation.",
    "plans.user.free.feature1": "1:1 conversations with friends",
    "plans.user.free.feature2": "Join up to 1 group at a time",
    "plans.user.free.feature3": "No option to create your own groups",
    "plans.user.free.feature4": "Up to 5 interests in your profile",
    "plans.user.free.feature5": "1 AI avatar per month",
    "plans.user.plus.feature1": "Create 1 private group",
    "plans.user.plus.feature2": "Join up to 3 groups",
    "plans.user.plus.feature3": "Up to 10 interests in your profile",
    "plans.user.plus.feature4": "More freedom to use the app daily",
    "plans.user.plus.feature5": "5 AI avatars per month",
    "plans.user.premium.feature1": "Create up to 3 private groups",
    "plans.user.premium.feature2": "Unlimited group joining",
    "plans.user.premium.feature3": "Add friends to groups",
    "plans.user.premium.feature4": "Up to 20 interests in your profile",
    "plans.user.premium.feature5": "15 AI avatars per month",
    "plans.user.premium.feature6": "Host badge in up to 2 interests",
    "plans.user.vip.feature1": "Unlimited group creation",
    "plans.user.vip.feature2": "No limits in groups and contacts",
    "plans.user.vip.feature3": "Add friends to groups",
    "plans.user.vip.feature4": "Unlimited number of interests",
    "plans.user.vip.feature5": "30 AI avatars per month",
    "plans.user.vip.feature6": "Host badge in up to 5 interests",
    "plans.price.free": "0 PLN",
    "plans.partner.free.price": "0 PLN",
    "plans.partner.pro.price": "129 PLN / month",
    "plans.partner.premium.price": "259 PLN / month",
    "plans.partner.enterprise.price": "Custom",
    "plans.partner.free.feature1": "Up to 2 active events at the same time",
    "plans.partner.free.feature2": "Basic dashboard view: active events",
    "plans.partner.free.feature3": "No participant messaging",
    "plans.partner.free.feature4": "No broadcast and no event highlighting",
    "plans.partner.free.feature5": "1 hashtag/category per event",
    "plans.partner.pro.feature1": "Up to 5 active events at the same time",
    "plans.partner.pro.feature2": "Extended dashboard view: active events, drafts and signups combined",
    "plans.partner.pro.feature3": "Ability to message participants",
    "plans.partner.pro.feature4": "No broadcast and no event highlighting",
    "plans.partner.pro.feature5": "Up to 2 hashtags/categories per event",
    "plans.partner.premium.feature1": "Unlimited active events",
    "plans.partner.premium.feature2": "Full dashboard view: active events, drafts, signups and attendance",
    "plans.partner.premium.feature3": "Ability to send broadcasts to participants",
    "plans.partner.premium.feature4": "Event highlighting in the app",
    "plans.partner.premium.feature5": "Up to 5 hashtags/categories per event",
    "plans.partner.enterprise.feature1": "Everything in the PREMIUM plan",
    "plans.partner.enterprise.feature2": "Support for multiple scenarios and custom activities",
    "plans.partner.enterprise.feature3": "The fullest scope of reporting and communication",
    "plans.partner.enterprise.feature4": "Implementation scope agreed individually",
    "plans.partner.enterprise.feature5": "Custom scope of event hashtags/categories",
    "enterprise.modal.title": "Enterprise Plan",
    "enterprise.modal.heading": "Let’s talk about a package for your brand",
    "enterprise.modal.subtitle": "Leave your contact details and select what you need. We will prepare a custom proposal for your venue, events or location network.",
    "enterprise.company.label": "Company / brand name",
    "enterprise.company.placeholder": "e.g. club, restaurant, venue network",
    "enterprise.city.label": "City / operating area",
    "enterprise.city.placeholder": "e.g. Warsaw, several cities, all of Poland",
    "enterprise.contact.label": "Email or phone for contact",
    "enterprise.contact.placeholder": "e.g. contact@company.com or phone number",
    "enterprise.interests.label": "What are you interested in?",
    "enterprise.message.label": "Short message",
    "enterprise.message.placeholder": "Briefly describe what you need or what result you want to achieve.",
    "enterprise.submit": "Send inquiry",
    "enterprise.need.visibility": "Greater event visibility",
    "enterprise.need.locations": "Promotion for multiple locations",
    "enterprise.need.campaign": "Campaign or special event",
    "enterprise.need.long_term": "Long-term cooperation",
    "enterprise.need.network": "Offer for a network or franchise",
    "enterprise.need.other": "Other",
    "common.email": "Email",
    "common.remove": "Remove",
    "common.block": "Block",
    "profileEdit.title": "Edit profile",
    "profileEdit.photoTitle": "Profile photo",
    "profileEdit.photoSubtitle": "Add your photo or generate an AI avatar.",
    "profileEdit.photoBtn": "Photo",
    "profileEdit.aiAvatarBtn": "AI Avatar",
    "profileEdit.nick": "Nickname",
    "profileEdit.nick_placeholder": "e.g. Ola_88",
    "profileEdit.bio": "BIO",
    "profileEdit.bio_placeholder": "Short, light, with personality",
    "profileEdit.location": "Current location",
    "profileEdit.radius": "Nearby range",
    "profileEdit.radius5": "Up to 5 km",
    "profileEdit.radius10": "Up to 10 km",
    "profileEdit.radius25": "Up to 25 km",
    "profileEdit.radius50": "Up to 50 km",
    "profileEdit.radius100": "Up to 100 km",
    "profileEdit.ageRangeTitle": "Preferred age range",
    "profileEdit.ageRangeText": "Set the preferred age range of people you want to see.",
    "profileEdit.ageFrom": "From",
    "profileEdit.ageTo": "To",
    "profileEdit.ageAny": "Age does not matter",
    "profileEdit.save": "Save changes",
    "profileInterests.title": "Interests",
    "profileInterests.subtitle": "One shared tag base for your profile, groups and events.",
    "profileInterests.tags": "Your tags",
    "profileInterests.placeholder": "e.g. coffee, yoga, concerts...",
    "profileInterests.limitPlaceholder": "Limit reached • Unlock more in PLUS",
    "profileInterests.limitToast": "Unlock more interests in the PLUS plan",
    "profileInterests.trainerTitle": "Do you run classes or workshops?",
    "profileInterests.trainerSubtitle": "Highlight the interests where you run classes, workshops or help others build skills.",
    "profileInterests.trainerPremiumLimit": "Premium: up to 2 host badges",
    "profileInterests.trainerVipLimit": "VIP: up to 5 host badges",
    "profileInterests.trainerLocked": "Available in Premium and VIP plans",
    "profileInterests.trainerBadge": "Host",
    "profileInterests.leadsClassesTitle": "Runs classes in:",
    "profileInterests.leadsNearbyLabel": "Runs classes",
    "profileInterests.trainerLimitToast": "Host badge limit reached for your plan",
    "profileFriends.title": "Friends",
    "profileFriends.search_placeholder": "Search for a friend...",
    "profileInvites.title": "Invitations",
    "profileInvites.subtitle": "Incoming and sent invitations in a clear layout.",
    "friends.selfAccount": "This is your account",
    "friends.friend": "Friend",
    "friends.pending": "Invitation sent",
    "friends.add": "Add friend",
    "friends.message": "Message",
    "friends.messagesPro": "Messages from PRO plan",
    "friends.toastNoProfile": "No profile selected",
    "friends.toastLogin": "Log in first",
    "friends.toastSendFailed": "Could not send invitation",
    "friends.toastSent": "Friend invitation sent",
    "friends.toastChatAfterAccept": "Private chat will be available after the friend request is accepted",
    "friends.toastAddFirst": "Add this person as a friend first",
    "friends.toastProfileUnavailable": "This profile is not available right now",
    "friends.emptyInvites": "No pending invitations.",
    "friends.defaultUser": "User #{{id}}",
    "friends.pendingDecision": "Invitation is waiting for a decision.",
    "friends.pendingAccept": "Invitation sent — waiting for acceptance.",
    "friends.accept": "Accept",
    "friends.reject": "Reject",
    "friends.sentPill": "Sent",
    "friends.defaultGroup": "Group",
    "friends.groupInviteLine": "{{user}} invited you to a group",
    "friends.emptyFriends": "You do not have friends yet.",
    "friends.friendFallback": "USLY friend",
    "friends.viewProfile": "View profile",
    "friends.groupInviteMissing": "Missing group invitation data",
    "friends.groupInviteUpdateFailed": "Could not update group invitation",
    "friends.groupInviteAccepted": "Group invitation accepted",
    "friends.groupInviteRejected": "Group invitation rejected",
    "friends.groupInviteConnectionFailed": "Connection error while updating group invitation",
    "friends.inviteUpdateFailed": "Could not update invitation",
    "friends.inviteAccepted": "Invitation accepted",
    "friends.inviteRejected": "Invitation rejected",
    "friends.inviteConnectionFailed": "Connection error while updating invitation",
    "profileSetup.topbar": "Profile",
    "profileSetup.title": "Complete your profile",
    "profileSetup.subtitle": "This is the final step after registration. Check your starting data and add missing information for better matches.",
    "profileSetup.startProfile": "Your starter profile",
    "profileSetup.addPhoto": "Add photo",
    "profileSetup.createAvatar": "Create avatar",
    "profileSetup.removePhoto": "Remove photo",
    "profileSetup.nickPlaceholder": "Your nickname",
    "profileSetup.interestsPlaceholder": "e.g. coffee, concerts...",
    "profileSetup.addInterest": "Add",
    "profileSetup.bioLabel": "BIO (max 250)",
    "profileSetup.ageRangeText": "Set the age range of people suggested by the app. You can change it later in settings.",
    "profileSetup.finish": "Save and continue",
    "partnerSetup.topbar": "Profile",
    "partnerSetup.title": "Complete your profile",
    "partnerSetup.subtitle": "Logo, city and venue character.",
    "partnerSetup.identityTitle": "Venue identity",
    "partnerSetup.addLogo": "Add logo",
    "partnerSetup.city": "Operating city",
    "partnerSetup.cityPlaceholder": "e.g. Warsaw",
    "partnerSetup.vibeTitle": "Venue vibe",
    "partnerSetup.vibeSubtitle": "Show users what they can expect.",
    "partnerSetup.category": "Category",
    "partnerCategory.gastro": "Gastro / restaurant / café",
    "partnerCategory.bar_nocne": "Bar / club / nightlife",
    "partnerCategory.kultura": "Culture / concerts / art",
    "partnerCategory.fitness": "Fitness / sport / wellness",
    "partnerCategory.beauty": "Beauty",
    "partnerCategory.hotel_event": "Hotel / event / conference",
    "partnerCategory.rozrywka": "Entertainment / attractions / gaming",
    "partnerCategory.zakupy": "Shop / showroom / retail",
    "partnerCategory.edukacja": "Education / workshops",
    "partnerCategory.cowork": "Cowork / business / networking",
    "partnerCategory.plener": "Outdoor / tourism / recreation",
    "partnerCategory.inne": "Other / not sure",
    "partnerSetup.about": "Short description",
    "partnerSetup.aboutPlaceholder": "What should people know about this place?",
    "nearby.title": "Nearby",
    "nearby.mapSub": "Tap a marker to preview a person or event.",
    "nearby.peopleTitle": "People nearby",
    "nearby.peopleSub": "A list based on your location.",
    "nearby.peoplePlaceholder": "e.g. Alex / Maja",
    "nearby.eventsTitle": "Events nearby",
    "nearby.eventsSub": "Tap a card to open details.",
    "nearby.emptyPeople": "We do not see any people with shared interests in your area yet.",
    "nearby.emptyEvents": "We do not see any events matching your interests in your area yet.",
    "nearby.distanceUnder1": "< 1 km from you",
    "nearby.distanceKm": "{{km}} km from you",
    "nearby.inArea": "Nearby",
    "personProfile.bioTitle": "About me",
    "personProfile.partnerCategory": "Category",
    "personProfile.organizer": "Organizer",
    "personProfile.organizerAboutTitle": "About organizer",
    "personProfile.emptyOrganizerBio": "This organizer has not added a description yet.",
    "personProfile.defaultEvent": "Event",
    "personProfile.eventSoon": "Date coming soon",
    "personProfile.noPartnerEvents": "This organizer has no visible events yet.",
    "personProfile.userProfileFallback": "User profile",
    "personProfile.ageYears": "{{age}} years",
    "personProfile.match": "{{score}}% match",
    "personProfile.message": "Message",
    "personProfile.messagesPro": "Messages from PRO plan",
    "personProfile.options": "Options",
    "personProfile.report": "Report",
    "personProfile.block": "Block",
    "personProfile.toastMissingUser": "Missing user data",
    "personProfile.toastBlockFailed": "Could not block user",
    "personProfile.toastBlocked": "User blocked",
    "personProfile.toastConnectionError": "Connection error",
    "userReport.modalTitle": "Report user",
    "userReport.reasonTitle": "Report reason",
    "userReport.subtitle": "The report will go to USLY moderation.",
    "userReport.reasonLabel": "Choose reason",
    "userReport.reasonSpam": "Spam / scam",
    "userReport.reasonHarassment": "Harassment or offensive content",
    "userReport.reasonProfile": "Inappropriate profile or bio",
    "userReport.reasonImpersonation": "Impersonation",
    "userReport.reasonOther": "Other",
    "userReport.descriptionLabel": "Optional description",
    "userReport.descriptionPlaceholder": "Add details that will help moderation.",
    "userReport.submit": "Send report",
    "userReport.toastNoUser": "No user selected",
    "userReport.toastNoReason": "Choose report reason",
    "userReport.toastFailed": "Could not send report",
    "userReport.toastSent": "Report sent • #{{ticket}}",
    "personProfile.emptyBio": "This person has not added a bio yet.",
    "personProfile.organizerEvents": "Organizer events",
    "personProfile.write": "Message",
    "personProfile.addFriend": "Add friend",
    "chats.title": "Chats",
    "chats.searchTitle": "Search chats",
    "chats.searchSub": "By conversation name",
    "chats.searchPlaceholder": "e.g. Alex",
    "chatThread.placeholder": "Write a message.",
    "chatThread.newMessages": "New messages",
    "chat.menu.title": "Chat menu",
    "chat.menu.notificationsOn": "Turn on notifications",
    "chat.menu.notificationsOff": "Mute conversation",
    "chat.toast.notificationsOn": "Conversation notifications turned on",
    "chat.toast.notificationsMuted": "Conversation muted",
    "chat.toast.sendFailed": "Could not send message",
    "chat.blocked.link": "Links are currently blocked for USLY safety. The message was not delivered.",
    "chat.blocked.content": "The content was blocked by USLY moderation and was not delivered.",
    "chat.avatarMine": "Your avatar",
    "chat.openProfile": "Open profile",
    "chat.defaultUser": "User",
    "chat.organizerMessage": "Message from organizer",
    "chat.organizerMessageMarker": "— message from organizer —",
    "chat.defaultEventTitle": "📣 Event",
    "chat.checkingContent": "Checking message content…",
    "groups.menu.title": "Group menu",
    "groups.menu.notificationsOn": "Turn on notifications",
    "groups.menu.notificationsOff": "Mute group",
    "groups.menu.people": "People in group",
    "groups.menu.close": "Close group",
    "groups.menu.leave": "Leave group",
    "groups.toast.notificationsOn": "Group notifications turned on",
    "groups.toast.notificationsMuted": "Group muted",
    "groups.toast.joined": "Joined the group",
    "groups.toast.joinFailed": "Could not join the group",
    "groups.toast.joinConnectionFailed": "Group join error",
    "groups.toast.closed": "Group closed",
    "groups.toast.closeFailed": "Could not close the group",
    "groups.toast.closeConnectionFailed": "Group closing error",
    "groups.toast.left": "Left the group",
    "groups.toast.leaveFailed": "Could not leave the group",
    "groups.toast.leaveConnectionFailed": "Group leaving error",
    "groups.toast.inviteMissing": "Missing invitation data",
    "groups.toast.inviteSent": "Group invitation sent",
    "groups.toast.inviteFailed": "Could not send group invitation",
    "groupThread.placeholder": "Write in group.",
    "groupThread.sendAria": "Send message to group",
    "groupThread.join": "Join group",
    "groupThread.defaultDesc": "A group based on shared interests.",
    "groupThread.joinToRead": "Join the group to see the conversation and write a message.",
    "groupThread.loading": "Loading messages...",
    "groupThread.empty": "There are no messages in this group yet. Be the first to write.",
    "groupThread.newMessages": "New messages",
    "groupThread.me": "You",
    "groupThread.loadFailed": "Could not load group messages.",
    "groupThread.joinToWrite": "Join the group to write messages",
    "groupThread.limitReached": "Group limit for your plan has been reached",
    "events.title": "Events",
    "events.forYou": "For you",
    "events.myEvents": "My events",
    "events.searchPlaceholder": "Search by name / # (e.g. music)",
    "events.emptyForYou": "There are no new events matching your interests yet.",
    "events.emptyFollowed": "You do not have any saved or followed events yet.",
    "eventDetail.kicker": "Event",
    "eventDetail.description": "Event description",
    "eventDetail.emptyDescription": "The organizer has not added an event description yet.",
    "eventDetail.place": "Place",
    "eventDetail.mapPlaceholder": "The exact address will appear here.",
    "eventDetail.locationSaved": "Event location saved on the map",
    "eventDetail.locationMissing": "Exact location has not been selected yet",
    "eventCapacity.signed": "{{count}} signed up",
    "eventCapacity.used": "{{taken}} of {{capacity}} spots taken",
    "eventCapacity.full": "Fully booked",
    "eventCapacity.lastOne": "Last spot left",
    "eventCapacity.lastFew": "Last {{count}} spots left",
    "eventDetail.ticketFree": "Free",
    "eventDetail.ticketFixed": "Paid — fixed price",
    "eventDetail.ticketRange": "Paid — range",
    "eventDetail.ticketPaid": "Paid",
    "eventDetail.organizer": "Organizer",
    "eventDetail.tickets": "Tickets",
    "eventDetail.ticketLink": "Go to purchase / reservation",
    "eventDetail.ticketLegal": "USLY does not sell tickets and is not the organizer of this event. The link takes you to an external page where the organizer handles sales or reservations.",
    "eventDetail.observe": "Follow",
    "eventDetail.interested": "I’m going",
    "eventDetail.addCalendar": "Add to calendar",
    "eventDetail.noDateToast": "This event does not have a date yet.",
    "eventDetail.calendarDesc": "Added from the USLY app.",
    "eventDetail.defaultSummary": "USLY event",
    "eventDetail.calendarDownloaded": "Calendar file downloaded.",
    "eventDetail.calendarNativeOpened": "Calendar opened. Save the event to add it to your calendar.",
    "eventDetail.share": "Share",
    "eventDetail.shareTitle": "Share",
    "eventDetail.shareHeading": "Share event",
    "eventDetail.shareSub": "Copy the link and share it.",
    "eventDetail.copyLink": "Copy link",
    "eventDetail.copyToast": "Link copied",
    "eventDetail.copyFailed": "Could not copy link",
    "eventDetail.interestedNote": "If you select “I’m going”, the organizer will see you on the interested list.",
    "eventDetail.writeOrganizer": "Message the organizer",
    "groups.searchPlaceholder": "Search groups (e.g. #cinema)",
    "groups.yourGroups": "Your groups",
    "groups.suggestedGroups": "Suggested groups",
    "groups.yourGroupsSub": "Groups you already belong to.",
    "groups.suggestedGroupsSub": "Matched to your interests and excluding groups you already joined.",
    "groups.noSuggestedGroups": "No suggested groups",
    "groups.memberOne": "1 person",
    "groups.memberFew": "{{count}} people",
    "groups.memberMany": "{{count}} people",
    "groups.createdByYouHtml": "Created<br>by you",
    "groups.create": "Create group",
    "groupThread.placeholder": "Write in the group.",
    "groupPeople.title": "People in group",
    "groupPeople.subtitle": "Manage invitations and see who is already in the group.",
    "groupPeople.premiumOnly": "Upgrade to PREMIUM to invite friends to groups.",
    "groupPeople.inviteTab": "To invite",
    "groupPeople.membersTab": "Members",
    "groupPeople.invitedTab": "Invited",
    "groupPeople.shared": "Shared: {{tags}}",
    "groupPeople.invite": "Invite",
    "groupPeople.emptyInvite": "No people to invite.",
    "groupPeople.memberFallback": "USLY group member",
    "groupPeople.founder": "Founder",
    "groupPeople.yourProfile": "Your profile",
    "groupPeople.viewProfile": "View profile",
    "groupPeople.emptyMembers": "No group members.",
    "groupPeople.invitePending": "Invitation pending",
    "groupPeople.emptyInvited": "No pending invitations.",
    "groupPeople.toastPremium": "Adding friends to groups is available from the PREMIUM plan",
    "groupPeople.addFriend": "Add friend",
    "groupPeople.availablePremium": "Available from PREMIUM",
    "groupPeople.inviteFriendModalTitle": "Add friend to group",
    "groupPeople.pickFriend": "Choose a friend",
    "groupPeople.pickFriendSub": "Choose the friend you want to invite to this group.",
    "partnerDash.title": "Organizer dashboard",
    "partnerDash.yourPlace": "Your place",
    "partnerDash.meta": "Complete your organizer profile to present your brand and offer in a better way.",
    "partnerDash.yourPlan": "Your plan",
    "partnerDash.upgradeHint": "Increase your event reach and unlock additional options with a higher plan.",
    "partnerDash.metricEvents": "Events",
    "partnerDash.metricTotal": "Total",
    "partnerDash.metricViews": "Profile views",
    "partnerDash.metricClicks": "Clicks",
    "partnerDash.metricConversions": "Conversions",
    "partnerDash.shortcuts": "Shortcuts",
    "partnerDash.shortcutsSub": "Most-used actions.",
    "partnerDash.addEvent": "Add event",
    "partnerDash.myEvents": "My events",
    "partnerCreate.title": "New event",
    "partnerCreate.name": "Name *",
    "partnerCreate.namePlaceholder": "e.g. Live concert",
    "partnerCreate.city": "City *",
    "partnerCreate.cityPlaceholder": "e.g. Warsaw",
    "partnerCreate.when": "When *",
    "partnerCreate.dateHint": "DD.MM.YYYY",
    "partnerCreate.timeHint": "HH:MM",
    "partnerCreate.where": "Where does the event take place? *",
    "partnerCreate.addressPlaceholder": "e.g. Aurora Studio or 12 Sunny Street",
    "partnerCreate.findPlace": "Find place on map",
    "partnerCreate.interest": "Interest / hashtag *",
    "partnerCreate.interestPlaceholder": "e.g. music",
    "partnerCreate.description": "Description",
    "partnerCreate.descriptionPlaceholder": "Short event description (max 600)",
    "partnerCreate.capacityTitle": "Number of spots",
    "partnerCreate.capacityText": "You can leave the event unlimited or provide the maximum number of participants.",
    "partnerCreate.unlimitedCapacity": "Unlimited spots",
    "partnerCreate.maxCapacity": "Maximum number of spots",
    "partnerCreate.ticketsTitle": "Tickets (optional)",
    "partnerCreate.ticketsText": "USLY does not sell tickets — you provide a link to external sales / reservation.",
    "partnerCreate.ticketType": "Type",
    "partnerCreate.ticketFree": "Free",
    "partnerCreate.ticketFixed": "Paid — fixed price",
    "partnerCreate.ticketRange": "Paid — range",
    "partnerCreate.price": "Price (PLN)",
    "partnerCreate.priceFrom": "From (PLN)",
    "partnerCreate.priceTo": "To (PLN)",
    "partnerCreate.ticketLink": "Ticket / reservation link",
    "partnerCreate.saveDraft": "Save draft",
    "partnerCreate.publish": "Create event",
    "partnerCreate.resume": "Resume event",
    "partnerCreate.publishExisting": "Publish",
    "partnerEvent.featured": "Featured",
    "partnerEvent.signupsShort": "{{count}} signups",
    "partnerEvent.observersShort": "{{count}} observers",
    "partnerEvent.capacityShort": "{{used}}/{{capacity}} spots",
    "partnerEvent.noCapacityLimit": "Unlimited spots",
    "partnerEvent.freeSpotsShort": "Free: {{count}}",
    "partnerEvent.participantsAction": "Participants",
    "partnerEvent.closeShort": "Close",
    "partnerEvent.archiveShort": "Archive",
    "partnerEvent.emptySection": "No events in this section",
    "partnerEvent.loading": "Loading events...",
    "partnerEvents.title": "Your events",
    "partnerParticipants.title": "Event participants",
    "partnerParticipants.notifyAll": "Notify all participants",
    "partnerParticipants.notifyText": "Send one message to all signed-up people. Ideal for reminders and important updates.",
    "partnerEvents.saveFailed": "Could not save the event",
    "tabbar.userAria": "Bottom navigation — Companion",
    "tabbar.partnerAria": "Bottom navigation — Organizer",
    "tabbar.nearby": "Nearby",
    "tabbar.chats": "Chats",
    "tabbar.events": "Events",
    "tabbar.eventsShort": "Events",
    "tabbar.partner.dashboardShort": "Panel",
    "tabbar.partner.messagesShort": "Chat",
    "tabbar.partner.settingsShort": "Settings",
    "tabbar.groups": "Groups",
    "tabbar.profile": "Profile",
    "tabbar.add": "Add",
    "tabbar.messages": "Messages",
    "tabbar.settings": "Settings",
    "partnerMessages.aria": "Organizer messages",
    "partnerMessages.title": "Messages",
    "partnerMessages.searchPlaceholder": "Search conversation...",
    "partnerMessages.defaultUser": "User",
    "partnerMessages.empty": "No conversations",
    "partnerMessages.loading": "Loading conversations...",
    "partnerMessages.loadFailed": "Could not load conversations",
    "notifications.title": "Notifications",
    "notifications.empty": "No notifications yet",
    "notifications.loadMore": "Load more",
    "notifications.defaultUser": "User",
    "notifications.defaultNewPerson": "New person",
    "notifications.defaultEvent": "Event",
    "notifications.defaultGroup": "Group",
    "notifications.partner.newObserverTitle": "New event follow",
    "notifications.partner.newSignupTitle": "New event signup",
    "notifications.partner.newObserverBody": "{{user}} is following: {{event}}",
    "notifications.partner.newSignupBody": "{{user}} signed up for: {{event}}",
    "notifications.friendRequestTitle": "Friend request",
    "notifications.friendRequestBody": "{{user}} wants to add you as a friend",
    "notifications.groupInviteTitle": "Group invitation",
    "notifications.groupInviteBody": "{{user}} invited you to the group: {{group}}",
    "notifications.admin.userReportInReview": "Your report is being reviewed",
    "notifications.admin.userReportResolved": "Your report has been accepted",
    "notifications.admin.userReportRejected": "Your report has been rejected",
    "notifications.admin.eventReportInReview": "Your event report is being reviewed",
    "notifications.admin.eventReportResolved": "Your event report has been accepted",
    "notifications.admin.eventReportRejected": "Your event report has been rejected",
    "notifications.admin.warningProfile": "Profile warning",
    "notifications.admin.warningContent": "Content warning",
    "notifications.admin.warningBehavior": "Behavior warning",
    "notifications.admin.bugAccepted": "We accepted your bug report",
    "notifications.admin.bugInProgress": "We are working on your report",
    "notifications.admin.bugFixed": "The reported issue has been fixed",
    "notifications.admin.bugResolved": "Your bug report has been resolved",
    "notifications.admin.bugNotReproducible": "We could not reproduce the reported issue",
    "notifications.admin.warningBody": "Administration sent a warning about USLY rules. Check your profile and activity in the app. If you have questions, you can contact USLY support.",
    "notifications.admin.bugBody": "Thank you for your report. We are updating the status so it is clear what is happening with your case.",
    "notifications.admin.reportBody": "Administration updated the status of your report. Thank you for helping keep the community safe.",
    "notifications.admin.eventReportBody": "Administration updated the status of your event report. Thank you for helping keep the community safe.",
    "notifications.event.reminder2dTitle": "Event in 2 days",
    "notifications.event.reminder1dTitle": "Event tomorrow",
    "notifications.event.timeAndLocationChangedTitle": "Event time and location changed",
    "notifications.event.timeChangedTitle": "Event time changed",
    "notifications.event.locationChangedTitle": "Event location changed",
    "notifications.event.underReviewTitle": "We’re reviewing this event",
    "notifications.event.safetyNoticeTitle": "Important event update",
    "notifications.event.archivedTitle": "This event is no longer available",
    "notifications.event.updatedTitle": "Saved event update",
    "notifications.event.reminder2dBody": "Reminder: {{event}} takes place in 2 days.{{context}}",
    "notifications.event.reminder1dBody": "Reminder: {{event}} takes place tomorrow.{{context}}",
    "notifications.event.underReviewBody": "We received a report about {{event}} and are reviewing it now. Please stay cautious until the review is complete.{{context}}",
    "notifications.event.safetyNoticeBody": "We have an important update about {{event}}. We are reviewing a report related to safety or USLY rules.{{context}}",
    "notifications.event.archivedBody": "{{event}} has been hidden by administration and is no longer available to participants.{{context}}",
    "notifications.event.updatedBody": "{{event}} has been updated",
    "partnerParticipants.messagePlaceholder": "Write a message to participants...",
    "partnerParticipants.send": "Send to participants",
    "partnerParticipants.savedUsers": "Signed-up participants",
    "partnerParticipants.savedUsersSub": "People who selected “I’m going” for this event.",
    "partnerParticipants.empty": "No one has signed up yet.",
    "partnerParticipants.loading": "Loading participants...",
    "settings.title": "Settings",
    "settings.profile": "Your profile",
    "settings.profileSub": "Complete your profile to improve matches.",
    "settings.ageLabel": "Age: {{age}} years",
    "bugReport.modalTitle": "Report a bug",
    "bugReport.heading": "Bug report",
    "bugReport.subtitle": "Briefly describe the problem. It goes to the team during testing.",
    "bugReport.label": "What is not working?",
    "bugReport.placeholder": "E.g. after tapping Save changes, nothing happens...",
    "bugReport.submit": "Send",
    "bugReport.toast.empty": "Please describe the problem",
    "bugReport.toast.sent": "Thanks! Report sent.",
    "bugReport.toast.failed": "Could not send",
    "bugReport.toast.saved": "Thanks! Report saved",
    "settings.interests": "Interests",
    "settings.friendsSub": "Contact list",
    "settings.open": "Open",
    "settings.invitesSub": "Invitations",
    "settings.accountHelp": "Account and help",
    "settings.reportBug": "Report a bug",
    "settings.changePassword": "Change password",
    "password.modalTitle": "Change password",
    "password.heading": "Password change",
    "password.subtitle": "Enter your current password and set a new password for your account.",
    "password.current": "Current password",
    "password.currentPlaceholder": "Enter current password",
    "password.new": "New password",
    "password.newPlaceholder": "Enter new password",
    "password.repeat": "Repeat new password",
    "password.repeatPlaceholder": "Repeat new password",
    "password.save": "Save new password",
    "password.toastMismatch": "New passwords do not match",
    "password.toastMin": "New password must contain at least 8 characters",
    "password.toastCurrentInvalid": "Current password is incorrect",
    "password.toastSame": "New password must be different from current password",
    "delete.modalTitle": "Delete account",
    "delete.heading": "Delete account",
    "delete.subtitle": "This action cannot be undone. Enter your password to confirm account deletion.",
    "delete.password": "Password",
    "delete.placeholder": "Enter password to confirm",
    "delete.confirm": "Delete account",
    "delete.toastFill": "Enter password to confirm account deletion",
    "delete.toastInvalid": "Password is incorrect",
    "delete.toastSuccess": "Account deleted",
    "delete.toastFailed": "Could not delete account",
    "settings.toast.saveFailed": "Could not save settings",
    "partnerSettings.toastSaveFailed": "Could not save organizer settings",
    "partnerSettings.toastSaved": "Organizer settings saved",
    "partnerLogo.toastUploadFailed": "Could not upload logo",
    "partnerLogo.toastSaved": "Logo saved",
    "partnerLogo.toastRemoveFailed": "Could not remove logo",
    "partnerLogo.toastRemoved": "Logo removed",
    "partnerParticipants.defaultUser": "User #{{id}}",
    "partnerParticipants.signupLabel": "Signup: {{when}}",
    "partnerParticipants.write": "Message",
    "partnerParticipants.loadFailed": "Could not load signups.",
    "partnerParticipants.messageLocked": "Participant messages are available from the PRO plan",
    "partnerParticipants.modalTitle": "Message participant",
    "partnerParticipants.conversationWith": "Conversation with:",
    "partnerParticipants.defaultParticipant": "Participant",
    "partnerParticipantMessage.placeholder": "Write a message...",
    "partnerParticipantMessage.send": "Send",
    "partnerParticipantMessage.blockedLink": "Links are currently blocked for USLY safety reasons. The message was not delivered.",
    "partnerParticipantMessage.blockedContent": "The content was blocked by USLY moderation and was not delivered.",
    "partnerBroadcast.locked": "This feature is available from the PREMIUM plan",
    "partnerBroadcast.noParticipants": "No signed-up participants",
    "partnerBroadcast.organizerMarker": "— message from organizer —",
    "partnerBroadcast.sent": "Sent to {{count}} participants",
    "partnerBroadcast.failed": "Could not send message to participants",
    "partnerPlace.enterQuery": "Enter a place name or address",
    "partnerPlace.notFound": "Place not found. Refine the address or name.",
    "partnerPlace.searchFailed": "Could not search for the place.",
    "partnerPlace.defaultPlace": "Place",
    "partnerPlace.selectedLabel": "Selected:",
    "partnerPlace.defaultLower": "place",
    "partnerPlace.selectedToast": "Event place selected",
    "partnerEvent.editorOpened": "Event opened for editing",
    "partnerEvent.partnerOnly": "This is available only for organizers",
    "partnerEvent.draftRequired": "To save a draft, fill in: name, city, date, place and hashtag",
    "partnerEvent.invalidDate": "Enter a valid event date",
    "partnerEvent.interestLimitReached": "This plan allows up to {{limit}} event hashtags.",
    "partnerEvent.invalidCapacity": "Enter a valid number of spots",
    "partnerEvent.ticketRequired": "Add a ticket / reservation link",
    "partnerEvent.invalidPrice": "Enter a valid price",
    "partnerEvent.invalidPriceRange": "Enter a valid price range",
    "partnerEvent.priceRangeOrder": "Price from cannot be higher than price to",
    "partnerEvent.draftSaveFailed": "Could not save draft",
    "partnerEvent.draftSaved": "Event draft saved",
    "partnerEvent.createdAsDraft": "Event saved as draft",
    "partnerEvent.publishRequiredExisting": "Fill in: name, city and date",
    "partnerEvent.publishRequiredNew": "Fill in: name, city, date, place and hashtag",
    "partnerEvent.saveChangesFailed": "Could not save event changes",
    "partnerEvent.updated": "Event updated",
    "partnerEvent.draftSavedPublishFailed": "Draft saved, but it could not be published",
    "partnerEvent.resumed": "Event resumed",
    "partnerEvent.published": "Event published",
    "partnerEvent.createFailed": "Could not create event",
    "partnerEvent.createdMissingId": "Event created, but the ID needed to publish is missing",
    "partnerEvent.createdPublishFailed": "Event created, but it could not be published",
    "partnerEvent.createdAndPublished": "Event created and published",
    "partnerEvent.publishLimitReached": "Plan {{plan}} allows up to {{limit}} active events. Save the next one as a draft or upgrade your plan.",
    "partnerSetup.cityRequired": "Enter operating city",
    "partnerSetup.profileSaved": "Organizer profile saved",
    "partnerSetup.profileSaveFailed": "Could not save organizer profile",
    "profileSetup.profileSaved": "Profile saved",
    "profileSetup.profileSaveFailed": "Could not save profile",
    "partnerEvent.publishFailed": "Could not publish event",
    "partnerEvent.quickPublished": "Event published",
    "partnerEvent.archiveFailed": "Could not archive event",
    "partnerEvent.archived": "Event moved to archive",
    "partnerEvent.statusDraft": "Draft",
    "partnerEvent.sectionActiveTitle": "Active",
    "partnerEvent.sectionActiveDesc": "Events currently visible to users.",
    "partnerEvent.sectionDraftsTitle": "Drafts",
    "partnerEvent.sectionDraftsDesc": "Draft events before publishing.",
    "partnerEvent.sectionFinishedTitle": "Finished",
    "partnerEvent.sectionFinishedDesc": "Events whose date has already passed.",
    "partnerEvent.sectionArchivedTitle": "Archived",
    "partnerEvent.sectionArchivedDesc": "Closed or moved to archive.",
    "partnerEvent.countOne": "1 event",
    "partnerEvent.countFew": "{{count}} events",
    "partnerEvent.countMany": "{{count}} events",
    "partnerDash.metricActive": "Active",
    "partnerDash.metricActiveSub": "Published now",
    "partnerDash.metricDrafts": "Drafts",
    "partnerDash.metricDraftsSub": "Draft",
    "partnerDash.metricSignupsTotal": "Signups total",
    "admin.toastStatusSaved": "Report status saved",
    "admin.toastStatusSaveFailed": "Could not save status",
    "admin.toastBugNotFound": "Bug report not found",
    "admin.toastBugPreviewFailed": "Could not open bug preview",
    "app.viewMissing": "Missing view: {{view}}",
    "bugReport.ticketSent": "Report sent • #{{ticket}}",
    "bugReport.ticketSaved": "Report saved • #{{ticket}}",
    "partnerParticipants.sent": "Message sent",
    "settings.toast.saved": "Settings saved",
    "photo.modalTitle": "Add photo",
    "photo.heading": "Photo upload",
    "photo.subtitle": "Add a profile photo or leave it empty and use the placeholder.",
    "photo.save": "Save photo",
    "photo.toast.pickFile": "Choose a photo file",
    "photo.toast.uploadFailed": "Could not upload photo",
    "photo.toast.saved": "Photo saved",
    "photo.toast.removeFailed": "Could not remove photo",
    "photo.toast.removed": "Photo removed",
    "avatar.modalTitle": "Create AI avatar",
    "avatar.heading": "AI avatar",
    "avatar.subtitle": "Describe the style and USLY will generate an illustrated profile avatar. Generation may take a moment.",
    "avatar.statusChecking": "Checking limit...",
    "avatar.styleLabel": "Avatar style",
    "avatar.placeholder": "e.g. minimal, warm, elegant, pastel",
    "avatar.generate": "Generate avatar",
    "avatar.generating": "Generating...",
    "avatar.limitReached": "Limit reached",
    "avatar.toastDescribe": "Briefly describe avatar style",
    "avatar.toastLimitReached": "AI avatar limit for your plan has been reached",
    "avatar.toastFailed": "Could not generate avatar",
    "avatar.toastReady": "Avatar ready",
    "avatar.toastReadyRemaining": "Avatar ready. Remaining: {{remaining}}",
    "avatar.statusFailed": "Could not check AI avatar limit.",
    "avatar.statusLine": "Your plan: <b>{{plan}}</b> • AI avatars: <b>{{used}}/{{limit}}</b> this month • Remaining: <b>{{remaining}}</b>",
    "avatar.statusLimitLine": "Your plan: <b>{{plan}}</b> • You have used the <b>{{used}}/{{limit}}</b> AI avatar limit this month. Change plan to generate more.",
    "settings.deleteAccount": "Delete account",
    "settings.partnerProfileSub": "Complete your organizer profile.",
    "settings.logoTitle": "Venue logo",
    "settings.logoSub": "Add, replace or remove the organizer logo.",
    "settings.removeLogo": "Remove logo",
    "settings.dashboard": "Dashboard",
    "settings.placeData": "Venue details",
    "settings.industry": "Industry",
    "settings.orgAboutPlaceholder": "Briefly describe the place, vibe and offer.",
    "settings.partnerAccountSub": "Key Organizer account actions.",
    "settings.languageTitle": "App language",
    "settings.languageSub": "Change the language instantly, without logging out.",
    "settings.documents": "Documents",
    "settings.documentsSub": "Terms and Privacy Policy.",
    "settings.logout": "Log out",
    "common.back": "Back",
    "forgot.modal.title": "Password recovery",
    "forgot.heading": "Reset password",
    "forgot.subtitle": "Enter the email address assigned to your account. We will send you a link to set a new password.",
    "forgot.email.label": "Email",
    "forgot.email.placeholder": "e.g. ola@email.com",
    "forgot.submit": "Send link",
    "forgot.toast.email_required": "Enter your email address",
    "forgot.toast.success": "If the account exists, we will send a link to set a new password.",
    "forgot.toast.error": "Could not send the link. Please try again.",
    "reset.title": "Password reset",
    "reset.heading": "Set a new password",
    "reset.subtitle": "Confirm your account and set a new password for the app.",
    "reset.email": "Email",
    "reset.email_placeholder": "Email address",
    "reset.new_password": "New password",
    "reset.new_password_placeholder": "Enter a new password",
    "reset.repeat_password": "Repeat new password",
    "reset.repeat_password_placeholder": "Repeat new password",
    "reset.submit": "Save new password",
    "reset.toast.fill_passwords": "Fill in all password fields",
    "reset.toast.passwords_mismatch": "Passwords do not match",
    "reset.toast.password_too_short": "Password must be at least 8 characters",
    "reset.toast.missing_token": "Missing password reset token",
    "reset.toast.success": "Password has been changed",
    "reset.toast.change_error": "Could not change the password",
    "reset.toast.generic_error": "Password reset error",
    "reset.toast.missing_link": "Missing password reset link",
    "reset.toast.invalid_link": "Password reset link is invalid",
    "register.title": "Create account",
    "register.subtitle": "Create an account and continue to your profile.",
    "register.account.title": "Account",
    "register.email": "Email *",
    "register.email_placeholder": "e.g. ola@email.com",
    "register.nick": "Nickname / public name *",
    "register.nick_placeholder": "e.g. Ola / ola_88",
    "register.company": "Official venue / company name *",
    "register.company_placeholder": "e.g. Aurora Café",
    "register.password": "Password *",
    "register.password_placeholder": "Minimum 8 characters",
    "register.repeat_password": "Repeat password *",
    "register.repeat_password_placeholder": "Repeat password",
    "register.user.location_title": "Age and location",
    "register.birthdate": "Date of birth *",
    "register.birthdate_hint": "Format: DD.MM.YYYY",
    "register.age_required": "18+ required.",
    "register.location": "Location *",
    "register.location_placeholder": "Getting your city...",
    "register.location_note": "📍 Your area, better matches.",
    "register.partner.place_title": "Your place",
    "register.partner.city": "City *",
    "register.partner.city_placeholder": "e.g. Warsaw",
    "register.partner.plan_title": "Organizer plan",
    "register.partner.plan_subtitle": "Choose access for your place.",
    "register.partner.plan.free": "FREE • 0 PLN / mo.",
    "register.partner.plan.pro": "PRO • 129 PLN / mo.",
    "register.partner.plan.premium": "PREMIUM • 259 PLN / mo.",
    "register.partner.plan.enterprise": "ENTERPRISE • custom",
    "register.user.plan_title": "Plan",
    "register.user.plan_subtitle": "Choose your starting access.",
    "register.user.plan.free": "FREE • 0 PLN / mo.",
    "register.user.plan.plus": "PLUS • 29 PLN / mo.",
    "register.user.plan.premium": "PREMIUM • 49 PLN / mo.",
    "register.user.plan.vip": "VIP • 89 PLN / mo.",
    "register.plan_details": "See plan details",
    "register.accept_terms": "I accept the Terms & Conditions*",
    "register.accept_privacy": "I accept the Privacy Policy*",
    "register.submit": "Register",
    "register.legal.title": "Consents",
    "register.accept_terms_prefix": "I accept",
    "register.terms_link": "Terms & Conditions*",
    "register.accept_privacy_prefix": "I accept",
    "register.privacy_link": "Privacy Policy*",
    "register.toast.consents_required": "Accept the required consents (*)",
    "register.toast.account_required": "Fill in email, password and repeated password (min. 8 characters)",
    "register.toast.birthdate_required": "Enter your date of birth.",
    "register.toast.birthdate_invalid": "Invalid date of birth.",
    "register.toast.age_under_18": "You cannot register — you must be at least 18 years old.",
    "register.toast.nick_required": "Fill in date of birth and nickname",
    "register.toast.location_required": "Enable location to continue",
    "register.toast.partner_required": "Fill in organizer name and city",
    "register.toast.create_error": "Could not create account",
    "register.toast.auto_login_error": "Account created, but automatic login failed",
    "register.toast.created_logged_in": "Account created and logged in",
    "register.toast.create_error": "Could not create account",
    "login.toast.missing": "Enter email and password",
    "login.toast.error": "Login error",
    "login.toast.roleMismatch": "This account belongs to a different role. Choose the correct account type and try again.",
    "login.toast.success": "Logged in",
    "logout.toast.success": "Logged out",
    "social.loginSoon": "Social login will be available soon",
    "social.signupSoon": "Social signup will be available soon",
    "role.user": "Companion",
    "role.partner": "Organizer",
    "auth.registerChoice.title": "How do you want to use USLY?",
    "auth.registerChoice.subtitle": "Choose your role and registration method.",
    "auth.loginChoice.title": "How do you want to log in?",
    "auth.loginChoice.subtitle": "Choose your role and login method.",
    "auth.role.userDesc": "For people who want to meet others, join events and build a local community.",
    "auth.role.partnerDesc": "For places, brands and people who create events, classes or local initiatives.",
    "auth.role.userLoginDesc": "Meet people, discover events and build your local community.",
    "auth.role.partnerLoginDesc": "Create events, reach new participants and grow your community.",
    "auth.method.email": "Email address",
    "auth.method.google": "Google",
    "auth.method.apple": "Apple",
    "auth.methodLabel.email": "email address",
    "auth.methodLabel.google": "Google",
    "auth.methodLabel.apple": "Apple",
    "auth.loginMethodTitle": "Login with {{method}}",
    "auth.registerMethodTitle": "Registration with {{method}}",
    "register.user.subtitleDynamic": "Create a Companion account and set up your profile.",
    "register.partner.subtitleDynamic": "Create an Organizer account and set up your profile.",
    "plans.toast.saveFailed": "Could not save plan",
    "plans.toast.partnerSaveFailed": "Could not save organizer plan",
    "plans.toast.selected": "Selected plan: {{plan}}",
    "enterprise.toast.contactRequired": "Enter an email or phone number for contact",
    "enterprise.toast.sending": "Sending...",
    "enterprise.toast.failed": "Could not send inquiry",
    "enterprise.toast.sent": "Inquiry sent. I will get back to you with an offer.",
    "groups.create.availablePlus": "Available from PLUS",
    "groups.create.limitReached": "Limit reached",
    "groups.create.button": "Create group",
    "groups.create.hintLocked": "Creating your own groups is available from the PLUS plan.",
    "groups.create.hintUnlimited": "Created groups: {{count}} • VIP plan allows unlimited groups.",
    "groups.create.hintReached": "Created groups: {{count}} / {{limit}} • You have reached the limit for this plan.",
    "groups.create.hintLeft": "Created groups: {{count}} / {{limit}} • You can still create {{left}}.",
    "groups.create.toastLocked": "Group creation is available from the PLUS plan",
    "groups.create.modalTitle": "Create group",
    "groups.create.title": "Group title *",
    "groups.create.titlePlaceholder": "e.g. Warsaw Coffee Lovers",
    "groups.create.interest": "Hashtag / interest *",
    "groups.create.interestPlaceholder": "e.g. coffee",
    "groups.create.description": "Description",
    "groups.create.descriptionPlaceholder": "Short group description (optional)",
    "groups.create.planUnlimited": "You can create unlimited groups.",
    "groups.create.planLimited": "This plan allows up to {{limit}} own groups.",
    "groups.create.submit": "Create",
    "groups.create.cancel": "Cancel",
    "groups.create.toastTitle": "Enter group name (min. 3 characters)",
    "groups.create.toastInterest": "Enter group hashtag",
    "groups.create.toastFailed": "Could not create group",
    "groups.create.toastSuccess": "Group created",
    "plans.user.plus.price": "29 PLN / month",
    "plans.user.premium.price": "49 PLN / month",
    "plans.user.vip.price": "89 PLN / month",
    "plans.subtitle": "See feature differences before logging in.",
    "plans.preview": "Preview plans",
    "login.no_account": "Don’t have an account? Register",
    "login.forgot_password": "Forgot password?",
    "welcome.title": "Your city. Your people.",
    "welcome.claim.line1": "Your city.",
    "welcome.claim.line2": "Your people.",
    "welcome.value.line1": "Meet people.",
    "welcome.value.line2": "Create events.",
    "welcome.value.line3": "Build community.",
    "welcome.micro": "One #. Thousands of possibilities.",
    "welcome.tag.sport": "#sports",
    "welcome.tag.coffee": "#coffee",
    "welcome.tag.concert": "#concerts",
    "welcome.tag.boardgames": "#boardgames",
    "welcome.tag.fitness": "#fitness",
    "welcome.tag.startup": "#startup",
    "welcome.subtitle": "People, conversations and events built around interests — not chance.",
    "welcome.tagline": "Meet people through interests, not looks.",
    "landing.pill.interests": "Meet through shared interests",
    "landing.pill.vibe": "Find people who match your vibe",
    "landing.pill.places": "Go to places that feel right",
    "welcome.langAria": "Language selection",
    "welcome.choose_account": "Choose account",
    "welcome.user": "Meet people",
    "welcome.partner": "Create events",
    "welcome.start": "Start",
    "welcome.have_account": "Log in",
    "welcome.promo": "Discover your city through people you genuinely connect with.",
    "welcome.plans_subtitle": "Choose the mode that fits you best.",
    "welcome.see_plans": "See plans",
  },
};

function t(key, fallback = "") {
  const lang = App?.lang || "pl";
  const params = fallback && typeof fallback === "object" ? fallback : null;
  let value = I18N?.[lang]?.[key] || I18N?.pl?.[key] || (params ? "" : fallback) || key;
  if (params) {
    Object.entries(params).forEach(([name, paramValue]) => {
      value = String(value).replaceAll(`{{${name}}}`, String(paramValue ?? ""));
    });
  }
  return value;
}

function setLanguage(lang) {
  App.lang = lang === "en" ? "en" : "pl";
  localStorage.setItem("usly_lang", App.lang);
  updateAuthHeadings();

  renderAll();
}

function applyI18n(root = document) {
  if (!root) return;

  root.querySelectorAll("[data-lang-choice]").forEach((el) => {
    el.classList.toggle("active", String(el.dataset.langChoice || "pl") === String(App.lang || "pl"));
  });

  root.querySelectorAll("[data-i18n]").forEach((el) => {
    const key = el.dataset.i18n;
    if (!key) return;
    el.textContent = t(key, el.textContent || "");
  });
  root.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
    const key = el.dataset.i18nPlaceholder;
    if (!key) return;
    el.setAttribute("placeholder", t(key, el.getAttribute("placeholder") || ""));
  });

  root.querySelectorAll("[data-i18n-aria-label]").forEach((el) => {
    const key = el.dataset.i18nAriaLabel;
    if (!key) return;
    el.setAttribute("aria-label", t(key, el.getAttribute("aria-label") || ""));
  });
}


/* ------------------------- App State -------------------------- */
const App = {
  lang: localStorage.getItem("usly_lang") === "en" ? "en" : "pl", // default: pl
  role: "user", // 'user' | 'partner'
  isLoggedIn: false,
  history: ["S0_WELCOME"],
  currentView: "S0_WELCOME",
  authMode: "register",      // register | login
  authMethod: "email",       // email | google | apple
  resetToken: "",
  resetEmail: "",
  partnerEventFormMode: "create", // create | draft_edit | published_edit | archived_edit
  planScreenMode: "settings", // settings | onboarding

  // Sub-states / filters
  eventsTab: "for_you", // 'for_you' | 'followed'

  // Profile 
  user: {
    plan: "free", // free | plus | premium | vip
    email: "",
    nick: "",
    city: "",
    age: "",
    bio: "",
    interests: [],
    trainerInterests: [],
    prefAgeFrom: 18,
    prefAgeTo: 35,
    geo: { lat: "", lng: "" },
    avatarEmoji: "",
    avatarUrl: "",
  },

  partner: {
    plan: "free", // free | pro | premium | enterprise
    email: "",
    company: "Studio Miejsce",
    category: "gastro",
    city: "Warszawa",
    about: "",
    logoEmoji: "",
  },

  // data
  people: [],

  events: [],

  // Group model: interestTag used for filtering by profile interests
  groups: [],

  myGroups: [],
  partnerEvents: [],

  chats: [],

  // Working selection
  selectedPersonId: null,
  selectedEventId: null,
  selectedPartnerEventId: null,
  selectedChatId: null,
  selectedChatUserId: null,
  currentUserId: null,
  currentRevenueCatAppUserId: null,
  selectedGroupId: null,
};

window.App = App;

/* ------------------------- DOM Helpers -------------------------- */
const $ = (id) => document.getElementById(id);

const USLY_STORAGE_KEYS = {
  token: "usly_token",
  userPlan: "usly_user_plan",
  partnerPlan: "usly_partner_plan",
  savedEvents: "usly_saved_events",
};

try {
  const hasToken =
    !!localStorage.getItem(USLY_STORAGE_KEYS.token) ||
    !!localStorage.getItem("usly_token");

  if (hasToken) {
    const savedUserPlan = localStorage.getItem(USLY_STORAGE_KEYS.userPlan);
    if (savedUserPlan && ["free", "plus", "premium", "vip"].includes(savedUserPlan)) {
      App.user.plan = savedUserPlan;
    }

    const savedPartnerPlan = localStorage.getItem(USLY_STORAGE_KEYS.partnerPlan);
    if (savedPartnerPlan && ["free", "pro", "premium", "enterprise"].includes(savedPartnerPlan)) {
      App.partner.plan = savedPartnerPlan;
    }
  } else {
    App.user.plan = "free";
    App.partner.plan = "free";
  }
} catch (_) {
  App.user.plan = "free";
  App.partner.plan = "free";
}

function safeSetText(id, text) {
  const el = $(id);
  if (el) el.textContent = text;
}

function show(el) { if (el) el.style.display = ""; }
function hide(el) { if (el) el.style.display = "none"; }

function getSavedEventIds() {
  try {
    const raw = localStorage.getItem(USLY_STORAGE_KEYS.savedEvents);
    const arr = raw ? JSON.parse(raw) : [];
    return new Set(Array.isArray(arr) ? arr.map(String) : []);
  } catch (_) {
    return new Set();
  }
}

function persistSavedEventIds() {
  try {
    const ids = App.events.filter(e => e.saved).map(e => String(e.id));
    localStorage.setItem(USLY_STORAGE_KEYS.savedEvents, JSON.stringify(ids));
  } catch (_) {}
}

function syncEventDetailButtons() {
  const ev = App.events.find(e => String(e.id) === String(App.selectedEventId));
  if (!ev) return;

  const saveBtn = document.querySelector('#S7B_EVENT_DETAIL button[onclick="toggleSaveEvent()"]');
  const interestedBtn = document.querySelector('#S7B_EVENT_DETAIL button[onclick="toggleInterestedEvent()"]');

  if (saveBtn) {
    saveBtn.textContent = ev.saved ? t("eventDetail.observed") : t("eventDetail.observe");
  }

  if (interestedBtn) {
    interestedBtn.textContent = ev.interested ? t("eventDetail.cancelInterest") : t("eventDetail.interested");
  }
}

/* ------------------------- Navigation -------------------------- */
function applyPlanScreenMode() {
  const isOnboarding = App.planScreenMode === "onboarding";
  const isPartner = App.role === "partner";
  const currentUserPlan = String(App.user?.plan || "free").toLowerCase();
  const currentPartnerPlan = String(App.partner?.plan || "free").toLowerCase();

  const plansUserOnly = $("plansUserOnly");
  const plansPartnerOnly = $("plansPartnerOnly");
  if (plansUserOnly && plansPartnerOnly) {
    if (isPartner) {
      hide(plansUserOnly);
      show(plansPartnerOnly);
    } else {
      show(plansUserOnly);
      hide(plansPartnerOnly);
    }
  }

  document.querySelectorAll("#S11_PLANS .restorePurchaseCard").forEach((el) => {
    el.style.display = isOnboarding ? "none" : "";
  });

  document.querySelectorAll("#S11_PLANS .onboardingOnly").forEach((el) => {
    el.style.display = isOnboarding ? "" : "none";
  });

  const planCards = [
    { selector: "#S11_PLANS #plansUserOnly .card[data-plan]", current: currentUserPlan, role: "user" },
    { selector: "#S11_PLANS #plansPartnerOnly .card[data-plan]", current: currentPartnerPlan, role: "partner" },
  ];

  planCards.forEach(({ selector, current, role }) => {
    document.querySelectorAll(selector).forEach((card) => {
      const plan = String(card.dataset.plan || "").toLowerCase();
      const isCurrent = plan === current;
      const btn = card.querySelector(".btn.secondary, .btn");

      card.classList.toggle("is-current", !isOnboarding && isCurrent);
      card.classList.toggle("is-recommended-plan", isOnboarding && role === "user" && plan === "free");
      card.classList.toggle("is-recommended-partner-plan", isOnboarding && role === "partner" && plan === "pro");

      if (!btn) return;

      if (isOnboarding) {
        const onboardingKeys = {
          free: "plans.continueFree",
          plus: "plans.continuePlus",
          premium: "plans.continuePremium",
          vip: "plans.continueVip",
          pro: "plans.continuePro",
        };
        btn.textContent = t(onboardingKeys[plan] || "plans.choose");
        return;
      }

      btn.textContent = plan === "enterprise"
        ? t("plans.contact_us", "Napisz do nas")
        : (isCurrent ? t("plans.current", "Aktualny plan") : t("plans.choose", "Wybierz"));
    });
  });

  const plansBackBtn = $("plansBackBtn");
  if (plansBackBtn) {
    plansBackBtn.style.visibility = isOnboarding ? "hidden" : "";
  }

  safeSetText("plansScreenTopTitle", isOnboarding ? t("plans.onboarding.topTitle") : t("plans.title"));
  safeSetText("plansUserHeroTitle", isOnboarding ? t("plans.onboarding.title") : t("plans.user.title"));
  safeSetText(
    "plansUserHeroSubtitle",
    isOnboarding
      ? t("plans.onboarding.userSubtitle")
      : t("plans.user.subtitle")
  );
  safeSetText("plansPartnerHeroTitle", isOnboarding ? t("plans.onboarding.title") : t("plans.partner.title"));
  safeSetText(
    "plansPartnerHeroSubtitle",
    isOnboarding
      ? t("plans.onboarding.partnerSubtitle")
      : t("plans.partner.subtitle")
  );
}

function goToPlansSettings() {
  App.planScreenMode = "settings";
  go("S11_PLANS");
}

function go(viewId) {
  if (!viewId) return;
  const current = App.currentView;
  if (current === viewId) {
    if (viewId === "S11_PLANS") applyPlanScreenMode();
    return;
  }

  // Hide all
  document.querySelectorAll(".view").forEach(v => v.classList.remove("active"));

  const next = $(viewId);
  if (!next) {
    toast(t("app.viewMissing", { view: viewId }));
    return;
  }
  next.classList.add("active");

  App.currentView = viewId;
  App.history.push(viewId);

  if (viewId === "S11_PLANS") {
    applyPlanScreenMode();
  }

  if (viewId === "S10E_PROFILE_INVITES" || viewId === "S12_NOTIFICATIONS") {
    updateNotifBadges(0);
  }

  if (viewId === "S10E_PROFILE_INVITES") {
    refreshProfileRelations().catch(() => {});
  }

  if (viewId === "S9_PARTNER_EVENTS") {
    renderPartnerEvents();
    loadPartnerEvents().then(() => {
      if (App.currentView === "S9_PARTNER_EVENTS") renderPartnerEvents();
    }).catch(() => {});
  }

  if (viewId === "S2_REGISTER" && App.role === "user") {
    useCurrentLocationForCity();
  }


  
  if (viewId === "S3_PROFILE_SETUP" && App.role === "user") {
    const setupCity = $("setupCity");
    if (setupCity) setupCity.value = "Pobieranie lokalizacji...";

    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          const lat = approximateCoordinate(pos.coords.latitude);
          const lng = approximateCoordinate(pos.coords.longitude);
          if (lat == null || lng == null) return;

          App.user.geo = App.user.geo || {};
          App.user.geo.lat = String(lat);
          App.user.geo.lng = String(lng);

          const cityInput = $("setupCity");
          if (cityInput) cityInput.value = "Pobieranie lokalizacji...";

          apiFetch("/users/me", {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              location_lat: lat,
              location_lng: lng,
            }),
          })
            .then((data) => {
              App.user.city = data?.data?.miasto || App.user.city;
              App.user.geo = App.user.geo || {};
              App.user.geo.lat = String(data?.data?.location_lat || lat);
              App.user.geo.lng = String(data?.data?.location_lng || lng);

              if (cityInput) cityInput.value = App.user.city || "Lokalizacja pobrana";
            })
            .catch(() => {
              if (cityInput) cityInput.value = App.user.city || "Lokalizacja pobrana";
            });
        },
        () => {},
        { enableHighAccuracy: true, timeout: 5000, maximumAge: 60000 }
      );
    }
  }


if (viewId === "S4_NEARBY" && App.role === "user") {
    const pList = $("nearbyPeopleList");
    const eList = $("nearbyEventsList");
    if (pList) pList.innerHTML = `<div class="tMuted">${t("geo.fetching")}</div>`;
    if (eList) eList.innerHTML = `<div class="tMuted">${t("geo.fetching")}</div>`;

    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          const lat = approximateCoordinate(pos.coords.latitude);
          const lng = approximateCoordinate(pos.coords.longitude);
          if (lat == null || lng == null) return;

          App.user.geo.lat = String(lat);
          App.user.geo.lng = String(lng);

          Promise.all([loadNearbyPeople(lat, lng), loadNearbyEvents(lat, lng)])
            .then(() => renderNearby())
            .catch((err) => console.error("nearby refresh failed", err));

          apiFetch("/users/me", {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              location_lat: lat,
              location_lng: lng,
            }),
          }).catch((err) => console.error("location save failed", err));

          if (nearbyMap) {
            nearbyMap.setView([lat, lng], 12);
            renderNearbyMapMarkers();
          }
        },
        (err) => {
          console.warn("nearby geolocation failed", err);
          toast(t("geo.failed"));
        },
        { enableHighAccuracy: false, timeout: 20000, maximumAge: 0 }
      );
    }
  }

  if (viewId === "S10_SETTINGS") {
    if ($("setNick")) $("setNick").value = App.user.nick || "";
    if ($("setBio")) $("setBio").value = App.user.bio || "";
    if ($("setCity")) $("setCity").value = App.user.city || "";

    safeSetText("settingsProfileHeroNick", App.user.nick || t("settings.profile"));
    safeSetText(
      "settingsProfileHeroMeta",
      [App.user.city, App.user.bio].filter(Boolean).join(" • ") || t("settings.profileSub")
    );
    safeSetText("settingsProfilePlanPill", String(App.user.plan || "FREE").toUpperCase());
    safeSetText("settingsProfilePlanPillSecondary", String(App.user.plan || "FREE").toUpperCase());
    if ($("setupPrefAgeFrom")) $("setupPrefAgeFrom").value = String(App.user.prefAgeFrom);
    if ($("setupPrefAgeTo")) $("setupPrefAgeTo").value = String(App.user.prefAgeTo);
    safeSetText("setupAgeDisplay", t("settings.ageLabel", { age: App.user.age || "—" }));
    safeSetText("setPrefAgeFromVal", String(App.user.prefAgeFrom));
    safeSetText("setPrefAgeToVal", String(App.user.prefAgeTo));
    refreshProfileRelations().catch(() => {});
  }

  // Render after navigation
  renderAll();
}

function back() {
  if (App.history.length <= 1) return go("S0_WELCOME");
  // Remove current
  App.history.pop();
  const prev = App.history[App.history.length - 1] || "S0_WELCOME";

  document.querySelectorAll(".view").forEach(v => v.classList.remove("active"));
  const prevEl = $(prev);
  if (prevEl) prevEl.classList.add("active");
  App.currentView = prev;

  renderAll();

  if (prev === "S4_NEARBY" && App.role === "user") {
    loadNearbyPeople()
      .then(() => renderNearby())
      .catch(() => renderNearby());
  }
}

/* ------------------------- Toast -------------------------- */
let toastTimer = null;
function toast(message) {
  const el = $("toast");
  if (!el) return;

  el.textContent = message || "";
  el.style.cssText = [
    "position:fixed",
    "left:50%",
    "right:auto",
    "top:auto",
    "bottom:calc(92px + env(safe-area-inset-bottom))",
    "width:fit-content",
    "min-width:0",
    "max-width:280px",
    "height:auto",
    "min-height:0",
    "padding:9px 13px",
    "border-radius:16px",
    "background:rgba(14,18,28,.92)",
    "border:1px solid rgba(255,255,255,.18)",
    "color:rgba(247,251,255,.96)",
    "font-size:12px",
    "font-weight:850",
    "line-height:1.25",
    "text-align:center",
    "white-space:normal",
    "box-shadow:0 12px 28px rgba(0,0,0,.28),0 0 16px rgba(58,224,255,.08)",
    "backdrop-filter:blur(16px) saturate(1.18)",
    "z-index:99999",
    "pointer-events:none",
    "opacity:0",
    "transform:translate(-50%, 10px)",
    "transition:opacity .16s ease, transform .16s ease"
  ].join(";");

  requestAnimationFrame(() => {
    el.style.opacity = "1";
    el.style.transform = "translate(-50%, 0)";
  });

  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    el.style.opacity = "0";
    el.style.transform = "translate(-50%, 10px)";
  }, 2200);
}

/* ------------------------- Modal -------------------------- */
function openModal(title, html) {
  const overlay = $("modalOverlay");
  const body = $("modalBody");
  const ttl = $("modalTitle");
  if (!overlay || !body || !ttl) return;

  ttl.textContent = title || "USLY";
  body.innerHTML = html || "";

  const footer = document.querySelector("#modalBox .modalFooter");
  if (footer) {
    footer.style.display = String(html || "").includes('data-hide-modal-footer="1"') ? "none" : "";
  }

  overlay.classList.add("show");
  overlay.setAttribute("aria-hidden", "false");
}

function closeModal() {
  const overlay = $("modalOverlay");
  if (!overlay) return;
  overlay.classList.remove("show");
  overlay.setAttribute("aria-hidden", "true");
}

/* ------------------------- Bug Report -------------------------- */
// Minimal UI for "Zgłoś błąd" button added in S10_SETTINGS.
// Does not remove/alter any existing behavior.
function openBugReport() {
  openModal(t("bugReport.modalTitle"), `
    <div class="tStrong">${t("bugReport.heading")}</div>
    <div class="sectionSub mt10">${t("bugReport.subtitle")}</div>
    <label class="mt12">${t("bugReport.label")}</label>
    <textarea id="bugReportText" maxlength="1000" placeholder="${t("bugReport.placeholder")}"></textarea>
    <div class="charHint"><span id="bugReportCount">0</span>/1000</div>
    <button class="btn mt16" type="button" onclick="submitBugReport()">${t("bugReport.submit")}</button>
  `);

  const ta = $("bugReportText");
  const cnt = $("bugReportCount");
  if (ta && cnt) {
    const upd = () => (cnt.textContent = String(ta.value.length));
    ta.addEventListener("input", upd);
    upd();
    // autofocus
    setTimeout(() => ta.focus(), 0);
  }
}

function submitBugReport() {
  const ta = $("bugReportText");
  const message = (ta?.value || "").trim();
  if (!message) {
    toast(t("bugReport.toast.empty"));
    return;
  }

  // Optional API base override via window.USLY_API_BASE.
  // Example: window.USLY_API_BASE = "https://api.example.com";
  const base = window.USLY_API_BASE;
  if (base) {
    fetch(String(base).replace(/\/$/, "") + "/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        type: "bug",
        message,
        // Minimal context to help diagnose (safe for MVP tests)
        view: App.currentView,
        role: App.role,
      }),
    })
      .then(async (r) => {
        if (!r.ok) throw new Error("HTTP " + r.status);
        toast(t("bugReport.toast.sent"));
        closeModal();
      })
      .catch(() => {
        toast(t("bugReport.toast.failed"));
        closeModal();
      });
    return;
  }

  // fallback
  toast(t("bugReport.toast.saved"));
  closeModal();
}

/* ------------------------- Role Selection -------------------------- */
function selectRole(role) {
  if (role !== "user" && role !== "partner") return;
  App.role = role;

  // Toggle segmented buttons (where present)
  const pairs = [
    ["roleUserBtn", "rolePartnerBtn"],
    ["roleUserBtnLogin", "rolePartnerBtnLogin"],
    ["roleUserBtn2", "rolePartnerBtn2"],
  ];
  pairs.forEach(([u, p]) => {
    const uEl = $(u), pEl = $(p);
    if (!uEl || !pEl) return;
    if (role === "user") {
      uEl.classList.add("on"); pEl.classList.remove("on");
    } else {
      pEl.classList.add("on"); uEl.classList.remove("on");
    }
  });

  // Labels
  safeSetText("roleLabelLogin", role === "user" ? t("role.user") : t("role.partner"));
  safeSetText("roleLabelRegister", role === "user" ? t("role.user") : t("role.partner"));
  safeSetText("regSubLine", role === "user"
    ? t("register.user.subtitleDynamic")
    : t("register.partner.subtitleDynamic"));

  // Show/Hide registration account fields
  const regUserAccountFields = $("regUserAccountFields");
  const regPartnerAccountFields = $("regPartnerAccountFields");
  if (regUserAccountFields && regPartnerAccountFields) {
    if (role === "user") { show(regUserAccountFields); hide(regPartnerAccountFields); }
    else { hide(regUserAccountFields); show(regPartnerAccountFields); }
  }

  // Show/Hide registration blocks
  const userBox = $("regUserBox");
  const userPlanBox = $("regUserPlanBox");
  const partnerBox = $("regPartnerBox");
  const partnerPlanBox = $("regPartnerPlanBox");
  if (userBox && partnerBox) {
    if (role === "user") {
      show(userBox);
      hide(partnerBox);
    } else {
      hide(userBox);
      show(partnerBox);
    }
  }
  if (userPlanBox) hide(userPlanBox);
  if (partnerPlanBox) hide(partnerPlanBox);

  // Settings sections
  const settingsUser = $("settingsUserBox");
  const settingsPartner = $("settingsPartnerBox");
  if (settingsUser && settingsPartner) {
    if (role === "user") { show(settingsUser); hide(settingsPartner); }
    else { hide(settingsUser); show(settingsPartner); }
  }

  // Plans sections
  const plansUserOnly = $("plansUserOnly");
  const plansPartnerOnly = $("plansPartnerOnly");
  if (plansUserOnly && plansPartnerOnly) {
    if (role === "user") { show(plansUserOnly); hide(plansPartnerOnly); }
    else { hide(plansUserOnly); show(plansPartnerOnly); }
  }

  // Update tabbars visibility (still controlled by login class + role)
  updateTabbars();

  // Re-render pills etc.
  renderAll();
}

function updateAuthHeadings() {
  const roleLabel = App.role === "partner" ? t("role.partner") : t("role.user");
  const method = App.authMethod === "google" || App.authMethod === "apple" ? App.authMethod : "email";
  const methodLabel = t("auth.methodLabel." + method);
  const isEmail = method === "email";

  safeSetText("authLoginRoleTitle", roleLabel);
  safeSetText(
    "authLoginRoleDesc",
    App.role === "partner"
      ? t("auth.role.partnerLoginDesc")
      : t("auth.role.userLoginDesc")
  );
  safeSetText("authLoginMethodTitle", t("auth.loginMethodTitle", { method: methodLabel }));
  safeSetText("authRegisterRoleTitle", roleLabel);
  safeSetText("authRegisterMethodTitle", t("auth.registerMethodTitle", { method: methodLabel }));

  const loginPasswordBlock = $("loginPasswordBlock");
  const registerPasswordBlock = $("registerPasswordBlock");
  if (loginPasswordBlock) loginPasswordBlock.style.display = isEmail ? "" : "none";
  if (registerPasswordBlock) registerPasswordBlock.style.display = isEmail ? "" : "none";
}

function selectAuthChoice(mode, role, method) {
  if ((mode !== "login" && mode !== "register") || (role !== "user" && role !== "partner")) return;

  App.authMode = mode;
  App.authMethod = method === "google" || method === "apple" ? method : "email";
  selectRole(role);
  updateAuthHeadings();

  const viewId = mode === "login" ? "S1_LOGIN" : "S2_REGISTER";
  go(viewId);
}

/* ------------------------- Login / Signup -------------------------- */
function syncAccountEmail(email) {
  const cleanEmail = String(email || "").trim();
  if (!cleanEmail) return;

  if (App.role === "partner") {
    App.partner.email = cleanEmail;
    const el = $("setOrgEmail");
    if (el) el.value = cleanEmail;
  } else {
    App.user.email = cleanEmail;
    const el = $("setEmail");
    if (el) el.value = cleanEmail;
  }
}

async function loginPrimary() {
  const email = $("loginId")?.value?.trim();
  const password = $("loginPass")?.value?.trim();

  if (!email || !password) {
    toast(t("login.toast.missing"));
    return;
  }

  try {
    const data = await apiFetch("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password, expected_role: App.role === "partner" ? "partner" : "user" }),
    });

    if (!data?.success || !data?.data?.access_token) {
      toast(data?.error?.message || t("login.toast.error"));
      return;
    }

    localStorage.setItem("usly_token", data.data.access_token);

    const me = await apiFetch("/auth/me");
    const meData = me?.data || me || {};
    App.currentUserId = meData.id ?? null;
    App.currentRevenueCatAppUserId = meData.revenuecat_app_user_id ?? null;
    App.role = meData.role === "admin" ? "admin" : (meData.role === "partner" ? "partner" : "user");
    App.isLoggedIn = true;
    setupPushNotifications();

    if (App.role === "admin") {
      window.location.href = "admin.html";
      return;
    }

    const accountEmail = meData.email || "";
    syncAccountEmail(accountEmail);

    if (App.role === "user") {
      const profile = await apiFetch("/users/me");
      if (profile?.success && profile?.data) {
        App.user.nick = profile.data.nick || App.user.nick;
        App.user.city = profile.data.miasto || App.user.city;
        App.user.bio = profile.data.bio || "";
        App.user.prefAgeFrom = Object.prototype.hasOwnProperty.call(profile.data, "age_min") ? profile.data.age_min : App.user.prefAgeFrom;
        App.user.prefAgeTo = Object.prototype.hasOwnProperty.call(profile.data, "age_max") ? profile.data.age_max : App.user.prefAgeTo;
        App.user.nearbyRadiusKm = Object.prototype.hasOwnProperty.call(profile.data, "nearby_radius_km") ? profile.data.nearby_radius_km : App.user.nearbyRadiusKm;
        const backendInterests = Array.isArray(profile.data.zainteresowania) ? profile.data.zainteresowania : [];

        App.user.interests = backendInterests;
        App.user.trainerInterests = Array.isArray(profile.data.trainer_interests) ? profile.data.trainer_interests : [];
        try { localStorage.setItem("usly_user_interests", JSON.stringify(backendInterests)); } catch(_) {}
        App.user.plan = profile.data.plan || App.user.plan;
        App.user.avatarUrl = profile.data.avatar_url ?? "";
        if (profile.data.location_lat != null && profile.data.location_lng != null) {
          App.user.geo.lat = String(profile.data.location_lat);
          App.user.geo.lng = String(profile.data.location_lng);
        }
        try { localStorage.setItem(USLY_STORAGE_KEYS.userPlan, App.user.plan); } catch (_) {}
      }
    } else {
      // Partner data is loaded after first render to keep login fast.
    }

    $("appRoot")?.classList.add("isLoggedIn");
updateTabbars();

if (App.role === "user") {
  renderAll();
  bindMessageInputs();

  toast(t("login.toast.success"));
  go("S4_NEARBY");

  Promise.allSettled([loadEvents(), loadMyGroups(), loadGroups(), renderChatList()])
    .then(() => renderAll())
    .catch((err) => console.error("post-login background refresh failed", err));
} else {
  renderAll();
  bindMessageInputs();

  toast(t("login.toast.success"));
  go("S9_PARTNER");

  Promise.allSettled([loadPartnerProfile(), loadPartnerEvents()])
    .then(() => renderAll())
    .catch((err) => console.error("partner post-login background refresh failed", err));
}
  } catch (err) {
    const code = String(err?.code || err?.data?.error?.code || err?.data?.code || err?.data?.detail || err?.message || "");
    toast(code.includes("INSUFFICIENT_ROLE") ? t("login.toast.roleMismatch") : (err?.userMessage || t("login.toast.error")));
  }
}

async function loadPartnerProfile() {
  try {
    const profile = await apiFetch("/partners/me");
    if (profile?.success && profile?.data) {
      App.partner.company = profile.data.nazwa || App.partner.company;
      App.partner.city = profile.data.miasto || App.partner.city;
      App.partner.category = profile.data.kategoria || App.partner.category || "inne";
      App.partner.plan = profile.data.plan || App.partner.plan || "free";
      App.partner.about = profile.data.bio || "";
      App.partner.logoUrl = profile.data.logo_url || "";
    }
  } catch (err) {
    console.error("loadPartnerProfile failed", err);
  }
}

function loginSocial(provider) {
  toast(t("social.loginSoon"));
}

function signupSocial(provider) {
  toast(t("social.signupSoon"));
}

function logout() {
  App.isLoggedIn = false;
  try { localStorage.removeItem("usly_token"); } catch (_) {}
  try { localStorage.removeItem(USLY_STORAGE_KEYS.userPlan); } catch (_) {}
  try { localStorage.removeItem("usly_user_interests"); } catch (_) {}

  App.currentUserId = null;
  App.currentRevenueCatAppUserId = null;
  App.selectedPersonId = null;
  App.selectedChatId = null;
  App.selectedChatUserId = null;
  App.selectedEventId = null;
  App.selectedGroupId = null;

  App.user.plan = "free";
  App.user.nick = "";
  App.user.city = "";
  App.user.age = 24;
  App.user.bio = "";
  App.user.interests = [];
  App.user.prefAgeFrom = 18;
  App.user.prefAgeTo = 35;
  App.user.avatarUrl = "";

  App.people = [];
  App.chats = [];
  App.myGroups = [];

  $("appRoot")?.classList.remove("isLoggedIn");

  hide($("tabbarUser"));
  hide($("tabbarPartner"));

  toast(t("logout.toast.success"));
  App.history = ["S0_WELCOME"];
  go("S0_WELCOME");
}
function openForgot() {
  openModal(t("forgot.modal.title"), `
    <div class="tStrong">${t("forgot.heading")}</div>
    <div class="sectionSub">${t("forgot.subtitle")}</div>
    <label class="mt12">${t("forgot.email.label", "Email")}</label>
    <input id="forgotEmail" type="email" placeholder="${t("forgot.email.placeholder", "np. ola@email.com")}" />
    <button class="btn mt16" type="button" onclick="submitForgotPassword()">${t("forgot.submit")}</button>
  `);
}

async function submitForgotPassword() {
  const email = ($("forgotEmail")?.value || "").trim().toLowerCase();

  if (!email) {
    toast(t("forgot.toast.email_required", "Podaj adres e-mail"));
    return;
  }

  try {
    await apiFetch("/auth/forgot-password", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email }),
    });

    closeModal();
    toast(t("forgot.toast.success"));
  } catch (err) {
    toast(err?.userMessage || t("forgot.toast.error"));
  }
}

/* ------------------------- Registration -------------------------- */
async function registerPrimary() {
  const terms = $("acceptTerms")?.checked;
  const rodo = $("acceptRodo")?.checked;
  if (!terms || !rodo) {
    toast(t("register.toast.consents_required", "Zaznacz wymagane zgody (*)"));
    return;
  }

  const email = $("regEmail")?.value?.trim();
  const pass = $("regPass")?.value?.trim();
  const passRepeat = $("regPassRepeat")?.value?.trim();

  if (!email || !pass || !passRepeat || pass.length < 8) {
    toast(t("register.toast.account_required"));
    return;
  }

  if (pass !== passRepeat) {
    toast(t("reset.toast.passwords_mismatch"));
    return;
  }

  let dob = "";

  if (App.role === "user") {
    const city = normalizeCity($("regCity")?.value);
    const nick = $("regNick")?.value?.trim();

    const dobEl = $("regBirthDate");
    const errEl = $("ageError");
    dob = (dobEl?.value || "").trim();

    function showAgeError(msg) {
      if (errEl) {
        errEl.style.display = "block";
        errEl.textContent = msg;
      }
      toast(msg);
    }

    function hideAgeError() {
      if (errEl) errEl.style.display = "none";
    }

    if (!dob) {
      showAgeError(t("register.toast.birthdate_required"));
      return;
    }

    const birth = new Date(dob);
    if (Number.isNaN(birth.getTime())) {
      showAgeError(t("register.toast.birthdate_invalid"));
      return;
    }

    const today = new Date();
    let age = today.getFullYear() - birth.getFullYear();
    const m = today.getMonth() - birth.getMonth();
    if (m < 0 || (m === 0 && today.getDate() < birth.getDate())) age--;

    if (age < 18) {
      showAgeError(t("register.toast.age_under_18"));
      return;
    }

    hideAgeError();

    if (!nick) {
      toast(t("register.toast.nick_required"));
      return;
    }

    if (!App.user?.geo?.lat || !App.user?.geo?.lng) {
      toast(t("register.toast.location_required"));
      return;
    }

    App.user.city = city;
    App.user.age = age;
    App.user.dob = dob;
    App.user.nick = nick;
  } else {
    const company = $("regCompany")?.value?.trim();
    const category = $("regCategory")?.value;
    const city = normalizeCity($("regCityPartner")?.value);
    dob = null;

    if (!company || !city) {
      toast(t("register.toast.partner_required"));
      return;
    }

    App.partner.company = company;
    App.partner.category = category || "inne";
    App.partner.city = city;
    App.partner.about = $("regOrgAbout")?.value?.trim() || "";
  }

  try {
    const data = await apiFetch("/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email,
        password: pass,
        dob,
        role: App.role === "partner" ? "partner" : "user",
        accept_terms: true,
        accept_privacy: true,
      }),
    });

    if (!data?.success || !data?.data?.id) {
      toast(data?.error?.message || t("register.toast.create_error"));
      return;
    }

    const loginData = await apiFetch("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password: pass, expected_role: App.role === "partner" ? "partner" : "user" }),
    });

    if (!loginData?.success || !loginData?.data?.access_token) {
      toast(t("register.toast.auto_login_error"));
      go("S1_LOGIN");
      return;
    }

    localStorage.setItem("usly_token", loginData.data.access_token);

    const me = await apiFetch("/auth/me");
    App.currentUserId = me?.id ?? me?.data?.id ?? null;
    App.currentRevenueCatAppUserId =
      me?.data?.revenuecat_app_user_id ?? me?.revenuecat_app_user_id ?? null;
    App.role = (me?.data?.role || me?.role) === "partner" ? "partner" : "user";
    App.isLoggedIn = true;

    if (App.role === "user") {
      apiFetch("/users/me").then((profile) => {
        if (profile?.success && profile?.data) {
          App.user.nick = profile.data.nick || App.user.nick;
          App.user.city = profile.data.miasto || App.user.city;
          App.user.bio = profile.data.bio || "";
          const backendInterests = Array.isArray(profile.data.zainteresowania) ? profile.data.zainteresowania : [];
          App.user.interests = backendInterests;
          App.user.trainerInterests = Array.isArray(profile.data.trainer_interests) ? profile.data.trainer_interests : [];
          try { localStorage.setItem("usly_user_interests", JSON.stringify(backendInterests)); } catch(_) {}
          App.user.plan = profile.data.plan || App.user.plan;
          App.user.avatarUrl = profile.data.avatar_url || App.user.avatarUrl || "";
          try { localStorage.setItem(USLY_STORAGE_KEYS.userPlan, App.user.plan); } catch (_) {}
        }
      }).catch((err) => console.error("post-register load user profile failed", err));
    } else {
      await loadPartnerProfile();
      await loadPartnerEvents();
    }

    $("appRoot")?.classList.add("isLoggedIn");
    updateTabbars();

    applyI18n();

    toast(t("register.toast.created_logged_in"));
      if (App.role === "user") {
        if ($("setupNick")) $("setupNick").value = App.user.nick || "";
        if ($("setupCity")) $("setupCity").value = App.user.city || "";
        if ($("setupBio")) $("setupBio").value = App.user.bio || "";
        if ($("setupPrefAgeFrom")) $("setupPrefAgeFrom").value = String(App.user.prefAgeFrom);
        if ($("setupPrefAgeTo")) $("setupPrefAgeTo").value = String(App.user.prefAgeTo);
        safeSetText("bioCount", String(($("setupBio")?.value || "").length));
        safeSetText("setupAgeDisplay", t("settings.ageLabel", { age: App.user.age || "—" }));
        renderInterestChips("interestChips");
        refreshInterestUi();
        App.planScreenMode = "onboarding";
        go("S11_PLANS");
      } else {
        if ($("setupOrgCity")) $("setupOrgCity").value = App.partner.city || "";
        if ($("setupOrgCategory")) $("setupOrgCategory").value = App.partner.category || "inne";
        if ($("setupOrgAbout")) $("setupOrgAbout").value = App.partner.about || "";
        safeSetText("setupOrgAboutCount", String(($("setupOrgAbout")?.value || "").length));
        safeSetText("setupPartnerCompanyName", App.partner.company || t("partnerSetup.title"));
        App.planScreenMode = "onboarding";
        go("S11_PLANS");
        setTimeout(updateOrgLogoFallback, 0);
      }
  } catch (err) {
    toast(err?.userMessage || t("register.toast.create_error"));
  }
}

/* ------------------------- Plans -------------------------- */

const PLAN_BASE_PRICES = {
  user: {
    plus: 29,
    premium: 49,
    vip: 89,
  },
  partner: {
    pro: 129,
    premium: 259,
  },
};

function formatPlanPriceAmount(amount) {
  const rounded = Math.max(0, Math.round(Number(amount) || 0));
  return App.lang === "en" ? `${rounded} PLN / month` : `${rounded} zł / miesiąc`;
}

function clearPlanPromoPrices(role) {
  const normalizedRole = role === "partner" ? "partner" : "user";
  const scopeSelector = normalizedRole === "partner" ? "#plansPartnerOnly" : "#plansUserOnly";
  document.querySelectorAll(`#S11_PLANS ${scopeSelector} .planPromoPrice`).forEach((el) => {
    const baseLabel = el.dataset.basePriceLabel || "";
    if (baseLabel) {
      const pill = document.createElement("div");
      pill.className = "planPill";
      pill.textContent = baseLabel;
      el.replaceWith(pill);
    } else {
      el.remove();
    }
  });
}

function refreshPlanPromoPrices(role) {
  const normalizedRole = role === "partner" ? "partner" : "user";
  clearPlanPromoPrices(normalizedRole);

  const promo = App.activePromoCode;
  if (!promo || promo.role !== normalizedRole || promo.benefit_type !== "discount_percent") return;

  const discount = Number(promo.benefit_value || 0);
  if (!discount || discount <= 0 || discount >= 100) return;

  const scopeSelector = normalizedRole === "partner" ? "#plansPartnerOnly" : "#plansUserOnly";
  const prices = PLAN_BASE_PRICES[normalizedRole] || {};

  document.querySelectorAll(`#S11_PLANS ${scopeSelector} .card[data-plan]`).forEach((card) => {
    const plan = String(card.dataset.plan || "").toLowerCase();
    const basePrice = prices[plan];
    const pill = card.querySelector(".planPill");
    if (!pill || !basePrice) return;

    const finalPrice = basePrice * (100 - discount) / 100;
    const months = promo.benefit_duration_months || "—";
    const info = document.createElement("div");
    info.className = "planPromoPrice";
    info.dataset.basePriceLabel = pill.textContent || formatPlanPriceAmount(basePrice);
    info.innerHTML = `
      <div class="planPromoOld">${formatPlanPriceAmount(basePrice)}</div>
      <div class="planPromoNew">${formatPlanPriceAmount(finalPrice)}</div>
      <div class="planPromoMeta">${t("plans.promo.discount", { value: discount, months })}</div>
    `;
    pill.replaceWith(info);
  });
}

function refreshUserPlanCardsUi() {
  const current = String(App.user?.plan || "free").toLowerCase();
  const isOnboarding = App.planScreenMode === "onboarding";

  document.querySelectorAll('#S11_PLANS #plansUserOnly .card[data-plan]').forEach(card => {
    const plan = String(card.dataset.plan || "").toLowerCase();
    const btn = card.querySelector('button.btn.secondary');

    if (!isOnboarding) {
      card.classList.toggle("is-current", plan === current);

      if (btn) {
        btn.textContent = plan === current ? t("plans.current", "Aktualny plan") : t("plans.choose", "Wybierz");
      }
    } else {
      card.classList.remove("is-current");
    }
  });

  safeSetText("settingsProfilePlanPill", current.toUpperCase());
  safeSetText("settingsProfilePlanPillSecondary", current.toUpperCase());
  refreshPlanPromoPrices("user");

  if (isOnboarding && App.currentView === "S11_PLANS") {
    applyPlanScreenMode();
  }
}


async function applyPlanPromoCode(role) {
  const normalizedRole = role === "partner" ? "partner" : "user";
  const inputId = normalizedRole === "partner" ? "partnerPromoCodeInput" : "userPromoCodeInput";
  const statusId = normalizedRole === "partner" ? "partnerPromoCodeStatus" : "userPromoCodeStatus";
  const input = $(inputId);
  const statusEl = $(statusId);
  const code = String(input?.value || "").trim().toUpperCase();

  if (statusEl) statusEl.textContent = "";

  if (!code) {
    toast(t("plans.promo.invalid"));
    return;
  }

  try {
    const res = await apiFetch(`/promo-campaigns/validate/${encodeURIComponent(code)}`);
    const promo = res?.data || {};

    if (promo.target_role && promo.target_role !== "both" && promo.target_role !== normalizedRole) {
      toast(t("plans.promo.invalid"));
      if (statusEl) statusEl.textContent = t("plans.promo.invalid");
      return;
    }

    const value = promo.benefit_value ?? "—";
    const months = promo.benefit_duration_months ?? "—";
    const label = promo.benefit_type === "discount_percent"
      ? t("plans.promo.discount", { value, months })
      : t("plans.promo.applied");

    App.activePromoCode = {
      code: promo.code || code,
      role: normalizedRole,
      benefit_type: promo.benefit_type || null,
      benefit_value: promo.benefit_value ?? null,
      benefit_duration_months: promo.benefit_duration_months ?? null,
      reward_type: promo.reward_type || null,
      reward_value: promo.reward_value ?? null,
    };

    let redemption = null;
    if (App.isLoggedIn && App.role === normalizedRole) {
      redemption = await apiFetch("/promo-campaigns/redeem", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code: promo.code || code, platform: "web" }),
      });
      App.activePromoCode.redemption_id = redemption?.data?.id || null;
      App.activePromoCode.redemption_status = redemption?.data?.status || "reserved";
      App.activePromoCode.already_redeemed = !!redemption?.data?.already_redeemed;
    }

    refreshPlanPromoPrices(normalizedRole);
    if (statusEl) statusEl.textContent = `${t("plans.promo.applied")}: ${label}`;
    toast(`${t("plans.promo.applied")}: ${promo.code || code}`);
  } catch (err) {
    App.activePromoCode = null;
    clearPlanPromoPrices(normalizedRole);

    const rawPromoError = String(
      err?.data?.detail || err?.data?.error?.code || err?.code || err?.detail || err?.message || err?.userMessage || ""
    );

    let promoMessage = t("plans.promo.invalid");
    if (rawPromoError.includes("PROMO_CODE_EXPIRED")) {
      promoMessage = t("plans.promo.expired");
    } else if (rawPromoError.includes("PROMO_CODE_LIMIT_REACHED")) {
      promoMessage = t("plans.promo.limitReached");
    } else if (rawPromoError.includes("PROMO_CODE_NOT_FOR_THIS_ROLE")) {
      promoMessage = t("plans.promo.wrongRole");
    } else if (
      rawPromoError.includes("PROMO_CODE_INACTIVE") ||
      rawPromoError.includes("PROMO_CODE_NOT_FOUND") ||
      rawPromoError.includes("server") ||
      rawPromoError.includes("serwera")
    ) {
      promoMessage = t("plans.promo.notActive");
    }

    if (statusEl) statusEl.textContent = promoMessage;
    toast(promoMessage);
  }
}


async function refreshPlanAfterStorePurchase(role) {
  const normalizedRole = String(role || App.role || "").toLowerCase();

  if (normalizedRole === "partner") {
    await loadPartnerProfile();
    try { localStorage.setItem(USLY_STORAGE_KEYS.partnerPlan, App.partner.plan || "free"); } catch (_) {}
    refreshPlanPromoPrices("partner");
    renderAll();
    return;
  }

  const profile = await apiFetch("/users/me");
  if (profile?.success && profile?.data) {
    App.user.plan = profile.data.plan || App.user.plan || "free";
    try { localStorage.setItem(USLY_STORAGE_KEYS.userPlan, App.user.plan); } catch (_) {}
    safeSetText("planPillSetup", String(App.user.plan || "free").toUpperCase());
    refreshUserPlanCardsUi();
    renderAll();
  }
}

function goToProfileSetupAfterPlan() {
  if (App.role === "partner") {
    if ($("setupOrgCity")) $("setupOrgCity").value = App.partner.city || "";
    if ($("setupOrgCategory")) $("setupOrgCategory").value = App.partner.category || "inne";
    if ($("setupOrgAbout")) $("setupOrgAbout").value = App.partner.about || "";
    safeSetText("setupOrgAboutCount", String(($("setupOrgAbout")?.value || "").length));
    safeSetText("setupPartnerCompanyName", App.partner.company || t("partnerSetup.title"));
    go("S3B_PARTNER_SETUP");
    setTimeout(updateOrgLogoFallback, 0);
    return;
  }

  safeSetText("planPillSetup", String(App.user.plan || "free").toUpperCase());

  if ($("setupNick")) $("setupNick").value = App.user.nick || "";
  if ($("setupCity")) $("setupCity").value = App.user.city || "";
  if ($("setupBio")) $("setupBio").value = App.user.bio || "";
  if ($("setupPrefAgeFrom")) $("setupPrefAgeFrom").value = String(App.user.prefAgeFrom);
  if ($("setupPrefAgeTo")) $("setupPrefAgeTo").value = String(App.user.prefAgeTo);
  safeSetText("bioCount", String(($("setupBio")?.value || "").length));
  safeSetText("setupAgeDisplay", t("settings.ageLabel", { age: App.user.age || "—" }));
  renderInterestChips("interestChips");
  refreshInterestUi();
  go("S3_PROFILE_SETUP");
}

async function chooseUserPlan(plan) {
  const normalizedPlan = String(plan || "").toLowerCase();
  if (normalizedPlan === "free") {
    await setUserPlan("free", true);
    goToProfileSetupAfterPlan();
    return;
  }

  try {
    await window.USLYBilling.purchasePlan({ role: "user", plan: normalizedPlan });
    toast(t("plans.payment.success", "Plan został aktywowany."));
    await refreshPlanAfterStorePurchase("user");
    goToProfileSetupAfterPlan();
  } catch (err) {
    const key = window.USLYBilling?.getBillingErrorMessageKey?.(err) || "plans.payment.failed";
    toast(t(key, "Nie udało się zakończyć płatności. Spróbuj ponownie."));
  }
}

async function choosePartnerPlan(plan) {
  const normalizedPlan = String(plan || "").toLowerCase();
  if (normalizedPlan === "free") {
    await setPartnerPlan("free", true);
    goToProfileSetupAfterPlan();
    return;
  }

  if (normalizedPlan === "enterprise") {
    return contactEnterprisePlan();
  }

  try {
    await window.USLYBilling.purchasePlan({ role: "partner", plan: normalizedPlan });
    toast(t("plans.payment.success", "Plan został aktywowany."));
    await refreshPlanAfterStorePurchase("partner");
    goToProfileSetupAfterPlan();
  } catch (err) {
    const key = window.USLYBilling?.getBillingErrorMessageKey?.(err) || "plans.payment.failed";
    toast(t(key, "Nie udało się zakończyć płatności. Spróbuj ponownie."));
  }
}

async function restoreStorePurchases(role) {
  const normalizedRole = String(role || App.role || "").toLowerCase() === "partner" ? "partner" : "user";

  try {
    if (!window.USLYBilling?.restorePurchases) {
      throw new Error("STORE_BILLING_RESTORE_UNAVAILABLE");
    }

    toast(t("plans.restore.checking", "Sprawdzamy aktywne subskrypcje..."));
    const result = await window.USLYBilling.restorePurchases(normalizedRole);
    await refreshPlanAfterStorePurchase(normalizedRole);

    const activePurchases = result?.customerInfo?.activeSubscriptions || [];
    if (Array.isArray(activePurchases) && activePurchases.length === 0) {
      toast(t("plans.restore.notFound", "Nie znaleziono aktywnych zakupów dla tego konta."));
      return;
    }

    toast(t("plans.restore.success", "Subskrypcja została odświeżona."));
  } catch (err) {
    const key = window.USLYBilling?.getBillingErrorMessageKey?.(err) || "plans.restore.failed";
    toast(t(key, "Nie udało się przywrócić zakupów. Spróbuj ponownie."));
  }
}

async function setUserPlan(plan, silent = false) {
  const allowed = ["free", "plus", "premium", "vip"];
  if (!allowed.includes(plan)) return;

  const prevPlan = App.user.plan;
  App.user.plan = plan;
  try { localStorage.setItem(USLY_STORAGE_KEYS.userPlan, plan); } catch(_) {}

  const btnIds = [
    "uplan_free", "uplan_plus", "uplan_premium", "uplan_vip",
    "uplan_free_set", "uplan_plus_set", "uplan_premium_set", "uplan_vip_set",
  ];
  btnIds.forEach(id => {
    const b = $(id);
    if (!b) return;
    const isOn = b.dataset.plan === plan;
    b.classList.toggle("on", isOn);
    b.classList.toggle("active", isOn);
  });

  safeSetText("planPillSetup", plan.toUpperCase());
  refreshUserPlanCardsUi();
  renderAll();

  if (App.isLoggedIn && App.role === "user") {
    try {
      const data = await apiFetch("/users/me", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          nick: App.user.nick || "",
          miasto: App.user.city || "",
          bio: App.user.bio || "",
          zainteresowania: Array.isArray(App.user.interests) ? App.user.interests : [],
          age_min: App.user.prefAgeFrom,
          age_max: App.user.prefAgeTo,
          plan: plan,
        }),
      });

      if (!data?.success || !data?.data) {
        throw new Error(data?.error?.message || t("plans.toast.saveFailed"));
      }

      App.user.plan = data.data.plan || prevPlan || "free";
      try { localStorage.setItem(USLY_STORAGE_KEYS.userPlan, App.user.plan); } catch(_) {}
      safeSetText("planPillSetup", String(App.user.plan || "free").toUpperCase());
      refreshUserPlanCardsUi();
      renderAll();
      if (!silent) toast(t("plans.toast.selected", { plan: App.user.plan.toUpperCase() }));
      return;
    } catch (err) {
      App.user.plan = prevPlan;
      try { localStorage.setItem(USLY_STORAGE_KEYS.userPlan, prevPlan); } catch(_) {}
      btnIds.forEach(id => {
        const b = $(id);
        if (!b) return;
        const isOn = b.dataset.plan === prevPlan;
        b.classList.toggle("on", isOn);
        b.classList.toggle("active", isOn);
      });
      safeSetText("planPillSetup", prevPlan.toUpperCase());
      refreshUserPlanCardsUi();
      renderAll();
      toast(err?.userMessage || err?.message || t("plans.toast.saveFailed"));
      return;
    }
  }

  if (!silent) toast(t("plans.toast.selected", { plan: plan.toUpperCase() }));
}

async function setPartnerPlan(plan, silent = false) {
  const allowed = ["free", "pro", "premium", "enterprise"];
  if (!allowed.includes(plan)) return;

  const prevPlan = App.partner.plan || "free";
  App.partner.plan = plan;
  try { localStorage.setItem(USLY_STORAGE_KEYS.partnerPlan, plan); } catch(_) {}

  const btnIds = [
    "pplan_free", "pplan_pro", "pplan_premium", "pplan_enterprise",
    "pplan_free_set", "pplan_pro_set", "pplan_premium_set", "pplan_enterprise_set",
  ];
  btnIds.forEach(id => {
    const b = $(id);
    if (!b) return;
    const isOn = b.dataset.plan === plan;
    b.classList.toggle("on", isOn);
    b.classList.toggle("active", isOn);
  });

  document.querySelectorAll('#S11_PLANS #plansPartnerOnly .card[data-plan]').forEach(card => {
    const isCurrent = String(card.dataset.plan || "").toLowerCase() === plan;
    const isOnboarding = App.planScreenMode === "onboarding";
    card.classList.toggle("is-current", !isOnboarding && isCurrent);
    const btn = card.querySelector(".btn");
    if (btn && !isOnboarding) {
      const cardPlan = String(card.dataset.plan || "").toLowerCase();
      btn.textContent = cardPlan === "enterprise" ? t("plans.contact_us", "Napisz do nas") : (isCurrent ? t("plans.current", "Aktualny plan") : t("plans.choose", "Wybierz"));
    }
  });

  if (App.planScreenMode === "onboarding" && App.currentView === "S11_PLANS") {
    applyPlanScreenMode();
  }

  document.querySelectorAll("#partnerPlanPill").forEach((el) => {
    el.textContent = plan.toUpperCase();
  });
  refreshPlanPromoPrices("partner");

  const isAuthSetupFlow = ["S1_LOGIN", "S2_REGISTER", "S3_PROFILE_SETUP", "S3B_PARTNER_SETUP"].includes(App.currentView);

  if (!silent && App.isLoggedIn && App.role === "partner" && !isAuthSetupFlow) {
    try {
      const res = await apiFetch("/partners/me", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ plan }),
      });

      if (!res?.success || !res?.data) {
        App.partner.plan = prevPlan;
        try { localStorage.setItem(USLY_STORAGE_KEYS.partnerPlan, prevPlan); } catch(_) {}
        renderAll();
        toast(res?.error?.message || t("plans.toast.partnerSaveFailed"));
        return;
      }

      App.partner.plan = res.data.plan || plan;
      try { localStorage.setItem(USLY_STORAGE_KEYS.partnerPlan, App.partner.plan); } catch(_) {}
      document.querySelectorAll("#partnerPlanPill").forEach((el) => {
        el.textContent = String(App.partner.plan).toUpperCase();
      });
      toast(t("plans.toast.selected", { plan: String(App.partner.plan).toUpperCase() }));
    } catch (err) {
      App.partner.plan = prevPlan;
      try { localStorage.setItem(USLY_STORAGE_KEYS.partnerPlan, prevPlan); } catch(_) {}
      renderAll();
      toast(err?.userMessage || t("plans.toast.partnerSaveFailed"));
      return;
    }
  } else if (!silent) {
    toast(t("plans.toast.selected", { plan: String(plan).toUpperCase() }));
  }

  renderAll();
}


async function submitEnterpriseContact() {
  const btn = $("enterpriseContactSubmitBtn");
  const selectedNeeds = Array.from(document.querySelectorAll(".enterpriseNeedOption:checked"))
    .map((item) => item.value)
    .filter(Boolean);

  const payload = {
    company: $("enterpriseContactCompany")?.value?.trim() || "",
    city: $("enterpriseContactCity")?.value?.trim() || "",
    contact: $("enterpriseContactContact")?.value?.trim() || "",
    locations: selectedNeeds.join(", "),
    needs: $("enterpriseContactNeeds")?.value?.trim() || "",
    extra: "",
    user_id: App.user?.id || App.partner?.id || null,
    account_email: App.partner?.email || App.user?.email || "",
  };

  if (!payload.contact) {
    toast(t("enterprise.toast.contactRequired"));
    return;
  }

  if (btn) {
    btn.disabled = true;
    btn.textContent = t("enterprise.toast.sending");
  }

  try {
    const data = await apiFetch("/enterprise/contact", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!data?.success) {
      toast(data?.error?.message || t("enterprise.toast.failed"));
      return;
    }

    toast(t("enterprise.toast.sent"));
    closeModal();
  } catch (err) {
    toast(err?.userMessage || t("enterprise.toast.failed"));
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = t("enterprise.submit");
    }
  }
}

function contactEnterprisePlan() {
  openModal(t("enterprise.modal.title"), `
    <div class="tStrong">${t("enterprise.modal.heading")}</div>
    <div class="sectionSub mt10">${t("enterprise.modal.subtitle")}</div>

    <label class="mt12">${t("enterprise.company.label")}</label>
    <input id="enterpriseContactCompany" type="text" placeholder="${t("enterprise.company.placeholder")}" />

    <label class="mt12">${t("enterprise.city.label")}</label>
    <input id="enterpriseContactCity" type="text" placeholder="${t("enterprise.city.placeholder")}" />

    <label class="mt12">${t("enterprise.contact.label")}</label>
    <input id="enterpriseContactContact" type="text" placeholder="${t("enterprise.contact.placeholder")}" />

    <label class="mt12">${t("enterprise.interests.label")}</label>
    <div class="mt8" style="display:grid;gap:8px">
      <label style="display:flex;align-items:center;gap:9px;padding:10px 12px;border:1px solid rgba(255,255,255,.10);border-radius:999px;background:linear-gradient(135deg,rgba(255,255,255,.07),rgba(255,255,255,.025));font-weight:700;line-height:1.2;box-shadow:inset 0 1px 0 rgba(255,255,255,.06)"><input class="enterpriseNeedOption" type="checkbox" value="${t("enterprise.need.visibility")}" style="width:18px;height:18px;flex:0 0 auto;margin:0" /><span>${t("enterprise.need.visibility")}</span></label>
      <label style="display:flex;align-items:center;gap:9px;padding:10px 12px;border:1px solid rgba(255,255,255,.10);border-radius:999px;background:linear-gradient(135deg,rgba(255,255,255,.07),rgba(255,255,255,.025));font-weight:700;line-height:1.2;box-shadow:inset 0 1px 0 rgba(255,255,255,.06)"><input class="enterpriseNeedOption" type="checkbox" value="${t("enterprise.need.locations")}" style="width:18px;height:18px;flex:0 0 auto;margin:0" /><span>${t("enterprise.need.locations")}</span></label>
      <label style="display:flex;align-items:center;gap:9px;padding:10px 12px;border:1px solid rgba(255,255,255,.10);border-radius:999px;background:linear-gradient(135deg,rgba(255,255,255,.07),rgba(255,255,255,.025));font-weight:700;line-height:1.2;box-shadow:inset 0 1px 0 rgba(255,255,255,.06)"><input class="enterpriseNeedOption" type="checkbox" value="${t("enterprise.need.campaign")}" style="width:18px;height:18px;flex:0 0 auto;margin:0" /><span>${t("enterprise.need.campaign")}</span></label>
      <label style="display:flex;align-items:center;gap:9px;padding:10px 12px;border:1px solid rgba(255,255,255,.10);border-radius:999px;background:linear-gradient(135deg,rgba(255,255,255,.07),rgba(255,255,255,.025));font-weight:700;line-height:1.2;box-shadow:inset 0 1px 0 rgba(255,255,255,.06)"><input class="enterpriseNeedOption" type="checkbox" value="${t("enterprise.need.long_term")}" style="width:18px;height:18px;flex:0 0 auto;margin:0" /><span>${t("enterprise.need.long_term")}</span></label>
      <label style="display:flex;align-items:center;gap:9px;padding:10px 12px;border:1px solid rgba(255,255,255,.10);border-radius:999px;background:linear-gradient(135deg,rgba(255,255,255,.07),rgba(255,255,255,.025));font-weight:700;line-height:1.2;box-shadow:inset 0 1px 0 rgba(255,255,255,.06)"><input class="enterpriseNeedOption" type="checkbox" value="${t("enterprise.need.network")}" style="width:18px;height:18px;flex:0 0 auto;margin:0" /><span>${t("enterprise.need.network")}</span></label>
      <label style="display:flex;align-items:center;gap:9px;padding:10px 12px;border:1px solid rgba(255,255,255,.10);border-radius:999px;background:linear-gradient(135deg,rgba(255,255,255,.07),rgba(255,255,255,.025));font-weight:700;line-height:1.2;box-shadow:inset 0 1px 0 rgba(255,255,255,.06)"><input class="enterpriseNeedOption" type="checkbox" value="${t("enterprise.need.other")}" style="width:18px;height:18px;flex:0 0 auto;margin:0" /><span>${t("enterprise.need.other")}</span></label>
    </div>

    <label class="mt12">${t("enterprise.message.label")}</label>
    <textarea id="enterpriseContactNeeds" rows="4" placeholder="${t("enterprise.message.placeholder")}"></textarea>

    <button id="enterpriseContactSubmitBtn" class="btn mt16" type="button" onclick="submitEnterpriseContact()">${t("enterprise.submit")}</button>
  `);
}


function getPartnerPlanRules() {
  const plan = String(App.partner?.plan || "free").toLowerCase();

  if (plan === "enterprise") {
    return {
      plan,
      maxActiveEvents: null,
      reportsScope: "full",
      canMessageParticipants: true,
      canBroadcastParticipants: true,
      canFeatureEvents: true,
      isCustom: true,
    };
  }

  if (plan === "premium") {
    return {
      plan,
      maxActiveEvents: null,
      reportsScope: "full",
      canMessageParticipants: true,
      canBroadcastParticipants: true,
      canFeatureEvents: true,
      isCustom: false,
    };
  }

  if (plan === "pro") {
    return {
      plan,
      maxActiveEvents: 5,
      reportsScope: "basic",
      canMessageParticipants: true,
      canBroadcastParticipants: false,
      canFeatureEvents: false,
      isCustom: false,
    };
  }

  return {
    plan: "free",
    maxActiveEvents: 2,
    reportsScope: "basic",
    canMessageParticipants: false,
    canBroadcastParticipants: false,
    canFeatureEvents: false,
    isCustom: false,
  };
}


function getUserInterestLimit() {
  const plan = App.user.plan || "free";

  if (plan === "vip") return null;
  if (plan === "premium") return 20;
  if (plan === "plus") return 10;
  return 5;
}

function canAddMoreInterests(currentCount) {
  const limit = getUserInterestLimit();
  if (limit === null) return true;
  return currentCount < limit;
}

function getUserGroupPlanRules() {
  const plan = App.user.plan || "free";

  if (plan === "vip") {
    return {
      plan,
      canBrowseGroups: true,
      canOpenGroup: true,
      canInviteFriendsToGroup: true,
      maxActiveGroups: null,
    };
  }

  if (plan === "premium") {
    return {
      plan,
      canBrowseGroups: true,
      canOpenGroup: true,
      canInviteFriendsToGroup: true,
      maxActiveGroups: null,
    };
  }

  if (plan === "plus") {
    return {
      plan,
      canBrowseGroups: true,
      canOpenGroup: true,
      canInviteFriendsToGroup: false,
      maxActiveGroups: 3,
    };
  }

  return {
    plan: "free",
    canBrowseGroups: true,
    canOpenGroup: true,
    canInviteFriendsToGroup: false,
    maxActiveGroups: 1,
  };
}

function getUserGroupCreateRules() {
  const plan = App.user.plan || "free";

  if (plan === "vip") {
    return { plan, canCreate: true, createLimit: null };
  }

  if (plan === "premium") {
    return { plan, canCreate: true, createLimit: 3 };
  }

  if (plan === "plus") {
    return { plan, canCreate: true, createLimit: 1 };
  }

  return { plan: "free", canCreate: false, createLimit: 0 };
}

function refreshCreateGroupUi() {
  const btn = $("btnCreateGroup");
  const hint = $("groupCreateHint");
  const rules = getUserGroupCreateRules();

  const createdCount = Array.isArray(App.myGroups) ? App.myGroups.length : 0;
  const limitReached =
    rules.canCreate &&
    rules.createLimit != null &&
    createdCount >= rules.createLimit;

  if (btn) {
    const enabled = rules.canCreate && !limitReached;
    btn.disabled = !enabled;
    btn.style.opacity = enabled ? "1" : "0.65";
    btn.style.cursor = enabled ? "pointer" : "not-allowed";

    if (!rules.canCreate) {
      btn.textContent = t("groups.create.availablePlus");
    } else if (limitReached) {
      btn.textContent = t("groups.create.limitReached");
    } else {
      btn.textContent = t("groups.create.button");
    }
  }

  if (hint) {
    if (!rules.canCreate) {
      hint.textContent = t("groups.create.hintLocked");
    } else if (rules.createLimit == null) {
      hint.textContent = t("groups.create.hintUnlimited", { count: createdCount });
    } else if (limitReached) {
      hint.textContent = t("groups.create.hintReached", { count: createdCount, limit: rules.createLimit });
    } else {
      hint.textContent = t("groups.create.hintLeft", { count: createdCount, limit: rules.createLimit, left: rules.createLimit - createdCount });
    }
  }
}

function openCreateGroupModal() {
  const rules = getUserGroupCreateRules();

  if (!rules.canCreate) {
    toast(t("groups.create.toastLocked"));
    return;
  }

  openModal(t("groups.create.modalTitle"), `
    <label>${t("groups.create.title")}</label>
    <input id="createGroupTitle" type="text" placeholder="${t("groups.create.titlePlaceholder")}" />

    <label class="mt12">${t("groups.create.interest")}</label>
    <div class="hashRow">
      <span class="hashPrefix">#</span>
      <input id="createGroupInterest" type="text" placeholder="${t("groups.create.interestPlaceholder")}" />
    </div>

    <label class="mt12">${t("groups.create.description")}</label>
    <textarea id="createGroupDesc" maxlength="600" placeholder="${t("groups.create.descriptionPlaceholder")}"></textarea>

    <div class="sectionSub mt12">
      ${rules.createLimit == null
        ? t("groups.create.planUnlimited")
        : t("groups.create.planLimited", { limit: rules.createLimit })}
    </div>

    <div class="row mt16">
      <button class="btn" type="button" onclick="submitCreateGroup()">${t("groups.create.submit")}</button>
      <button class="btn secondary" type="button" onclick="closeModal()">${t("groups.create.cancel")}</button>
    </div>
  `);
}

async function submitCreateGroup() {
  const title = $("createGroupTitle")?.value?.trim();
  const interest = normalizeTag($("createGroupInterest")?.value?.trim());
  const description = $("createGroupDesc")?.value?.trim() || "";

  if (!title || title.length < 3) {
    toast(t("groups.create.toastTitle"));
    return;
  }

  if (!interest || interest.length < 2) {
    toast(t("groups.create.toastInterest"));
    return;
  }

  try {
    const data = await apiFetch("/groups", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title,
        description,
        interest_tag: interest,
      }),
    });

    if (!data?.success) {
      toast(data?.error?.message || t("groups.create.toastFailed"));
      return;
    }

    closeModal();
    await Promise.all([loadMyGroups(), loadGroups()]);
    renderGroups();
    toast(t("groups.create.toastSuccess"));
  } catch (err) {
    toast(err?.userMessage || t("groups.create.toastFailed"));
  }
}


/* ------------------------- Groups helpers -------------------------- */
function isUserInGroup(groupId) {
  return App.myGroups.some(g => String(g.id) === String(groupId));
}

function userGroupsCount() {
  return App.myGroups.length;
}

function canJoinMoreGroups() {
  const plan = App.user.plan || "free";

  const limits = {
    free: 1,
    plus: 3,
    premium: null,
    vip: null,
  };

  const limit = Object.prototype.hasOwnProperty.call(limits, plan) ? limits[plan] : 1;

  if (limit === null) return true;

  return userGroupsCount() < limit;
}

function canInviteFriendsToGroup() {
  return getUserGroupPlanRules().canInviteFriendsToGroup;
}

/* ------------------------- Settings -------------------------- */
async function saveSettings() {
  const nick = $("setNick")?.value?.trim() || App.user.nick;
  const bio = $("setBio")?.value?.trim() || "";
  const city = normalizeCity($("setCity")?.value) || App.user.city;

  const ageAny = !!$("setAgeAny")?.checked;
  const fromAge = Number($("setPrefAgeFrom")?.value || App.user.prefAgeFrom);
  const toAge = Number($("setPrefAgeTo")?.value || App.user.prefAgeTo);
  const ageMin = ageAny ? null : Math.min(fromAge, toAge);
  const ageMax = ageAny ? null : Math.max(fromAge, toAge);
  const nearbyRadiusKm = Number($("setNearbyRadiusKm")?.value || App.user.nearbyRadiusKm || 25);

  const payload = {
    nick: nick,
    miasto: city,
    bio: bio,
    zainteresowania: Array.isArray(App.user.interests) ? App.user.interests : [],
    age_min: ageMin,
    age_max: ageMax,
    nearby_radius_km: nearbyRadiusKm,
  };

  const trainerPlan = ["premium", "vip"].includes(String(App.user.plan || "").toLowerCase());
  const trainerInterests = Array.isArray(App.user.trainerInterests) ? App.user.trainerInterests : [];
  if (trainerPlan && trainerInterests.length) {
    payload.trainer_interests = trainerInterests;
  }

  if (App.user?.geo?.lat && App.user?.geo?.lng) {
    payload.location_lat = Number(App.user.geo.lat);
    payload.location_lng = Number(App.user.geo.lng);
  }

  try {
    const data = await apiFetch("/users/me", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!data?.success || !data?.data) {
      toast(data?.error?.message || t("settings.toast.saveFailed"));
      return;
    }

    App.user.nick = data.data.nick || nick;
    App.user.bio = data.data.bio || bio;
    App.user.nearbyRadiusKm = data.data.nearby_radius_km || nearbyRadiusKm;
    App.user.city = data.data.miasto || city;
    App.user.prefAgeFrom = Object.prototype.hasOwnProperty.call(data.data, "age_min") ? data.data.age_min : ageMin;
    App.user.prefAgeTo = Object.prototype.hasOwnProperty.call(data.data, "age_max") ? data.data.age_max : ageMax;
    App.user.interests = Array.isArray(data.data.zainteresowania) ? data.data.zainteresowania : (Array.isArray(App.user.interests) ? App.user.interests : []);
    App.user.trainerInterests = Array.isArray(data.data.trainer_interests) ? data.data.trainer_interests : (Array.isArray(App.user.trainerInterests) ? App.user.trainerInterests : []);

    toast(t("settings.toast.saved"));
    await Promise.allSettled([loadNearbyPeople(), loadEvents(), loadMyGroups(), loadGroups(), renderChatList()]);
    renderAll();
  } catch (err) {
    toast(err?.userMessage || t("settings.toast.saveFailed"));
  }
}

async function savePartnerSettings() {
  const company = $("setOrgCompany")?.value?.trim() || App.partner.company;
  const category = $("setOrgCategory")?.value || App.partner.category;
  const city = normalizeCity($("setOrgCity")?.value) || App.partner.city;
  const about = $("setOrgAbout")?.value?.trim() || "";

  try {
    const data = await apiFetch("/partners/me", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        nazwa: company,
        miasto: city,
        kategoria: category,
        bio: about,
      }),
    });

    if (!data?.success || !data?.data) {
      toast(data?.error?.message || t("partnerSettings.toastSaveFailed"));
      return;
    }

    App.partner.company = data.data.nazwa || company;
    App.partner.category = data.data.kategoria || category;
    App.partner.city = data.data.miasto || city;
    App.partner.about = data.data.bio || about;

    renderAll();
    setTimeout(() => toast(t("partnerSettings.toastSaved")), 80);
  } catch (err) {
    toast(err?.userMessage || t("partnerSettings.toastSaveFailed"));
  }
}

/* ------------------------- Terms / Privacy -------------------------- */
function legalBaseUrl() {
  const host = window.location.hostname;
  const isNative = !!(window.Capacitor && window.Capacitor.isNativePlatform && window.Capacitor.isNativePlatform());
  const isLocalWeb = !isNative && (host === "localhost" || host === "127.0.0.1");
  return isLocalWeb ? window.location.origin : "https://uslyapp.pl";
}

function openTerms() {
  const path = App.lang === "en" ? "/regulamin/en" : "/regulamin";
  window.open(`${legalBaseUrl()}${path}`, "_blank");
}

function openRodo() {
  const path = App.lang === "en" ? "/privacy-policy" : "/polityka-prywatnosci";
  window.open(`${legalBaseUrl()}${path}`, "_blank");
}

async function uploadPartnerLogo(file) {
  if (!file) return;

  const form = new FormData();
  form.append("file", file);

  try {
    const data = await apiFetch("/uploads/logo", {
      method: "POST",
      body: form,
    });

    if (!data?.success || !data?.data?.logo_url) {
      toast(data?.error?.message || t("partnerLogo.toastUploadFailed"));
      return;
    }

    App.partner.logoUrl = data.data.logo_url;
    toast(t("partnerLogo.toastSaved"));
    renderAll();
  } catch (err) {
    toast(err?.userMessage || t("partnerLogo.toastUploadFailed"));
  }
}

function initPartnerLogoUpload() {
  ["setOrgLogo", "setupOrgLogo"].forEach((inputId) => {
    const input = $(inputId);
    if (!input || input.dataset.bound === "1") return;

    input.addEventListener("change", async (e) => {
      const file = e.target?.files?.[0];
      if (!file) return;
      await uploadPartnerLogo(file);
      input.value = "";
    });

    input.dataset.bound = "1";
  });
}

/* ------------------------- Avatar / Photo hooks -------------------------- */
async function uploadUserAvatar(file) {
  if (!file) return;

  const form = new FormData();
  form.append("file", file);

  try {
    const data = await apiFetch("/uploads/avatar", {
      method: "POST",
      body: form,
    });

    if (!data?.success || !data?.data?.avatar_url) {
      toast(data?.error?.message || t("photo.toast.uploadFailed"));
      return;
    }

    App.user.avatarUrl = data.data.avatar_url;
    toast(t("photo.toast.saved"));
    renderAll();
    closeModal();
  } catch (err) {
    toast(err?.userMessage || t("photo.toast.uploadFailed"));
  }
}


async function removeUserAvatar() {
  try {
    const data = await apiFetch("/users/me", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ avatar_url: "" }),
    });

    if (!data?.success) {
      toast(data?.error?.message || t("photo.toast.removeFailed"));
      return;
    }

    App.user.avatarUrl = "";
    toast(t("photo.toast.removed"));
    renderAll();
    closeModal();
  } catch (err) {
    toast(err?.userMessage || t("photo.toast.removeFailed"));
  }
}

async function removePartnerLogo() {
  try {
    const data = await apiFetch("/partners/me", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ logo_url: "" }),
    });

    if (!data?.success) {
      toast(data?.error?.message || t("partnerLogo.toastRemoveFailed"));
      return;
    }

    App.partner.logoUrl = "";
    toast(t("partnerLogo.toastRemoved"));
    renderAll();
  } catch (err) {
    toast(err?.userMessage || t("partnerLogo.toastRemoveFailed"));
  }
}

function openAddPhoto() {
  openModal(t("photo.modalTitle"), `
    <div class="tStrong">${t("photo.heading")}</div>
    <div class="sectionSub mt10">${t("photo.subtitle")}</div>
    <input id="userAvatarFileInput" type="file" accept="image/jpeg,image/png,image/webp" class="mt12" />
    <button id="userAvatarUploadBtn" class="btn mt16" type="button">${t("photo.save")}</button>
  `);

  setTimeout(() => {
    const btn = $("userAvatarUploadBtn");
    const input = $("userAvatarFileInput");
    if (!btn || !input || btn.dataset.bound === "1") return;

    btn.addEventListener("click", async () => {
      const file = input.files?.[0];
      if (!file) {
        toast(t("photo.toast.pickFile"));
        return;
      }
      await uploadUserAvatar(file);
    });

    btn.dataset.bound = "1";
  }, 0);
}

async function generateAiAvatar() {
  const input = $("aiAvatarPrompt");
  const btn = $("aiAvatarGenerateBtn");
  const prompt = input?.value?.trim() || "";

  if (prompt.length < 3) {
    toast(t("avatar.toastDescribe"));
    return;
  }

  if (btn) {
    btn.disabled = true;
    btn.textContent = t("avatar.generating");
  }

  try {
    const data = await apiFetch("/ai/avatar/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt }),
    });

    if (!data?.success || !data?.data?.avatar_url) {
      const detail = data?.error?.detail || data?.error?.message || data?.detail;
      const code = detail?.code || data?.error?.code;

      if (code === "ai_avatar_limit_reached") {
        toast(t("avatar.toastLimitReached"));
      } else {
        toast(data?.error?.message || t("avatar.toastFailed"));
      }
      return;
    }

    App.user.avatarUrl = data.data.avatar_url;
    const remaining = Number(data.data.remaining ?? 0);
    toast(remaining > 0 ? t("avatar.toastReadyRemaining", { remaining }) : t("avatar.toastReady"));
    renderAll();
    closeModal();
  } catch (err) {
    toast(err?.userMessage || t("avatar.toastFailed"));
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = t("avatar.generate");
    }
  }
}

async function refreshAiAvatarStatus() {
  const box = $("aiAvatarStatusBox");
  const btn = $("aiAvatarGenerateBtn");
  if (box) box.textContent = t("avatar.statusChecking");

  try {
    const data = await apiFetch("/ai/avatar/status");
    if (!data?.success || !data?.data) {
      if (box) box.textContent = t("avatar.statusFailed");
      return;
    }

    const status = data.data;
    const plan = String(status.plan || "free").toUpperCase();
    const used = Number(status.used || 0);
    const limit = Number(status.limit || 0);
    const remaining = Number(status.remaining || 0);

    if (box) {
      box.innerHTML = remaining > 0
        ? t("avatar.statusLine", { plan, used, limit, remaining })
        : t("avatar.statusLimitLine", { plan, used, limit, remaining });
    }

    if (btn) {
      btn.disabled = remaining <= 0;
      btn.textContent = remaining > 0 ? t("avatar.generate") : t("avatar.limitReached");
    }
  } catch (err) {
    if (box) box.textContent = t("avatar.statusFailed");
  }
}

function openAvatarAI() {
  openModal(t("avatar.modalTitle"), `
    <div class="tStrong">${t("avatar.heading")}</div>
    <div class="sectionSub mt10">${t("avatar.subtitle")}</div>
    <div id="aiAvatarStatusBox" class="sectionSub mt10">${t("avatar.statusChecking")}</div>
    <label class="mt12">${t("avatar.styleLabel")}</label>
    <input id="aiAvatarPrompt" type="text" maxlength="240" placeholder="${t("avatar.placeholder")}" />
    <button id="aiAvatarGenerateBtn" class="btn mt16" type="button" onclick="generateAiAvatar()">${t("avatar.generate")}</button>
  `);
  setTimeout(() => refreshAiAvatarStatus(), 0);
}

function updateOrgLogoFallback() {
  const el = $("setupOrgLogoPreview");
  if (!el) return;

  const hasImg = el.querySelector("img");
  if (hasImg) return;

  const name = App.partner?.company || "U";
  const initial = name.trim().charAt(0).toUpperCase();

  el.textContent = initial;
}
async function finishPartnerSetup() {
  const company = App.partner.company || $("regCompany")?.value?.trim() || "Twoje miejsce";
  const category = $("setupOrgCategory")?.value || App.partner.category || "inne";
  const city = normalizeCity($("setupOrgCity")?.value) || App.partner.city;
  const about = $("setupOrgAbout")?.value?.trim() || "";

  if (!city) {
    toast(t("partnerSetup.cityRequired"));
    return;
  }

  try {
    const data = await apiFetch("/partners/me", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        nazwa: company,
        miasto: city,
        kategoria: category,
        bio: about,
      }),
    });

    if (!data?.success || !data?.data) {
      toast(data?.error?.message || t("partnerSetup.profileSaveFailed"));
      return;
    }

    App.partner.company = data.data.nazwa || company;
    App.partner.city = data.data.miasto || city;
    App.partner.category = data.data.kategoria || category;
    App.partner.about = data.data.bio || about;

    await Promise.all([loadPartnerProfile(), loadPartnerEvents()]);
    toast(t("partnerSetup.profileSaved"));
    go("S9_PARTNER");
  } catch (err) {
    toast(err?.userMessage || t("partnerSetup.profileSaveFailed"));
  }
}

/* ------------------------- Profile Setup -------------------------- */
async function finishProfileSetup() {
  if (App.role === "partner") {
    return finishPartnerSetup();
  }

  const nick = $("setupNick")?.value?.trim() || App.user.nick;
  const city = normalizeCity($("setupCity")?.value) || App.user.city;
  const bio = $("setupBio")?.value?.trim() || "";
  const nearbyRadiusKm = Number($("setupNearbyRadiusKm")?.value || App.user.nearbyRadiusKm || 25);

  const ageAny = !!$("setupAgeAny")?.checked;
  const f = Number($("setupPrefAgeFrom")?.value || App.user.prefAgeFrom);
  const toAge = Number($("setupPrefAgeTo")?.value || App.user.prefAgeTo);
  const ageMin = ageAny ? null : Math.min(f, toAge);
  const ageMax = ageAny ? null : Math.max(f, toAge);

  const payload = {
    nick: nick,
    miasto: city,
    bio: bio,
    zainteresowania: Array.isArray(App.user.interests) ? App.user.interests : [],
    age_min: ageMin,
    age_max: ageMax,
    nearby_radius_km: nearbyRadiusKm,
  };

  const trainerPlan = ["premium", "vip"].includes(String(App.user.plan || "").toLowerCase());
  const trainerInterests = Array.isArray(App.user.trainerInterests) ? App.user.trainerInterests : [];
  if (trainerPlan && trainerInterests.length) {
    payload.trainer_interests = trainerInterests;
  }

  if (App.user?.geo?.lat && App.user?.geo?.lng) {
    payload.location_lat = Number(App.user.geo.lat);
    payload.location_lng = Number(App.user.geo.lng);
  }

  try {
    const data = await apiFetch("/users/me", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!data?.success || !data?.data) {
      toast(data?.error?.message || t("profileSetup.profileSaveFailed"));
      return;
    }

    App.user.nick = data.data.nick || nick;
    App.user.city = data.data.miasto || city;
    App.user.bio = data.data.bio || bio;
    App.user.nearbyRadiusKm = data.data.nearby_radius_km || nearbyRadiusKm;
    App.user.prefAgeFrom = Object.prototype.hasOwnProperty.call(data.data, "age_min") ? data.data.age_min : ageMin;
    App.user.prefAgeTo = Object.prototype.hasOwnProperty.call(data.data, "age_max") ? data.data.age_max : ageMax;
    App.user.interests = Array.isArray(data.data.zainteresowania) ? data.data.zainteresowania : (Array.isArray(App.user.interests) ? App.user.interests : []);
    App.user.trainerInterests = Array.isArray(data.data.trainer_interests) ? data.data.trainer_interests : (Array.isArray(App.user.trainerInterests) ? App.user.trainerInterests : []);

    await Promise.all([loadNearbyPeople(), loadEvents(), loadMyGroups(), loadGroups(), renderChatList()]);

    toast(t("profileSetup.profileSaved"));
    go("S4_NEARBY");
  } catch (err) {
    toast(err?.userMessage || t("profileSetup.profileSaveFailed"));
  }
}

/* ------------------------- Nearby / Map -------------------------- */
function getNearbyPeopleForView() {
  const q = ($("nearbyPeopleSearch")?.value || "").trim().toLowerCase();
  return App.people
    .filter(p => String(p.id) !== String(App.currentUserId))
    .map(p => ({ person: p, score: commonInterests(p).length }))
    .filter(({ person, score }) => {
      const matchesSearch = !q || person.nick.toLowerCase().includes(q);
      return matchesSearch && score > 0;
    })
    .sort((a, b) => b.score - a.score)
    .map(({ person }) => person)
    .slice(0, 12);
}

function openMapMarker(type, index) {
  if (type === "person") {
    const person = getNearbyPeopleForView()[index];
    if (!person) return;
    App.selectedPersonId = person.id;
    openPerson(person.id);
  } else {
    const ev = App.events[index];
    if (!ev) return;
    openEvent(ev.id);
  }
}


function resolvePersonById(userId) {
  if (!userId) return null;

  const pid = String(userId);

  const fromPeople = (App.people || []).find(p => String(p.id) === pid);
  if (fromPeople) return fromPeople;

  const fromChats = (App.chats || []).find(c => String(c.with?.id) === pid);
  if (fromChats?.with) {
    return {
      id: String(fromChats.with.id),
      nick: fromChats.with.nick || t("friends.defaultUser", { id: pid }),
      role: fromChats.with.role || "user",
      company: fromChats.with.company || "",
      city: fromChats.with.city || "",
      category: fromChats.with.category || "",
      age: fromChats.with.age || 0,
      emoji: fromChats.with.emoji || "",
      interests: Array.isArray(fromChats.with.interests) ? fromChats.with.interests : [],
      bio: fromChats.with.bio || "",
      avatarUrl: fromChats.with.avatarUrl || "",
      logoUrl: fromChats.with.logoUrl || fromChats.with.avatarUrl || "",
    };
  }

  const friendCards = Array.from(document.querySelectorAll('#profileFriendsList [onclick*="openChatParticipantProfile"]'));
  const friendCard = friendCards.find(el => String(el.getAttribute('onclick') || '').includes(`'${pid}'`));
  if (friendCard) {
    const title = friendCard.querySelector('.sectionTitle')?.textContent?.trim() || t("friends.defaultUser", { id: pid });
    const sub = friendCard.querySelector('.sectionSub')?.textContent?.trim() || "";
    return {
      id: pid,
      nick: title,
      city: sub === "Znajomy w USLY" ? "" : sub,
      age: 0,
      emoji: "",
      interests: [],
      bio: "",
      avatarUrl: "",
    };
  }

  const groupPeople = window._lastGroupPeople || { members: [], invited: [] };
  const fromGroupMembers = (groupPeople.members || []).find(p => String(p.id) === pid);
  if (fromGroupMembers) {
    return {
      id: pid,
      nick: fromGroupMembers.nick || t("friends.defaultUser", { id: pid }),
      city: fromGroupMembers.city || "",
      age: 0,
      emoji: "",
      interests: [],
      bio: "",
      avatarUrl: fromGroupMembers.avatar_url || "",
    };
  }

  const fromGroupInvited = (groupPeople.invited || []).find(p => String(p.id) === pid);
  if (fromGroupInvited) {
    return {
      id: pid,
      nick: fromGroupInvited.nick || t("friends.defaultUser", { id: pid }),
      city: fromGroupInvited.city || "",
      age: 0,
      emoji: "",
      interests: [],
      bio: "",
      avatarUrl: fromGroupInvited.avatar_url || "",
    };
  }

  return null;
}


/* ------------------------- Person Profile -------------------------- */

function getEventTagIcon(tag = "") {
  const t = normalizeTag(tag).toLowerCase();

  if (["joga", "fitness", "sport", "bieganie", "medytacja"].includes(t)) return "🧘";
  if (["muzyka", "koncerty", "koncert", "taniec"].includes(t)) return "🎵";
  if (["kawa", "restauracje", "jedzenie", "gastro"].includes(t)) return "☕";
  if (["kino", "film", "teatr", "sztuka"].includes(t)) return "🎭";
  if (["książki", "czytanie", "literatura"].includes(t)) return "📚";
  if (["planszówki", "gry", "gaming", "rpg"].includes(t)) return "🎲";
  if (["podróże", "spacer", "natura"].includes(t)) return "📍";
  if (["technologia", "programowanie", "biznes"].includes(t)) return "💡";

  return "🎟️";
}

function getEventTagsLabel(ev) {
  const tags = Array.isArray(ev?.interests) && ev.interests.length
    ? ev.interests
    : [ev?.interest || ev?.interest_tag || "wydarzenie"];

  return tags
    .map(tag => normalizeTag(String(tag || "")))
    .filter(Boolean)
    .map(tag => `#${tag}`)
    .join(" ");
}

function openPerson(personId) {
  const p = resolvePersonById(personId);
  if (!p) return;

  App.selectedPersonId = personId;

  const initialProfileState =
    String(personId) === String(App.currentUserId) ? "self" : "default";

  setPersonFriendButtonState(initialProfileState);
  setPersonChatButtonState(initialProfileState);

  const isPartnerProfile = String(p.role || "").toLowerCase() === "partner";
  const friendBtn = $("personFriendBtn");
  const chatBtn = $("personChatBtn");
  const chips = $("personInterests");
  const avatar = $("personAvatar");

  if (isPartnerProfile) {
    if (friendBtn) {
      friendBtn.style.display = "none";
      friendBtn.disabled = true;
    }

    const actionsWrap = document.querySelector("#S5_PERSON_PROFILE .personProfileActions");
    if (actionsWrap) {
      actionsWrap.classList.add("isSingle");
    }

    if (chatBtn) {
      chatBtn.disabled = false;
      chatBtn.style.opacity = "";
      chatBtn.classList.remove("secondary");
      chatBtn.dataset.state = "friend";
      chatBtn.textContent = t("personProfile.message");
    }

    const organizerId = String(p.id || personId);
    const displayName = p.company || p.nick || t("personProfile.organizer");
    safeSetText("personInterestsTitle", t("personProfile.partnerCategory"));
    safeSetText("personTitle", displayName);
    safeSetText("personNick", displayName);
    safeSetText("personMeta", p.city || t("personProfile.organizer"));
    const matchEl = $("personMatchScore");
    if (matchEl) matchEl.style.display = "none";
    safeSetText("personMatchScore", "");
    safeSetText("personBioTitle", t("personProfile.organizerAboutTitle"));
    safeSetText("personBio", p.bio || t("personProfile.emptyOrganizerBio"));

    const partnerEventsPanel = $("partnerEventsPanel");
    const partnerEventsList = $("personPartnerEventsList");

    if (partnerEventsPanel && partnerEventsList) {
      const partnerEvents = (App.events || []).filter(ev => String(ev.organizer?.id || "") === organizerId);
      partnerEventsPanel.hidden = false;
      partnerEventsList.innerHTML = partnerEvents.length
        ? partnerEvents.slice(0, 4).map(ev => `
            <div
              class="partnerEventRow"
              onclick="openEvent('${String(ev.id)}')"
            >
              <div class="partnerEventIcon">
                ${getEventTagIcon(ev.interest)}
              </div>

              <div class="partnerEventContent">
                <div class="partnerEventTitle">
                  ${escapeHtml(ev.title || t("personProfile.defaultEvent"))}
                </div>

                <div class="partnerEventMeta">
                  📍 ${escapeHtml([ev.city, ev.where].filter(Boolean).join(" • "))}
                </div>

                <div class="partnerEventMeta">
                  📅 ${escapeHtml(ev.when || t("personProfile.eventSoon"))}
                </div>
              </div>

              <div class="partnerEventArrow">›</div>
            </div>
          `).join("")
        : `<div class="sectionSub">${t("personProfile.noPartnerEvents")}</div>`;
    }

    if (avatar) {
      const rawSrc = p.logoUrl || p.avatarUrl || "";
      const src = rawSrc && String(rawSrc).trim() !== "" ? rawSrc : "";
      avatar.style.display = "";
      avatar.innerHTML = src
        ? `<img src="${String(src).startsWith("http") ? src : `${API_BASE_URL}${src}`}" alt="${displayName}" style="width:100%;height:100%;object-fit:cover;border-radius:inherit;" />`
        : `<div style="width:100%;height:100%;display:flex;align-items:center;justify-content:center;background:linear-gradient(145deg,#f8fbff,#dce7f7);color:#111827;font-weight:1000;font-size:30px;border-radius:inherit;">${avatarInitial(displayName)}</div>`;
    }

    if (chips) {
      chips.dataset.label = t("personProfile.partnerCategory");
      chips.innerHTML = "";
      const categoryLabel = getPartnerCategoryLabel(p.category);
      if (categoryLabel) chips.appendChild(makeChip(categoryLabel, null));
    }
    go("S5_PERSON_PROFILE");
    return;
  }

  safeSetText("personInterestsTitle", t("personProfile.interestsTitle"));
  safeSetText("personBioTitle", t("personProfile.bioTitle"));
  const partnerEventsPanelDefault = $("partnerEventsPanel");
  if (partnerEventsPanelDefault) partnerEventsPanelDefault.hidden = true;

  if (App.role === "partner") {
    if (friendBtn) friendBtn.style.display = "none";
    if (chatBtn) {
      const rules = getPartnerPlanRules();
      chatBtn.disabled = !rules.canMessageParticipants;
      chatBtn.style.opacity = rules.canMessageParticipants ? "" : "0.7";
      chatBtn.classList.toggle("secondary", !rules.canMessageParticipants);
      chatBtn.dataset.state = rules.canMessageParticipants ? "friend" : "partner_locked";
      chatBtn.textContent = rules.canMessageParticipants ? t("personProfile.message") : t("personProfile.messagesPro");
    }
  } else {
    if (friendBtn) friendBtn.style.display = "";
  }

  safeSetText("personTitle", p.nick);
  safeSetText("personNick", p.nick);
  safeSetText("personMeta", [
    p.city,
    Number.isFinite(p.age) && p.age > 0 ? t("personProfile.ageYears", { age: p.age }) : ""
  ].filter(Boolean).join(" • ") || t("personProfile.userProfileFallback"));
  safeSetText("personDistanceMeta", formatDistanceFromMe(p));
  const matchEl = $("personMatchScore");
  if (matchEl) matchEl.style.display = "";
  safeSetText("personMatchScore", t("personProfile.match", { score: sharedScore(p) }));
  safeSetText("personBio", p.bio || t("personProfile.emptyBio"));

  if (avatar) {
    avatar.innerHTML = p.avatarUrl
      ? `<img src="${String(p.avatarUrl).startsWith("http") ? p.avatarUrl : `${API_BASE_URL}${p.avatarUrl}`}" alt="${p.nick}" style="width:100%;height:100%;object-fit:cover;border-radius:inherit;" />`
      : `<div class="userAvatarFallback" style="${premiumAvatarStyle(getAvatarGradient(p.nick || "U"))}" data-name="${escapeHtml(p.nick || "U")}">${avatarInitial(p.nick || "U")}</div>`;
  }

  if (chips) {
    chips.dataset.label = "";
    chips.innerHTML = "";
    const shared = new Set(commonInterests(p).map(x => String(x).toLowerCase()));
    (p.interests || []).forEach(tag => {
      const chip = makeChip(`#${tag}`, null);
      if (shared.has(String(tag).toLowerCase())) {
        chip.classList.add("isShared");
      }
      chips.appendChild(chip);
    });
    renderPersonTrainerInterests(p);
  }

  go("S5_PERSON_PROFILE");
  refreshProfileRelations().catch(() => {});

  if (String(personId) === String(App.currentUserId)) return;

  apiFetch(`/users/${encodeURIComponent(personId)}`)
    .then((data) => {
      const full = data?.data ? mapApiPersonToViewModel(data.data) : null;
      if (!full) return;

      const previous = resolvePersonById(personId);
      const nearbyPerson = (App.people || []).find(p => String(p.id) === String(personId));

      if (nearbyPerson?.distance_km != null) full.distance_km = nearbyPerson.distance_km;
      if (nearbyPerson?.location_lat != null) full.location_lat = nearbyPerson.location_lat;
      if (nearbyPerson?.location_lng != null) full.location_lng = nearbyPerson.location_lng;

      if (full.distance_km == null && previous?.distance_km != null) {
        full.distance_km = previous.distance_km;
      }

      if (String(App.selectedPersonId) !== String(personId)) return;

      safeSetText("personTitle", full.nick);
      safeSetText("personNick", full.nick);
      safeSetText("personMeta", [
        full.city,
        Number.isFinite(full.age) && full.age > 0 ? t("personProfile.ageYears", { age: full.age }) : ""
      ].filter(Boolean).join(" • ") || t("personProfile.userProfileFallback"));
      safeSetText("personDistanceMeta", formatDistanceFromMe(full));
      safeSetText("personMatchScore", t("personProfile.match", { score: sharedScore(full) }));
      safeSetText("personBio", full.bio || t("personProfile.emptyBio"));

      const avatarEl = $("personAvatar");
      if (avatarEl) {
        avatarEl.innerHTML = full.avatarUrl
          ? `<img src="${String(full.avatarUrl).startsWith("http") ? full.avatarUrl : `${API_BASE_URL}${full.avatarUrl}`}" alt="${full.nick}" style="width:100%;height:100%;object-fit:cover;border-radius:inherit;" />`
          : `<div class="userAvatarFallback" style="${premiumAvatarStyle(getAvatarGradient(full.nick || "U"))}" data-name="${escapeHtml(full.nick || "U")}">${avatarInitial(full.nick || "U")}</div>`;
      }

      const fullChips = $("personInterests");
      if (fullChips) {
        fullChips.dataset.label = "";
        fullChips.innerHTML = "";
        const shared = new Set(commonInterests(full).map(x => String(x).toLowerCase()));
        (full.interests || []).forEach(tag => {
          const chip = makeChip(`#${tag}`, null);
          if (shared.has(String(tag).toLowerCase())) {
            chip.classList.add("isShared");
          }
          fullChips.appendChild(chip);
        });
        renderPersonTrainerInterests(full);
      }

      const idx = (App.people || []).findIndex(x => String(x.id) === String(full.id));
      if (idx >= 0) {
        App.people[idx] = { ...App.people[idx], ...full };
      } else {
        App.people.push(full);
      }
    })
    .catch(() => {});
}


async function blockUser(userId) {
  const token = localStorage.getItem(USLY_STORAGE_KEYS.token) || localStorage.getItem("usly_token");
  if (!token || !userId) {
    toast(t("personProfile.toastMissingUser"));
    return;
  }

  try {
    const res = await fetch(`${API_BASE_URL}/blocks`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`,
      },
      body: JSON.stringify({ blocked_user_id: Number(userId) }),
    });

    const data = await res.json().catch(() => ({}));

    if (!res.ok) {
      toast(t("personProfile.toastBlockFailed"));
      return;
    }

    toast(t("personProfile.toastBlocked"));
    closeModal();

    // szybki refresh danych
    await Promise.all([
      loadNearbyPeople(),
      renderChatList?.(),
    ]);

  } catch (e) {
    console.error("submitEventReport failed", e);
    toast(e?.userMessage || e?.message || t("personProfile.toastConnectionError"));
  }
}


function openPersonMenu() {
  openModal(t("personProfile.options"), `
    <button class="btn secondary" type="button" onclick="openUserReportModal()">${t("personProfile.report")}</button>
    <button class="btn danger mt12" type="button" onclick="blockUser(App.selectedPersonId)">${t("personProfile.block")}</button>
  `);
}


function openUserReportModal() {
  if (!App.selectedPersonId) {
    toast(t("userReport.toastNoUser"));
    return;
  }

  openModal(t("userReport.modalTitle"), `
    <div data-hide-modal-footer="1" style="display:none;"></div>\n    <div class="tStrong">${t("userReport.reasonTitle")}</div>
    <div class="sectionSub mt10">${t("userReport.subtitle")}</div>

    <label class="mt12">${t("userReport.reasonLabel")}</label>
    <select id="userReportReason">
      <option value="spam">${t("userReport.reasonSpam")}</option>
      <option value="harassment">${t("userReport.reasonHarassment")}</option>
      <option value="inappropriate_profile">${t("userReport.reasonProfile")}</option>
      <option value="impersonation">${t("userReport.reasonImpersonation")}</option>
      <option value="other">${t("userReport.reasonOther")}</option>
    </select>

    <label class="mt12">${t("userReport.descriptionLabel")}</label>
    <textarea id="userReportDescription" maxlength="1000" placeholder="${t("userReport.descriptionPlaceholder")}"></textarea>
    <div class="charHint"><span id="userReportDescriptionCount">0</span>/1000</div>

    <button class="btn mt16" type="button" onclick="submitUserReport()">${t("userReport.submit")}</button>
    <button class="btn secondary mt12" type="button" onclick="closeModal()">${t("groups.create.cancel")}</button>
  `);

  setTimeout(() => {
    const ta = $("userReportDescription");
    const cnt = $("userReportDescriptionCount");
    if (!ta || !cnt) return;
    ta.addEventListener("input", () => {
      cnt.textContent = String(ta.value.length);
    });
  }, 0);
}

async function submitUserReport() {
  const reportedUserId = App.selectedPersonId;
  const reason = $("userReportReason")?.value || "";
  const description = $("userReportDescription")?.value?.trim() || "";

  if (!reportedUserId) {
    toast(t("userReport.toastNoUser"));
    return;
  }

  if (!reason) {
    toast(t("userReport.toastNoReason"));
    return;
  }

  try {
    const data = await apiFetch("/reports/user", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        reported_user_id: Number(reportedUserId),
        reason,
        description,
        current_view: App.currentView || "",
      }),
    });

    if (!data?.success) {
      toast(data?.error?.message || t("userReport.toastFailed"));
      return;
    }

    toast(t("userReport.toastSent", { ticket: data.data?.ticket || "" }).trim());
    closeModal();
  } catch (err) {
    toast(err?.userMessage || t("userReport.toastFailed"));
  }
}

function startChatFromProfile() {
  const pid = App.selectedPersonId;
  if (!pid) return;
  const p = resolvePersonById(pid);
  if (!p) return;

  const chatBtn = $("personChatBtn");
  const chatState = chatBtn?.dataset?.state || "default";

  if (chatState !== "friend") {
    if (chatState === "self") {
      toast(t("friends.selfAccount"));
    } else if (chatState === "pending") {
      toast(t("friends.toastChatAfterAccept"));
    } else {
      toast(t("friends.toastAddFirst"));
    }
    return;
  }

  // Create or open existing chat
  let chat = App.chats.find(c => String(c.with?.id) === String(pid));
  if (!chat) {
    chat = {
      id: `pm_${pid}`,
      with: {
        id: pid,
        nick: p.nick,
        role: "user",
        city: p.city || "",
        bio: p.bio || "",
        avatarUrl: p.avatarUrl || "",
        emoji: p.emoji || "",
      },
      last: "",
      unread: 0,
      messages: [],
    };
    App.chats.unshift(chat);
  }

  App.selectedChatId = chat.id;
  openChat(chat.id);
}

function setPersonFriendButtonState(state) {
  const btn = $("personFriendBtn");
  if (!btn) return;

  const badge = $("personRelationBadge");
  const actions = document.querySelector(".personProfileActions");

  if (badge) {
    badge.textContent = "";
    badge.classList.remove("isVisible");
  }
  if (actions) {
    actions.classList.remove("isFriend");
    actions.classList.remove("isSingle");
  }

  if (App.role === "partner") {
    btn.style.display = "none";
    btn.dataset.state = "partner_hidden";
    return;
  }

  btn.style.display = "";
  btn.dataset.state = state || "default";
  btn.disabled = false;
  btn.style.opacity = "";
  btn.classList.remove("secondary");
  btn.textContent = t("friends.add");

  if (state === "self") {
    btn.textContent = t("friends.selfAccount");
    btn.disabled = true;
    btn.style.opacity = "0.7";
    btn.classList.add("secondary");
    if (actions) actions.classList.add("isSingle");
    return;
  }

  if (state === "friend") {
    btn.style.display = "none";
    btn.dataset.state = "friend_status";
    if (badge) {
      badge.textContent = t("friends.friend");
      badge.classList.add("isVisible");
    }
    if (actions) {
      actions.classList.add("isFriend");
    }
    return;
  }

  if (state === "pending") {
    btn.textContent = t("friends.pending");
    btn.disabled = true;
    btn.style.opacity = "0.7";
    btn.classList.add("secondary");
    if (actions) actions.classList.add("isSingle");
    return;
  }
}

function setPersonChatButtonState(state) {
  const btn = $("personChatBtn");
  if (!btn) return;

  if (App.role === "partner") {
    btn.style.display = "";
    const rules = getPartnerPlanRules();
    btn.dataset.state = rules.canMessageParticipants ? "friend" : "partner_locked";
    btn.disabled = !rules.canMessageParticipants;
    btn.style.opacity = rules.canMessageParticipants ? "" : "0.7";
    btn.classList.toggle("secondary", !rules.canMessageParticipants);
    btn.textContent = rules.canMessageParticipants ? t("friends.message") : t("friends.messagesPro");
    return;
  }

  btn.dataset.state = state || "default";
  btn.disabled = false;
  btn.style.opacity = "";
  btn.classList.add("secondary");
  btn.textContent = t("friends.message");
  btn.style.display = "none";

  if (state === "friend") {
    btn.style.display = "";
    btn.textContent = t("friends.message");
    btn.classList.remove("secondary");
    return;
  }
}

function syncPersonFriendButton(incoming, outgoing, friends) {
  const pid = App.selectedPersonId;
  if (!pid) return;

  if (String(pid) === String(App.currentUserId)) {
    setPersonFriendButtonState("self");
    setPersonChatButtonState("self");
    return;
  }

  const normalizedFriends = Array.isArray(friends) ? friends : [];
  const normalizedIncoming = Array.isArray(incoming) ? incoming : [];
  const normalizedOutgoing = Array.isArray(outgoing) ? outgoing : [];

  const isFriend = normalizedFriends.some(item => {
    const friendId = item.id || item.user_id || item.friend_id;
    return String(friendId) === String(pid);
  });

  if (isFriend) {
    setPersonFriendButtonState("friend");
    setPersonChatButtonState("friend");
    return;
  }

  const hasPendingIncoming = normalizedIncoming.some(item => {
    const user = item.user || {};
    return String(user.id) === String(pid) && String(item.status || "pending").toLowerCase() === "pending";
  });

  const hasPendingOutgoing = normalizedOutgoing.some(item => {
    const user = item.user || {};
    return String(user.id) === String(pid) && String(item.status || "pending").toLowerCase() === "pending";
  });

  if (hasPendingIncoming || hasPendingOutgoing) {
    setPersonFriendButtonState("pending");
    setPersonChatButtonState("pending");
    return;
  }

  setPersonFriendButtonState("default");
  setPersonChatButtonState("default");
}

async function addFriendFromProfile() {
  const pid = App.selectedPersonId;
  if (!pid) {
    toast(t("friends.toastNoProfile"));
    return;
  }

  if (String(pid) === String(App.currentUserId)) {
    toast(t("friends.selfAccount"));
    return;
  }

  const token = localStorage.getItem(USLY_STORAGE_KEYS.token) || localStorage.getItem("usly_token");
  if (!token) {
    toast(t("friends.toastLogin"));
    return;
  }

  try {
    const data = await apiFetch("/friends/requests", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ addressee_user_id: Number(pid) }),
    });

    if (!data?.success && data !== null) {
      toast(data?.error?.message || t("friends.toastSendFailed"));
      return;
    }

    toast(t("friends.toastSent"));
    await refreshProfileRelations();
    await refreshNotifBadgeCount();
    if (App.currentView === "S12_NOTIFICATIONS") await renderNotifications();
  } catch (err) {
    toast(err?.userMessage || err?.message || t("friends.toastSendFailed"));
  }
}

async function refreshProfileRelations() {
  if (App.role !== "user") return;

  const token = localStorage.getItem(USLY_STORAGE_KEYS.token) || localStorage.getItem("usly_token");
  if (!token) return;

  try {
    const [requestsRes, groupInvRes, friendsRes] = await Promise.all([
      fetch(`${API_BASE_URL}/friends/requests`, {
        headers: { "Authorization": `Bearer ${token}` },
      }),
      fetch(`${API_BASE_URL}/group-invitations`, {
        headers: { "Authorization": `Bearer ${token}` },
      }),
      fetch(`${API_BASE_URL}/friends`, {
        headers: { "Authorization": `Bearer ${token}` },
      }),
    ]);

    const requestsData = await requestsRes.json().catch(() => ({}));
    const groupInvData = await groupInvRes.json().catch(() => ({}));
    const friendsData = await friendsRes.json().catch(() => ({}));

    const requestsPayload = requestsData && typeof requestsData === "object"
      ? (requestsData.data || requestsData)
      : {};

    const groupInvPayload = groupInvData && typeof groupInvData === "object"
      ? (groupInvData.data || groupInvData)
      : {};

    const friendsPayload = friendsData && typeof friendsData === "object"
      ? (friendsData.data || friendsData)
      : [];

    const incoming = Array.isArray(requestsPayload.incoming) ? requestsPayload.incoming : [];
    const outgoing = Array.isArray(requestsPayload.outgoing) ? requestsPayload.outgoing : [];
    const incomingGroupInvites = Array.isArray(groupInvPayload.incoming) ? groupInvPayload.incoming : [];
    const outgoingGroupInvites = Array.isArray(groupInvPayload.outgoing) ? groupInvPayload.outgoing : [];
    const friends = Array.isArray(friendsPayload) ? friendsPayload : (Array.isArray(friendsPayload.items) ? friendsPayload.items : []);
    window._lastFriendsList = friends.map(friend => ({
      ...friend,
      avatarUrl: friend.avatar_url || "",
      interests: Array.isArray(friend.interests) ? friend.interests : [],
      emoji: friend.emoji || "",
    }));
    window._lastOutgoingGroupInvites = Array.isArray(outgoingGroupInvites) ? outgoingGroupInvites : [];

    const sortedFriends = [...friends].sort((a, b) => {
      const an = String(a?.nick || a?.name || a?.friend_nick || "").toLocaleLowerCase("pl-PL");
      const bn = String(b?.nick || b?.name || b?.friend_nick || "").toLocaleLowerCase("pl-PL");
      return an.localeCompare(bn, "pl-PL");
    });

    window._lastFriendsList = sortedFriends.map(friend => ({
      ...friend,
      avatarUrl: friend.avatar_url || "",
      interests: Array.isArray(friend.interests) ? friend.interests : [],
      emoji: friend.emoji || "",
    }));

    renderProfileFriendRequests(incoming, outgoing, incomingGroupInvites, outgoingGroupInvites);
    renderProfileFriends(sortedFriends);
    syncPersonFriendButton(incoming, outgoing, sortedFriends);
  } catch (_) {
    renderProfileFriendRequests([], []);
    renderProfileFriends([]);
    syncPersonFriendButton([], [], []);
  }
}

function renderProfileFriendRequests(incoming, outgoing, incomingGroupInvites = [], outgoingGroupInvites = []) {
  const el = $("profileFriendRequestsList");
  if (!el) return;

  const inItems = Array.isArray(incoming) ? incoming : [];
  const outItems = Array.isArray(outgoing) ? outgoing : [];
  const inGroupItems = Array.isArray(incomingGroupInvites) ? incomingGroupInvites : [];
  const outGroupItems = Array.isArray(outgoingGroupInvites) ? outgoingGroupInvites : [];

  if (!inItems.length && !outItems.length && !inGroupItems.length && !outGroupItems.length) {
    el.innerHTML = `<div class="tMuted">${t("friends.emptyInvites")}</div>`;
    return;
  }

  const incomingHtml = inItems.map(item => {
    const user = item.user || {};
    const sender = user.nick || t("friends.defaultUser", { id: user.id || "—" });
    const city = user.city || "";
    const requestId = item.id;

    return `
      <div class="card" style="margin:0;">
        <div class="row" style="align-items:center;justify-content:space-between;gap:12px;">
            <div style="text-align:left;flex:1;cursor:pointer;" onclick="openPerson('${user.id}')">
            <div class="sectionTitle" style="font-size:16px;">${sender}</div>
            <div class="sectionSub">${city || t("friends.pendingDecision")}</div>
          </div>
          <div class="row" style="gap:8px;flex-wrap:wrap;justify-content:flex-end;">
            <button class="btn small" type="button" onclick="respondToFriendRequest(${Number(requestId)}, 'accepted')">${t("friends.accept")}</button>
            <button class="btn secondary small" type="button" onclick="respondToFriendRequest(${Number(requestId)}, 'rejected')">${t("friends.reject")}</button>
          </div>
        </div>
      </div>
    `;
  }).join("");

  const outgoingHtml = outItems.map(item => {
    const user = item.user || {};
    const nick = user.nick || t("friends.defaultUser", { id: user.id || "—" });
    const city = user.city || "";

    return `
      <div class="card" style="margin:0;opacity:0.9;">
        <div class="row" style="align-items:center;justify-content:space-between;gap:12px;">
            <div style="text-align:left;flex:1;cursor:pointer;" onclick="openPerson('${user.id}')">
            <div class="sectionTitle" style="font-size:16px;">${nick}</div>
            <div class="sectionSub">${city || t("friends.pendingAccept")}</div>
          </div>
          <div class="pill">${t("friends.sentPill")}</div>
        </div>
      </div>
    `;
  }).join("");

  const groupInvHtml = incomingGroupInvites.map(inv => {
    const user = inv.user || {};
    const group = inv.group || {};
    const nick = user.nick || t("friends.defaultUser", { id: user.id || "—" });
    const groupTitle = group.title || t("friends.defaultGroup");

    return `
      <div class="card" style="margin:0;">
        <div class="row" style="align-items:center;justify-content:space-between;gap:12px;">
          <div style="text-align:left;flex:1;">
            <div class="sectionTitle" style="font-size:16px;">${groupTitle}</div>
            <div class="sectionSub">${t("friends.groupInviteLine", { user: nick })}</div>
          </div>
          <div class="row" style="gap:8px;flex-wrap:wrap;justify-content:flex-end;">
            <button class="btn small" type="button" onclick="respondToGroupInvitation(${Number(inv.id)}, 'accepted')">${t("friends.accept")}</button>
            <button class="btn secondary small" type="button" onclick="respondToGroupInvitation(${Number(inv.id)}, 'rejected')">${t("friends.reject")}</button>
          </div>
        </div>
      </div>
    `;
  }).join("");

  el.innerHTML = incomingHtml + groupInvHtml + outgoingHtml;
}



function filterFriendsList(query) {
  const q = String(query || "").toLowerCase();

  const all = Array.isArray(window._lastFriendsList)
    ? window._lastFriendsList
    : [];

  const filtered = !q
    ? all
    : all.filter(f => {
        const nick = String(f.nick || f.name || "").toLowerCase();
        return nick.includes(q);
      });

  renderProfileFriends(filtered);
}

function renderProfileFriends(items) {
  const el = $("profileFriendsList");
  if (!el) return;

  if (!items.length) {
    el.innerHTML = `<div class="tMuted">${t("friends.emptyFriends")}</div>`;
    return;
  }

  el.innerHTML = items.map(item => {
    const friendId = item.id || item.user_id || item.friend_id;
    const friendNick = item.nick || item.name || item.friend_nick || t("friends.defaultUser", { id: friendId || "—" });
    const friendCity = item.city || "";

    return `
      <div class="card" style="margin:0;cursor:pointer;" onclick="openChatParticipantProfile('${String(friendId || "")}')">
        <div class="row" style="align-items:center;justify-content:space-between;gap:12px;">
          <div style="text-align:left;flex:1;">
            <div class="sectionTitle" style="font-size:16px;">${friendNick}</div>
            <div class="sectionSub">${friendCity || t("friends.friendFallback")}</div>
          </div>
          <button class="btn secondary small" type="button" onclick="event.stopPropagation(); openChatParticipantProfile('${String(friendId || "")}')">${t("friends.viewProfile")}</button>
        </div>
      </div>
    `;
  }).join("");
}


async function respondToGroupInvitation(invitationId, action) {
  const token = localStorage.getItem(USLY_STORAGE_KEYS.token) || localStorage.getItem("usly_token");
  if (!token || !invitationId) {
    toast(t("friends.groupInviteMissing"));
    return;
  }

  try {
    const res = await fetch(`${API_BASE_URL}/group-invitations/${invitationId}/respond`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`,
      },
      body: JSON.stringify({ action }),
    });

    const data = await res.json().catch(() => ({}));

    if (!res.ok) {
      toast(data?.error?.message || data?.detail || t("friends.groupInviteUpdateFailed"));
      return;
    }

    toast(action === "accepted" ? t("friends.groupInviteAccepted") : t("friends.groupInviteRejected"));
    await loadMyGroups();
    await refreshProfileRelations();
    await refreshGroupBadgeCount();
    if (App.currentView === "S12_NOTIFICATIONS") await renderNotifications();
  } catch (_) {
    toast(t("friends.groupInviteConnectionFailed"));
  }
}


async function respondToFriendRequest(requestId, action) {
  const token = localStorage.getItem(USLY_STORAGE_KEYS.token) || localStorage.getItem("usly_token");
  if (!token || !requestId) {
    toast(t("groups.toast.inviteMissing"));
    return;
  }

  try {
    const res = await fetch(`${API_BASE_URL}/friends/requests/${requestId}/respond`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`,
      },
      body: JSON.stringify({ action }),
    });

    const data = await res.json().catch(() => ({}));

    if (!res.ok) {
      toast(data.detail || t("friends.inviteUpdateFailed"));
      return;
    }

    toast(action === "accepted" ? t("friends.inviteAccepted") : t("friends.inviteRejected"));
    await refreshProfileRelations();
  } catch (_) {
    toast(t("friends.inviteConnectionFailed"));
  }
}

function getChatOtherPerson() {
  if (!App.selectedChatUserId) return null;
  return resolvePersonById(App.selectedChatUserId) || null;
}

function openChatParticipantProfile(userId) {
  if (!userId) return;

  if (String(userId) === String(App.currentUserId)) {
    toast(t("friends.selfAccount"));
    return;
  }

  const person = resolvePersonById(userId);
  if (!person) {
    toast(t("friends.toastProfileUnavailable"));
    return;
  }

  openPerson(person.id);
}

/* ------------------------- Chats -------------------------- */
async function openChat(chatId) {
  const chat = App.chats.find(c => c.id === chatId);
  if (!chat) return;
  App.selectedChatId = chatId;
  App.selectedChatUserId = chat.with.id;
  App.chatUnreadAtOpen = Number(chat.rawUnread ?? chat.unread ?? 0);

  safeSetText("chatTitle", chat.with.nick);

  // Mark read
  chat.unread = 0;

  go("S6B_CHAT_THREAD");
}

function getBlockedChatMessagesKey(recipientUserId = App.selectedChatUserId) {
  return `usly_blocked_messages_${App.currentUserId || "guest"}_${String(recipientUserId || "unknown")}`;
}

function loadBlockedChatMessages(recipientUserId = App.selectedChatUserId) {
  try {
    return JSON.parse(localStorage.getItem(getBlockedChatMessagesKey(recipientUserId)) || "[]");
  } catch (_) {
    return [];
  }
}

function saveBlockedChatMessages(recipientUserId, items) {
  try {
    localStorage.setItem(getBlockedChatMessagesKey(recipientUserId), JSON.stringify((items || []).slice(-30)));
  } catch (_) {}
}


async function renderChatThread() {
  const box = $("chatBubbles");
  if (!box || !App.selectedChatUserId) return;

  const renderMessageRow = ({ from, text, senderUserId, createdAt, isRead, pending = false, blockedReason = "" }) => {
    const row = document.createElement("div");
    row.style.display = "flex";
    row.style.alignItems = "flex-end";
    row.style.gap = "10px";
    row.style.margin = "10px 0";
    row.style.justifyContent = from === "me" ? "flex-end" : "flex-start";

    const avatar = document.createElement("button");
    avatar.type = "button";
    avatar.style.width = "32px";
    avatar.style.height = "32px";
    avatar.style.minWidth = "32px";
    avatar.style.borderRadius = "999px";
    avatar.style.border = from === "them" ? "1px solid rgba(16,24,40,0.08)" : "0";
    avatar.style.padding = "0";
    avatar.style.display = "inline-flex";
    avatar.style.alignItems = "center";
    avatar.style.justifyContent = "center";
    avatar.style.background = "#f2f4f7";
    avatar.style.cursor = from === "them" ? "pointer" : "default";
    avatar.style.overflow = "hidden";
    avatar.style.boxShadow = from === "them" ? "0 2px 8px rgba(16,24,40,0.08)" : "none";
    avatar.style.flexShrink = "0";

    if (from === "me") {
      const meName = App.role === "partner"
        ? (App.partner.company || App.partner.nazwa || t("personProfile.organizer"))
        : (App.user.nick || "U");
      const meAvatar = App.role === "partner"
        ? (App.partner.logoUrl || App.partner.logo_url || "")
        : (App.user.avatarUrl || "");

      if (meAvatar) {
        const src = String(meAvatar).startsWith("http")
          ? meAvatar
          : `${API_BASE_URL}${meAvatar}`;
        avatar.innerHTML = `<img src="${src}" alt="${t("chat.avatarMine")}" style="width:100%;height:100%;object-fit:cover;" />`;
      } else {
        avatar.innerHTML = `<div style="width:100%;height:100%;display:flex;align-items:center;justify-content:center;background:linear-gradient(145deg,#f8fbff,#dce7f7);color:#111827;font-weight:900;border:1px solid rgba(255,255,255,.75);">${avatarInitial(meName)}</div>`;
      }
      avatar.disabled = true;
    } else {
      const other = getChatOtherPerson();
      const otherAvatar = other?.avatarUrl || other?.logoUrl || other?.logo_url || "";
      const otherName = other?.nick || other?.company || other?.name || t("chat.defaultUser");
      if (otherAvatar) {
        const src = String(otherAvatar).startsWith("http")
          ? otherAvatar
          : `${API_BASE_URL}${otherAvatar}`;
        avatar.innerHTML = `<img src="${src}" alt="${escapeHtml(otherName)}" style="width:100%;height:100%;object-fit:cover;" />`;
      } else {
        avatar.innerHTML = `<div style="width:100%;height:100%;display:flex;align-items:center;justify-content:center;background:linear-gradient(145deg,#f8fbff,#dce7f7);color:#111827;font-weight:900;border:1px solid rgba(255,255,255,.75);">${avatarInitial(otherName)}</div>`;
      }
      avatar.title = t("chat.openProfile");
      avatar.addEventListener("mouseenter", () => {
        avatar.style.transform = "scale(1.04)";
      });
      avatar.addEventListener("mouseleave", () => {
        avatar.style.transform = "scale(1)";
      });
      avatar.style.transition = "transform 120ms ease, box-shadow 120ms ease";
      avatar.addEventListener("click", (e) => {
        e.stopPropagation();
        openChatParticipantProfile(senderUserId);
      });
    }

    const bubble = document.createElement("div");
    bubble.className = `bubble ${from === "me" ? "me" : "them"}`;
    bubble.style.maxWidth = "78%";
    bubble.style.wordBreak = "break-word";
    bubble.style.boxShadow = "0 4px 14px rgba(16,24,40,0.06)";

    if (pending) {
      bubble.style.opacity = "0.72";
      bubble.style.filter = "grayscale(.12)";
    }

    if (blockedReason) {
      bubble.style.opacity = "0.58";
      bubble.style.background = "rgba(120,120,120,.14)";
      bubble.style.border = "1px dashed rgba(255,120,120,.45)";
    }

    const rawText = String(text || "");
    const ts = parseUslyTimestamp(createdAt);
    const timeLabel = ts
      ? new Date(ts).toLocaleString("pl-PL", {
          day: "2-digit",
          month: "2-digit",
          hour: "2-digit",
          minute: "2-digit",
        })
      : "";
    const readLabel = from === "me" ? (isRead ? "✓✓" : "✓") : "";
    const metaLabel = [timeLabel, readLabel].filter(Boolean).join("   ");

    if (rawText.startsWith("📣 ")) {
      const lines = rawText.split("\n").map(x => x.trim()).filter(Boolean);
      const titleLine = lines[0] || t("chat.defaultEventTitle");
      const bodyLines = lines.filter(line => line !== t("chat.organizerMessageMarker") && line !== titleLine);
      const bodyText = bodyLines.join("\n\n");

      bubble.innerHTML = `
        <div style="display:flex;flex-direction:column;gap:8px;">
          <div style="font-weight:1000;line-height:1.15;">${escapeHtml(titleLine)}</div>
          <div style="font-size:12px;font-weight:900;letter-spacing:.01em;opacity:.72;text-transform:uppercase;">${t("chat.organizerMessage")}</div>
          <div style="line-height:1.45;">${escapeHtml(bodyText)}</div>
          ${metaLabel ? `<div style="font-size:11px;opacity:.65;text-align:right;">${metaLabel.includes("✓✓") ? escapeHtml(metaLabel).replace("✓✓", '<span style="color:#6EE7FF;font-weight:700;">✓✓</span>') : metaLabel.includes("✓") ? escapeHtml(metaLabel).replace("✓", '<span style="opacity:0.4;">✓</span>') : escapeHtml(metaLabel)}</div>` : ``}
        </div>
      `;
    } else {
      bubble.innerHTML = `
        <div style="display:flex;flex-direction:column;gap:6px;">
          <div style="line-height:1.45;">
            ${blockedReason
              ? `⚠️ ${escapeHtml(blockedReason)}`
              : pending
                ? `${escapeHtml(rawText)}<div style="margin-top:6px;font-size:11px;opacity:.72;">${t("chat.checkingContent")}</div>`
                : escapeHtml(rawText)
            }
          </div>
          ${metaLabel ? `<div style="font-size:11px;opacity:.65;text-align:right;">${metaLabel.includes("✓✓") ? escapeHtml(metaLabel).replace("✓✓", '<span style="color:#6EE7FF;font-weight:700;">✓✓</span>') : metaLabel.includes("✓") ? escapeHtml(metaLabel).replace("✓", '<span style="opacity:0.4;">✓</span>') : escapeHtml(metaLabel)}</div>` : ``}
        </div>
      `;
    }

    if (from === "me") {
      row.appendChild(bubble);
      row.appendChild(avatar);
    } else {
      row.appendChild(avatar);
      row.appendChild(bubble);
    }

    box.appendChild(row);
  };

  try {
    const data = await apiFetch(`/messages/private/${App.selectedChatUserId}`);
    const items = Array.isArray(data?.data?.items) ? data.data.items : [];
    const unreadAtOpen = Math.max(0, Number(App.chatUnreadAtOpen || 0));
    const incomingTotal = items.filter(m => String(m.sender_user_id) !== String(App.currentUserId)).length;
    const dividerIncomingIndex = unreadAtOpen > 0 ? Math.max(0, incomingTotal - unreadAtOpen) : -1;

    box.innerHTML = "";
    let newDividerInserted = false;
    let incomingIndex = 0;

    const savedBlockedMessages = loadBlockedChatMessages(App.selectedChatUserId);
    const localPendingMessages = (renderChatThread.__localPending || [])
      .filter(m => String(m.recipientUserId || "") === String(App.selectedChatUserId));

    const timelineItems = [
      ...items.map(m => ({
        kind: "remote",
        from: String(m.sender_user_id) === String(App.currentUserId) ? "me" : "them",
        text: m.content || "",
        senderUserId: m.sender_user_id,
        createdAt: m.created_at || null,
        isRead: !!m.is_read,
      })),
      ...savedBlockedMessages.map(m => ({
        kind: "local",
        from: "me",
        text: m.text || "",
        senderUserId: App.currentUserId,
        createdAt: m.createdAt || null,
        isRead: false,
        pending: false,
        blockedReason: normalizeBlockedReason(m.blockedReason, "chat.blocked.content"),
      })),
      ...localPendingMessages.map(m => ({
        kind: "local",
        from: "me",
        text: m.text || "",
        senderUserId: App.currentUserId,
        createdAt: m.createdAt || null,
        isRead: false,
        pending: m.state === "pending",
        blockedReason: "",
      })),
    ].sort((a, b) => {
      const at = parseUslyTimestamp(a.createdAt) || 0;
      const bt = parseUslyTimestamp(b.createdAt) || 0;
      return at - bt;
    });

    timelineItems.forEach(m => {
      const from = m.from;

      if (from === "them") {
        if (!newDividerInserted && dividerIncomingIndex >= 0 && incomingIndex === dividerIncomingIndex) {
          const divider = document.createElement("div");
          divider.style.display = "flex";
          divider.style.alignItems = "center";
          divider.style.gap = "10px";
          divider.style.margin = "18px 0 10px";
          divider.innerHTML = `
            <div style="flex:1;height:1px;background:rgba(255,255,255,.10);"></div>
            <div class="sectionSub" style="white-space:nowrap;">${t("chatThread.newMessages")}</div>
            <div style="flex:1;height:1px;background:rgba(255,255,255,.10);"></div>
          `;
          box.appendChild(divider);
          newDividerInserted = true;
        }
        incomingIndex += 1;
      }

      renderMessageRow({
        from,
        text: m.text || "",
        senderUserId: m.senderUserId,
        createdAt: m.createdAt || null,
        isRead: !!m.isRead,
        pending: !!m.pending,
        blockedReason: m.blockedReason || "",
      });
    });

    const chat = App.chats.find(c => c.id === App.selectedChatId);
    if (chat) {
      chat.last = items.length ? (items[items.length - 1].content || "") : chat.last;
      chat.messages = items.map(m => ({
        from: String(m.sender_user_id) === String(App.currentUserId) ? "me" : "them",
        text: m.content || "",
        senderUserId: m.sender_user_id,
        createdAt: m.created_at || null,
        isRead: !!m.is_read,
      }));
    }

    markChatAsSeen(App.selectedChatId);

    if (chat) {
      chat.unread = 0;
      chat.rawUnread = 0;
    }

    if (App.role === "partner") {
      refreshPartnerMsgBadgeCount().catch(() => {});
    } else {
      renderChatList().catch(() => {});
    }
  } catch (err) {
    console.error("renderChatThread failed", err);

    const chat = App.chats.find(c => c.id === App.selectedChatId);
    if (!chat) return;

    box.innerHTML = "";
    chat.messages.forEach(m => {
      renderMessageRow({
        from: m.from === "me" ? "me" : "them",
        text: m.text || "",
        senderUserId: m.senderUserId || App.selectedChatUserId,
        createdAt: m.createdAt || null,
        isRead: !!m.isRead,
      });
    });
  }

  setTimeout(() => {
    box.parentElement?.scrollTo({ top: box.parentElement.scrollHeight, behavior: "smooth" });
  }, 0);
}

async function sendChat() {
  if (sendChat.__busy) return;
  const inp = $("chatInput");
  const sendBtn = $("chatSendBtn");
  const text = inp?.value?.trim();
  if (!text || !App.selectedChatUserId) return;
  sendChat.__busy = true;
  if (sendBtn) sendBtn.disabled = true;

  if (inp) inp.value = "";

  const box = $("chatBubbles");
  const pendingId = `pending-${Date.now()}`;
  const localCreatedAt = new Date().toISOString();
  if (box) {
    renderChatThread.__localPending = renderChatThread.__localPending || [];
    renderChatThread.__localPending.push({ id: pendingId, text, state: "pending", recipientUserId: String(App.selectedChatUserId), createdAt: localCreatedAt });
    await renderChatThread();
  }

  try {
    await apiFetch("/messages/private", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        recipient_user_id: Number(String(App.selectedChatUserId).replace("u", "")),
        content: text,
      }),
    });

    renderChatThread.__localPending = (renderChatThread.__localPending || []).filter(m => m.id !== pendingId);

    const chat = App.chats.find(c => c.id === App.selectedChatId);
    if (chat) chat.last = text;

    await renderChatThread();
    renderChatList();
  } catch (err) {
    const rawMessage = String(err?.userMessage || err?.message || err?.detail || "");
    const rawStatus = String(err?.status || err?.statusCode || err?.response?.status || "");
    const isModerated =
      rawStatus === "422" ||
      rawMessage.includes("message_blocked") ||
      rawMessage.includes("message_empty") ||
      rawMessage.includes("422") ||
      rawMessage.toLowerCase().includes("moderac");

    const blockedReason = rawMessage.includes("message_blocked_link")
      ? t("chat.blocked.link")
      : t("chat.blocked.content");

    const blockedItem = {
      id: pendingId,
      text,
      state: "blocked",
      blockedReason,
      recipientUserId: String(App.selectedChatUserId),
      createdAt: localCreatedAt,
    };

    renderChatThread.__localPending = (renderChatThread.__localPending || []).filter(m => m.id !== pendingId);

    const savedBlocked = loadBlockedChatMessages(App.selectedChatUserId);
    saveBlockedChatMessages(App.selectedChatUserId, [...savedBlocked, blockedItem]);

    await renderChatThread();

    if (!isModerated) {
      toast(err?.userMessage || t("chat.toast.sendFailed"));
    }
  } finally {
    sendChat.__busy = false;
    if (sendBtn) sendBtn.disabled = false;
  }
}

function openChatMenu() {
  const chatId = App.selectedChatId;
  const isMuted = isChatMuted(chatId);

  openModal(t("chat.menu.title"), `
    <button class="btn secondary" type="button"
      onclick="setChatMuted('${chatId}', ${isMuted ? "false" : "true"}); closeModal(); renderChatList(); toast('${isMuted ? t("chat.toast.notificationsOn") : t("chat.toast.notificationsMuted")}');">
      ${isMuted ? t("chat.menu.notificationsOn") : t("chat.menu.notificationsOff")}
    </button>

    <button class="btn danger mt12" type="button" onclick="blockUser(Number(String(App.selectedChatUserId).replace('u', '')))">${t("common.block")}</button>
  `);
}

/* ------------------------- Events -------------------------- */
function setEventsTab(tab) {
  if (tab === "nearby") tab = "for_you";
  if (tab !== "for_you" && tab !== "followed") return;
  App.eventsTab = tab;

  $("eventsTabNearby")?.classList.toggle("on", tab === "for_you");
  $("eventsTabForYou")?.classList.toggle("on", tab === "for_you");
  $("eventsTabFollowed")?.classList.toggle("on", tab === "followed");

  renderEventsList();
}

function openEvent(eventId) {
  const ev = App.events.find(e => String(e.id) === String(eventId));
  if (!ev) return;
  App.selectedEventId = eventId;

  safeSetText("eventTitleTop", ev.title);
  safeSetText("evTitle", ev.title);
  const eventPlaceName = ev.where || ev.address || "Miejsce wydarzenia";
  const eventPlaceAddress = ev.address || "";
  const hasEventCoords = ev.location_lat != null && ev.location_lng != null;

  safeSetText(
    "evMeta",
    [
      [ev.city, eventPlaceName].filter(Boolean).join(" • "),
      ev.when || ""
    ].filter(Boolean).join("\n")
  );
  safeSetText("evPlaceTitle", eventPlaceName);
  safeSetText(
    "evPlaceMeta",
    ev.address || ev.where || ev.city || (hasEventCoords ? t("eventDetail.locationSaved") : t("eventDetail.locationMissing"))
  );

  const chips = $("evInterestChips");
  if (chips) {
    chips.innerHTML = "";
    const tags = Array.isArray(ev.interests) && ev.interests.length ? ev.interests : [ev.interest];
    tags
      .map(tag => normalizeTag(String(tag || "")))
      .filter(Boolean)
      .forEach(tag => chips.appendChild(makeChip(`#${tag}`, null)));
  }

  safeSetText("evDesc", ev.desc || t("eventDetail.emptyDescription"));

  const organizerName = ev.organizer?.name || t("eventDetail.organizer");
  const organizerMeta = [
    getPartnerCategoryLabel(ev.organizer?.category || ""),
    ev.city || ""
  ].filter(Boolean).join(" • ") || t("eventDetail.organizerMeta");

  safeSetText("evOrganizerName", organizerName);
  const miniMapEl = $("evPlaceMiniMap");

  if (miniMapEl) {
    if (window.evPlaceMiniMapInstance) {
      window.evPlaceMiniMapInstance.remove();
      window.evPlaceMiniMapInstance = null;
    }

    const lat = Number(ev.location_lat);
    const lng = Number(ev.location_lng);

    if (!Number.isNaN(lat) && !Number.isNaN(lng)) {
      miniMapEl.hidden = false;

      setTimeout(() => {
        try {
          const map = L.map(miniMapEl, {
            zoomControl: false,
            attributionControl: false,
            dragging: false,
            scrollWheelZoom: false,
            doubleClickZoom: false,
            boxZoom: false,
            keyboard: false,
            tap: false,
            touchZoom: false,
          }).setView([lat, lng], 15);

          window.evPlaceMiniMapInstance = map;

          L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
            maxZoom: 19,
          }).addTo(map);

          L.marker([lat, lng]).addTo(map);

          setTimeout(() => map.invalidateSize(), 120);
        } catch (e) {
          console.error("event mini map render error", e);
        }
      }, 50);
    } else {
      miniMapEl.hidden = true;
    }
  }

  safeSetText("evOrganizerMeta", organizerMeta);

  const organizerLogo = $("evOrganizerLogo");
  if (organizerLogo) {
    const src = ev.organizer?.logoUrl || "";
    organizerLogo.innerHTML = src
      ? `<img src="${String(src).startsWith("http") ? src : `${API_BASE_URL}${src}`}" alt="${organizerName}" style="width:100%;height:100%;object-fit:cover;border-radius:inherit;" />`
      : premiumIcon("org", organizerName || t("eventDetail.organizer"));
  }

  const capacityLine = $("evCapacityLine");
  const capacityAlert = $("evCapacityAlert");
  const capacityCopy = getEventCapacityCopy(ev);

  if (capacityLine) capacityLine.textContent = capacityCopy.line;
  if (capacityAlert) {
    if (capacityCopy.alert) {
      capacityAlert.style.display = "block";
      capacityAlert.textContent = capacityCopy.alert;
    } else {
      capacityAlert.style.display = "none";
      capacityAlert.textContent = "";
    }
  }

  // ticket display
  const typeEl = $("evTicketType");
  const pricePill = $("evTicketPricePill");
  const lineEl = $("evTicketPriceLine");
  const linkEl = $("evTicketLink");

  const legalBoxEl = $("evTicketLegalBox");

  if (ev.paidMode === "free") {
    if (typeEl) typeEl.textContent = t("eventDetail.ticketFree");
    if (pricePill) pricePill.textContent = "0 zł";
    if (lineEl) lineEl.textContent = "";
    if (linkEl) {
      linkEl.href = "#";
      linkEl.style.display = "none";
    }
    if (legalBoxEl) legalBoxEl.style.display = "none";
  } else if (ev.paidMode === "paid_fixed") {
    if (typeEl) typeEl.textContent = t("eventDetail.ticketFixed");
    if (pricePill) pricePill.textContent = `${ev.price} zł`;
    if (lineEl) lineEl.textContent = t("eventDetail.priceLine", { price: ev.price });
    if (linkEl) {
      linkEl.href = ev.ticketLink || "#";
      linkEl.style.display = "";
    }
    if (legalBoxEl) legalBoxEl.style.display = "";
  } else {
    if (typeEl) typeEl.textContent = t("eventDetail.ticketRange");
    if (pricePill) pricePill.textContent = `${ev.priceFrom}–${ev.priceTo} zł`;
    if (lineEl) lineEl.textContent = t("eventDetail.priceRangeLine", { from: ev.priceFrom, to: ev.priceTo });
    if (linkEl) {
      linkEl.href = ev.ticketLink || "#";
      linkEl.style.display = "";
    }
    if (legalBoxEl) legalBoxEl.style.display = "";
  }

  // Badge (plan)
  safeSetText("evBadge", App.user.plan.toUpperCase());

  go("S7B_EVENT_DETAIL");
  safeSetText(
    "evPlaceMeta",
    ev.address || ev.where || ev.city || (hasEventCoords ? t("eventDetail.locationSaved") : t("eventDetail.locationMissing"))
  );
  syncEventDetailButtons();
}


function formatIcsDate(dateValue) {
  const d = new Date(dateValue);
  if (Number.isNaN(d.getTime())) return "";
  return d.toISOString().replace(/[-:]/g, "").replace(/\.\d{3}Z$/, "Z");
}

function escapeIcsText(value = "") {
  return String(value)
    .replace(/\\/g, "\\\\")
    .replace(/\n/g, "\\n")
    .replace(/,/g, "\\,")
    .replace(/;/g, "\\;");
}

async function addSelectedEventToCalendar() {
  const ev = App.events.find(e => String(e.id) === String(App.selectedEventId));
  if (!ev) return;

  if (!ev.start_at) {
    toast(t("eventDetail.noDateToast"));
    return;
  }

  const startDate = new Date(ev.start_at);
  const endDate = new Date(ev.end_at || new Date(startDate.getTime() + 60 * 60 * 1000));

  const location = [ev.where, ev.address, ev.city].filter(Boolean).join(", ");
  const description = [
    ev.desc || "",
    "",
    ev.organizer?.name ? `Organizator: ${ev.organizer.name}` : "",
    t("eventDetail.calendarDesc")
  ].filter(Boolean).join("\n");

  const CapacitorCalendar = window.Capacitor?.Plugins?.CapacitorCalendar;
  if (IS_CAPACITOR_APP && CapacitorCalendar?.createEventWithPrompt) {
    try {
      await CapacitorCalendar.createEventWithPrompt({
        title: ev.title || t("eventDetail.defaultSummary"),
        location,
        startDate: startDate.getTime(),
        endDate: endDate.getTime(),
        isAllDay: false,
        description,
        url: `https://uslyapp.pl/app?event=${encodeURIComponent(ev.id)}`
      });
      toast(t("eventDetail.calendarNativeOpened"));
      return;
    } catch (err) {
      console.warn("USLY native calendar failed, falling back to ICS", err);
    }
  }

  const start = formatIcsDate(startDate);
  const end = formatIcsDate(endDate);

  const ics = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//USLY//Events//PL",
    "CALSCALE:GREGORIAN",
    "METHOD:PUBLISH",
    "BEGIN:VEVENT",
    `UID:usly-event-${escapeIcsText(ev.id)}@uslyapp.pl`,
    `DTSTAMP:${formatIcsDate(new Date())}`,
    `DTSTART:${start}`,
    `DTEND:${end}`,
    `SUMMARY:${escapeIcsText(ev.title || t("eventDetail.defaultSummary"))}`,
    `LOCATION:${escapeIcsText(location)}`,
    `DESCRIPTION:${escapeIcsText(description)}`,
    "END:VEVENT",
    "END:VCALENDAR"
  ].join("\r\n");

  const blob = new Blob([ics], { type: "text/calendar;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  const safeName = String(ev.title || "wydarzenie-usly").toLowerCase().replace(/[^a-z0-9ąćęłńóśźż]+/gi, "-").replace(/^-+|-+$/g, "") || "wydarzenie-usly";

  a.href = url;
  a.download = `${safeName}.ics`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);

  toast(t("eventDetail.calendarDownloaded"));
}

async function toggleSaveEvent() {
  const ev = App.events.find(e => String(e.id) === String(App.selectedEventId));
  if (!ev) return;

  try {
    if (ev.saved) {
      const res = await apiFetch(`/events/${ev.id}/save`, {
        method: "DELETE",
      });
      if (!res?.success) {
        toast(res?.error?.message || t("eventDetail.saveRemoveFailed"));
        return;
      }
      toast(t("eventDetail.saveRemoved"));
    } else {
      const res = await apiFetch(`/events/${ev.id}/save`, {
        method: "POST",
      });
      if (!res?.success) {
        toast(res?.error?.message || t("eventDetail.saveAddFailed"));
        return;
      }
      toast(t("eventDetail.saveAdded"));
    }

    await loadEvents();

    const fresh = App.events.find(e => String(e.id) === String(App.selectedEventId));
    if (fresh) {
      openEvent(fresh.id);
      syncEventDetailButtons();
    } else {
      renderEventsList();
      renderNearby();
    }
  } catch (err) {
    toast(err?.userMessage || t("eventDetail.saveToggleFailed"));
  }
}

async function toggleInterestedEvent() {
  const ev = App.events.find(e => String(e.id) === String(App.selectedEventId));
  if (!ev) return;

  try {
    if (ev.interested) {
      const res = await apiFetch(`/events/${ev.id}/join`, {
        method: "DELETE",
      });
      if (!res?.success) {
        toast(res?.error?.message || t("eventDetail.joinRemoveFailed"));
        return;
      }
      toast(t("eventDetail.joinRemoved"));
    } else {
      const res = await apiFetch(`/events/${ev.id}/join`, {
        method: "POST",
      });
      if (!res?.success) {
        toast(res?.error?.message || t("eventDetail.joinAddFailed"));
        return;
      }
      toast(t("eventDetail.joinAdded"));
    }

    await loadEvents();

    const fresh = App.events.find(e => String(e.id) === String(App.selectedEventId));
    if (fresh) {
      openEvent(fresh.id);
      syncEventDetailButtons();
    } else {
      renderEventsList();
      renderNearby();
    }
  } catch (err) {
    toast(err?.userMessage || t("eventDetail.joinToggleFailed"));
  }
}

function getSelectedEventShareUrl() {
  const eventId = App.selectedEventId ? encodeURIComponent(String(App.selectedEventId)) : "";
  return eventId ? `https://uslyapp.pl/app?event=${eventId}` : "https://uslyapp.pl/app";
}

async function copySelectedEventLink() {
  const url = getSelectedEventShareUrl();

  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(url);
    } else {
      const input = document.createElement("input");
      input.value = url;
      document.body.appendChild(input);
      input.select();
      document.execCommand("copy");
      input.remove();
    }

    toast(t("eventDetail.copyToast"));
    closeModal();
  } catch (err) {
    toast(t("eventDetail.copyFailed"));
  }
}

function openShare() {
  openModal(t("eventDetail.shareTitle"), `
    <div class="tStrong">${t("eventDetail.shareHeading")}</div>
    <div class="sectionSub mt10">${t("eventDetail.shareSub")}</div>
    <button class="btn mt16" type="button" onclick="copySelectedEventLink()">${t("eventDetail.copyLink")}</button>
  `);
}


function openEventReportModal() {
  const eventId = App.selectedEventId;

  if (!eventId) {
    toast(t("eventReport.noEvent"));
    return;
  }

  openModal(t("eventReport.modalTitle"), `
    <div data-hide-modal-footer="1" style="display:none;"></div>

    <div class="tStrong">${t("eventReport.reasonTitle")}</div>

    <select id="eventReportReason" class="input mt8">
      <option value="">${t("eventReport.chooseReason")}</option>
      <option value="spam">${t("eventReport.reasonSpam")}</option>
      <option value="misleading">${t("eventReport.reasonMisleading")}</option>
      <option value="inappropriate">${t("eventReport.reasonInappropriate")}</option>
      <option value="unsafe">${t("eventReport.reasonUnsafe")}</option>
      <option value="other">${t("eventReport.reasonOther")}</option>
    </select>

    <textarea id="eventReportDesc" class="mt12" maxlength="1000"
      placeholder="${t("eventReport.descriptionPlaceholder")}"></textarea>

    <div class="row mt16">
      <button class="btn" type="button" onclick="submitEventReport()">${t("eventReport.submit")}</button>
      <button class="btn secondary" type="button" onclick="closeModal()">${t("groups.create.cancel")}</button>
    </div>
  `);
}

async function submitEventReport() {
  const eventId = App.selectedEventId;
  const reason = $("eventReportReason")?.value;
  const description = $("eventReportDesc")?.value || "";

  if (!reason) {
    toast(t("eventReport.toastNoReason"));
    return;
  }

  try {
    const res = await apiFetch("/reports/event", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        event_id: Number(eventId),
        reason,
        description,
        current_view: App.currentView || "unknown",
      }),
    });

    if (!res?.success) {
      toast(res?.error?.message || t("eventReport.toastFailed"));
      return;
    }

    toast(t("eventReport.toastSent", { ticket: res.data.ticket }));
    closeModal();

  } catch (e) {
    toast(t("eventReport.toastConnection"));
  }
}

function openEventMenu() {
  openModal(t("eventMenu.title"), `
    <button class="btn secondary" type="button" onclick="openEventReportModal();">${t("eventMenu.report")}</button>
    <button class="btn danger mt12" type="button" onclick="toast(t('eventMenu.hideSoon')); closeModal();">${t("eventMenu.hide")}</button>
  `);
}

function openEventOrganizerProfile() {
  const ev = App.events.find(e => String(e.id) === String(App.selectedEventId));
  if (!ev || !ev.organizer?.id) return;

  const organizerId = String(ev.organizer.id);
  const organizerName = ev.organizer.name || "Organizator";

  let chat = App.chats.find(c => String(c.with?.id) === organizerId);
  if (!chat) {
    chat = {
      id: `c_org_${organizerId}`,
      with: {
        id: organizerId,
        nick: organizerName,
        role: "partner",
        company: organizerName,
        city: ev.organizer?.city || ev.city || "",
        category: ev.organizer?.category || ev.category || "",
        bio: ev.organizer?.bio || "",
        avatarUrl: ev.organizer?.logoUrl || "",
        logoUrl: ev.organizer?.logoUrl || "",
        emoji: "",
      },
      last: "",
      unread: 0,
      messages: [],
    };
    App.chats.unshift(chat);
  } else {
    chat.with = {
      ...(chat.with || {}),
      id: organizerId,
      nick: chat.with?.nick || organizerName,
      role: "partner",
      company: chat.with?.company || organizerName,
      city: chat.with?.city || ev.city || "",
      category: chat.with?.category || ev.organizer?.category || ev.category || "",
      bio: chat.with?.bio || ev.organizer?.bio || "",
      avatarUrl: chat.with?.avatarUrl || ev.organizer?.logoUrl || "",
      logoUrl: chat.with?.logoUrl || ev.organizer?.logoUrl || chat.with?.avatarUrl || "",
      emoji: chat.with?.emoji || "",
    };
  }

  openPerson(organizerId);
}

function openChatWithOrganizer() {
  const ev = App.events.find(e => String(e.id) === String(App.selectedEventId));
  if (!ev || !ev.organizer?.id) return;

  const organizerId = String(ev.organizer.id);
  const organizerName = ev.organizer.name || "Organizator";

  let chat = App.chats.find(c => String(c.with?.id) === organizerId);
  if (!chat) {
    chat = {
      id: `c_org_${organizerId}`,
      with: {
        id: organizerId,
        nick: organizerName,
        role: "partner",
        company: organizerName,
        city: ev.city || "",
        category: ev.organizer?.category || ev.category || "",
        bio: ev.organizer?.bio || "",
        avatarUrl: ev.organizer?.logoUrl || "",
        logoUrl: ev.organizer?.logoUrl || "",
        emoji: "",
      },
      last: "",
      unread: 0,
      messages: [],
    };
    App.chats.unshift(chat);
  } else {
    chat.with = {
      ...(chat.with || {}),
      id: organizerId,
      nick: chat.with?.nick || organizerName,
      role: "partner",
      company: chat.with?.company || organizerName,
      city: chat.with?.city || ev.city || "",
      category: chat.with?.category || ev.organizer?.category || ev.category || "",
      bio: chat.with?.bio || ev.organizer?.bio || "",
      avatarUrl: chat.with?.avatarUrl || ev.organizer?.logoUrl || "",
      logoUrl: chat.with?.logoUrl || ev.organizer?.logoUrl || chat.with?.avatarUrl || "",
      emoji: chat.with?.emoji || "",
    };
  }

  App.selectedChatId = chat.id;
  App.selectedChatUserId = organizerId;
  openChat(chat.id);
}

/* ------------------------- Groups -------------------------- */
async function openGroup(groupId) {
  const allGroups = [...(App.myGroups || []), ...(App.groups || [])];
  const g = allGroups.find(x => String(x.id) === String(groupId));
  if (!g) return;
  App.selectedGroupId = groupId;

  const inviteBtn = $("btnInviteFriendToGroup");
  const inviteHook = $("groupInviteHook");
  const canInvite = canInviteFriendsToGroup();
  const inGroup = isUserInGroup(groupId);

  if (inviteBtn) {
    inviteBtn.disabled = !canInvite;
    inviteBtn.textContent = canInvite ? t("groupPeople.addFriend") : t("groupPeople.availablePremium");
  }

  if (inviteHook) {
    inviteHook.style.opacity = canInvite ? "1" : "0.72";
  }

  safeSetText("groupTitle", g.title);
  safeSetText("groupTagline", g.interestTag ? `#${g.interestTag}` : "");

  const joinCta = $("groupJoinCta");
  const input = $("groupInput");
  const inputDock = $("groupInputDock");

  if (joinCta) {
    joinCta.innerHTML = "";
  }

  if (inputDock) {
    inputDock.innerHTML = inGroup
      ? `
          <input id="groupInput" type="text" placeholder="${t("groupThread.placeholder")}" />
          <button class="btn small" id="groupSendBtn" type="button" onclick="sendGroup()" aria-label="${t("groupThread.sendAria")}">➜</button>
        `
      : `
          <button class="btn" type="button" style="width:100%;" onclick="joinGroup('${groupId}')">
            ${t("groupThread.join")}
          </button>
        `;
  }

  const currentInput = $("groupInput");
  const currentSendBtn = $("groupSendBtn");

  if (currentInput) {
    currentInput.disabled = false;
    currentInput.value = "";
    currentInput.placeholder = t("groupThread.placeholder");
  }
  if (currentSendBtn) {
    currentSendBtn.disabled = false;
    currentSendBtn.style.opacity = "1";
    currentSendBtn.style.cursor = "pointer";
  }

  bindMessageInputs();

  try {
    const peopleRes = await apiFetch(`/groups/${groupId}/people`);
    const peopleData = peopleRes?.data || peopleRes || {};
    window._lastGroupPeople = {
      members: Array.isArray(peopleData.members) ? peopleData.members : [],
      invited: Array.isArray(peopleData.invited) ? peopleData.invited : [],
    };
  } catch (err) {
    console.error("group people preload failed", err);
  }

  // messages
  const box = $("groupBubbles");
  if (box) {
    if (!inGroup) {
      box.innerHTML = `
        <div style="padding:16px;">
          <div class="tStrong">${g.title}</div>
          <div class="sectionSub" style="margin-top:6px;">
            ${g.desc || t("groupThread.defaultDesc")}
          </div>
          <div class="tMuted" style="margin-top:12px;">
            ${t("groupThread.join")}, aby zobaczyć rozmowę i napisać wiadomość.
          </div>
        `;
      go("S8B_GROUP_THREAD");
      return;
    }

    box.innerHTML = `<div class="tMuted" style="padding:16px; text-align:center;">${t("groupThread.loading")}</div>`;
    const seenAt = parseUslyTimestamp(readGroupSeenMap()[String(groupId)]);

    try {
      const data = await apiFetch(`/messages/group/${groupId}`);
      const items = Array.isArray(data?.data?.items) ? data.data.items : [];

      const savedBlockedGroupMessages = loadBlockedGroupMessages(groupId);
      const localPendingGroupMessages = (openGroup.__localPending || [])
        .filter(m => String(m.groupId || "") === String(groupId));

      const timelineItems = [
        ...items.map(m => ({
          kind: "remote",
          from: String(m.sender_user_id) === String(App.currentUserId) ? "me" : "them",
          text: m.content || "",
          senderUserId: m.sender_user_id,
          createdAt: m.created_at || null,
          isRead: !!m.is_read,
        })),
        ...savedBlockedGroupMessages.map(m => ({
          kind: "local",
          from: "me",
          text: m.text || "",
          senderUserId: App.currentUserId,
          createdAt: m.createdAt || null,
          isRead: false,
          pending: false,
          blockedReason: normalizeBlockedReason(m.blockedReason, "chat.blocked.content"),
        })),
        ...localPendingGroupMessages.map(m => ({
          kind: "local",
          from: "me",
          text: m.text || "",
          senderUserId: App.currentUserId,
          createdAt: m.createdAt || null,
          isRead: false,
          pending: m.state === "pending",
          blockedReason: "",
        })),
      ].sort((a, b) => {
        const at = parseUslyTimestamp(a.createdAt) || 0;
        const bt = parseUslyTimestamp(b.createdAt) || 0;
        return at - bt;
      });

      if (!timelineItems.length) {
        box.innerHTML = `
          <div class="tMuted" style="padding:16px; text-align:center;">
            ${t("groupThread.empty")}
          </div>
        `;
      } else {
        let newDividerInserted = false;
        box.innerHTML = timelineItems.map(m => {
          const from = m.from;
          const isLocal = m.kind === "local";
          const isBlocked = !!m.blockedReason;
          const isPending = !!m.pending;
          const person = isLocal ? null : resolvePersonById(m.senderUserId);
          const ts = parseUslyTimestamp(m.createdAt);
          const isNewForCurrentUser = !newDividerInserted && from !== "me" && ts > seenAt;
          const timeLabel = ts
            ? new Date(ts).toLocaleString("pl-PL", {
                day: "2-digit",
                month: "2-digit",
                hour: "2-digit",
                minute: "2-digit",
              })
            : "";

          const avatarHtml = person?.avatarUrl
            ? `<img src="${String(person.avatarUrl).startsWith("http") ? person.avatarUrl : `${API_BASE_URL}${person.avatarUrl}`}" alt="${escapeHtml(person.nick || t("chat.defaultUser"))}" style="width:100%;height:100%;object-fit:cover;border-radius:999px;" />`
            : `<div class="userAvatarFallback" style="${premiumAvatarStyle(getAvatarGradient(person?.nick || "U"))}" data-name="${escapeHtml(person?.nick || "U")}">${avatarInitial(person?.nick || "U")}</div>`;

          const avatarButton = `
            <button
              type="button"
              onclick="openPerson('${String(m.senderUserId)}')"
              title="${t("chat.openProfile")}"
              style="width:32px;height:32px;min-width:32px;border-radius:999px;border:${from === "me" ? "0" : "1px solid rgba(16,24,40,0.08)"};padding:0;display:inline-flex;align-items:center;justify-content:center;background:#f2f4f7;overflow:hidden;box-shadow:${from === "me" ? "none" : "0 2px 8px rgba(16,24,40,0.08)"};cursor:pointer;flex-shrink:0;"
            >${avatarHtml}</button>
          `;

          const senderLabel = from === "me" ? t("groupThread.me") : escapeHtml(person?.nick || t("friends.defaultUser", { id: String(m.senderUserId) }));
          const dividerHtml = isNewForCurrentUser
            ? `<div style="display:flex;align-items:center;gap:10px;margin:18px 0 10px;"><div style="flex:1;height:1px;background:rgba(255,255,255,.10);"></div><div class="sectionSub" style="white-space:nowrap;">${t("groupThread.newMessages")}</div><div style="flex:1;height:1px;background:rgba(255,255,255,.10);"></div></div>`
            : ``;

          if (isNewForCurrentUser) newDividerInserted = true;

          const contentHtml = isBlocked
            ? `⚠️ ${escapeHtml(m.blockedReason)}`
            : `${escapeHtml(m.text || "")}${isPending ? `<div style="margin-top:6px;font-size:11px;opacity:.72;">${t("chat.checkingContent")}</div>` : ""}`;

          return `
            ${dividerHtml}
            <div style="display:flex; align-items:flex-end; gap:10px; justify-content:${from === "me" ? "flex-end" : "flex-start"}; margin:10px 0;">
              ${from === "me" ? "" : avatarButton}
              <div class="bubble ${from === "me" ? "me" : "them"}" style="max-width:78%; word-break:break-word; opacity:${isBlocked ? ".58" : isPending ? ".72" : "1"}; ${isBlocked ? "background:rgba(120,120,120,.14);border:1px dashed rgba(255,120,120,.45);" : ""}">
                <div style="font-size:12px; opacity:.72; margin-bottom:4px; font-weight:800;">${senderLabel}</div>
                <div style="line-height:1.45;">${contentHtml}</div>
                ${timeLabel ? `<div style="font-size:11px; opacity:.65; text-align:right; margin-top:6px;">${escapeHtml(timeLabel)}</div>` : ``}
              </div>
              ${from === "me" ? avatarButton : ""}
            </div>
          `;
        }).join("");

        markGroupAsSeen(groupId);

        setTimeout(() => {
          box.parentElement?.scrollTo({ top: box.parentElement.scrollHeight, behavior: "auto" });
        }, 0);
      }
    } catch (err) {
      console.error("load group messages failed", err);
      box.innerHTML = `<div class="tMuted" style="padding:16px; text-align:center;">${t("groupThread.loadFailed")}</div>`;
    }
  }

  go("S8B_GROUP_THREAD");
}


function getBlockedGroupMessagesKey(groupId = App.selectedGroupId) {
  return `usly_blocked_group_messages_${App.currentUserId || "guest"}_${String(groupId || "unknown")}`;
}

function loadBlockedGroupMessages(groupId = App.selectedGroupId) {
  try {
    return JSON.parse(localStorage.getItem(getBlockedGroupMessagesKey(groupId)) || "[]");
  } catch (_) {
    return [];
  }
}

function saveBlockedGroupMessages(groupId, items) {
  try {
    localStorage.setItem(getBlockedGroupMessagesKey(groupId), JSON.stringify((items || []).slice(-30)));
  } catch (_) {}
}


function bindMessageInputs() {
  const chatInput = $("chatInput");
  const chatSendBtn = $("chatSendBtn");
  if (chatSendBtn && !chatSendBtn.dataset.bound) {
    chatSendBtn.addEventListener("click", sendChat);
    chatSendBtn.dataset.bound = "1";
  }
  if (chatInput && !chatInput.dataset.bound) {
    chatInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        sendChat();
      }
    });
    chatInput.dataset.bound = "1";
  }

  const groupInput = $("groupInput");
  const groupSendBtn = $("groupSendBtn");
  if (groupSendBtn && !groupSendBtn.dataset.bound) {
    groupSendBtn.addEventListener("click", sendGroup);
    groupSendBtn.dataset.bound = "1";
  }
  if (groupInput && !groupInput.dataset.bound) {
    groupInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        sendGroup();
      }
    });
    groupInput.dataset.bound = "1";
  }
}

async function sendGroup() {
  if (sendGroup.__busy) return;
  sendGroup.__busy = true;
  const groupId = App.selectedGroupId;
  if (!isUserInGroup(groupId)) {
    toast(t("groupThread.joinToWrite"));
    sendGroup.__busy = false;
    return;
  }

  const inp = $("groupInput");
  const sendBtn = $("groupSendBtn");
  const text = inp?.value?.trim();
  if (!text) {
    sendGroup.__busy = false;
    return;
  }

  if (sendBtn) sendBtn.disabled = true;
  if (inp) inp.value = "";

  const pendingId = `group-pending-${Date.now()}`;
  const localCreatedAt = new Date().toISOString();
  openGroup.__localPending = openGroup.__localPending || [];
  openGroup.__localPending.push({ id: pendingId, text, state: "pending", groupId: String(groupId), createdAt: localCreatedAt });
  await openGroup(groupId);

  try {
    const res = await apiFetch("/messages/group", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        group_id: Number(groupId),
        content: text,
      }),
    });

    if (!res?.success) {
      throw new Error(res?.error?.message || t("chat.toast.sendFailed"));
    }

    openGroup.__localPending = (openGroup.__localPending || []).filter(m => m.id !== pendingId);
    await openGroup(groupId);
  } catch (err) {
    console.error("sendGroup failed", err);

    const rawMessage = String(err?.userMessage || err?.message || err?.detail || "");
    const rawStatus = String(err?.status || err?.statusCode || err?.response?.status || "");
    const isModerated =
      rawStatus === "422" ||
      rawMessage.includes("message_blocked") ||
      rawMessage.includes("message_empty") ||
      rawMessage.includes("422") ||
      rawMessage.toLowerCase().includes("moderac");

    const blockedReason = rawMessage.includes("message_blocked_link")
      ? t("chat.blocked.link")
      : t("chat.blocked.content");

    const blockedItem = {
      id: pendingId,
      text,
      state: "blocked",
      blockedReason,
      groupId: String(groupId),
      createdAt: localCreatedAt,
    };

    openGroup.__localPending = (openGroup.__localPending || []).filter(m => m.id !== pendingId);

    const savedBlocked = loadBlockedGroupMessages(groupId);
    saveBlockedGroupMessages(groupId, [...savedBlocked, blockedItem]);

    await openGroup(groupId);

    if (!isModerated) {
      toast(err?.userMessage || t("chat.toast.sendFailed"));
    }
  } finally {
    sendGroup.__busy = false;
    if (sendBtn) sendBtn.disabled = false;
  }
}


/* ------------------------- Groups API -------------------------- */
async function joinGroup(groupId) {
  try {
    if (!canJoinMoreGroups()) {
      toast(t("groupThread.limitReached"));
      return;
    }

    const res = await apiFetch(`/groups/${groupId}/join`, {
      method: "POST"
    });

    if (res?.success) {
      await loadMyGroups();
      toast(t("groups.toast.joined"));
      renderAll();
      openGroup(groupId);
    } else {
      toast(t("groups.toast.joinFailed"));
    }

  } catch (err) {
    console.error("joinGroup failed", err);
    toast(t("groups.toast.joinConnectionFailed"));
  }
}


async function closeGroup(groupId) {
  try {
    const res = await apiFetch(`/groups/${groupId}/close`, {
      method: "POST"
    });

    if (res?.success) {
      await loadMyGroups();
      toast(t("groups.toast.closed"));
      App.selectedGroupId = null;
      renderAll();
    } else {
      toast(t("groups.toast.closeFailed"));
    }

  } catch (err) {
    console.error("closeGroup failed", err);
    toast(err?.userMessage || t("groups.toast.closeConnectionFailed"));
  }
}


async function leaveGroup(groupId) {
  try {

    const res = await apiFetch(`/groups/${groupId}/leave`, {
      method: "POST"
    });

    if (res?.success) {
      await loadMyGroups();
      toast(t("groups.toast.left"));
      renderAll();
    } else {
      toast(t("groups.toast.leaveFailed"));
    }

  } catch (err) {
    console.error("leaveGroup failed", err);
    toast(err?.userMessage || t("groups.toast.leaveConnectionFailed"));
  }
}
function openGroupMenu() {
  const groupId = App.selectedGroupId;
  const inGroup = isUserInGroup(groupId);
  const canInvite = canInviteFriendsToGroup();
  const allGroups = [...(App.myGroups || []), ...(App.groups || [])];
  const g = allGroups.find(x => String(x.id) === String(groupId));
  const isCreator = !!g?.isCreator;
  const isMuted = isGroupMuted(groupId);

  openModal(t("groups.menu.title"), `
    <button class="btn secondary" type="button" onclick="setGroupMuted('${groupId}', ${isMuted ? "false" : "true"}); closeModal(); renderGroups(); refreshGroupBadgeCount(); toast('${isMuted ? t("groups.toast.notificationsOn") : t("groups.toast.notificationsMuted")}');">
      ${isMuted ? t("groups.menu.notificationsOn") : t("groups.menu.notificationsOff")}
    </button>

    <button class="btn secondary mt12" type="button"
             onclick="closeModal(); openGroupPeopleScreen();">
             ${t("groups.menu.people")}
           </button>

    ${
      inGroup && isCreator
        ? `<button class="btn danger mt12" type="button"
             onclick="closeGroup('${groupId}'); closeModal();">
             ${t("groups.menu.close")}
           </button>`
        : inGroup
          ? `<button class="btn danger mt12" type="button"
               onclick="leaveGroup('${groupId}'); closeModal();">
               ${t("groups.menu.leave")}
             </button>`
          : ``
    }
  `);
}

// Punkt 9: dodanie znajomego do grupy, nawet jeśli jej nie widzi

async function inviteFriendToSelectedGroup(userId) {
  const groupId = App.selectedGroupId;
  if (!groupId || !userId) {
    toast(t("groups.toast.inviteMissing"));
    return;
  }

  try {
    const res = await apiFetch(`/groups/${groupId}/invite`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ invitee_user_id: Number(userId) }),
    });

    if (res?.success) {
      toast(t("groups.toast.inviteSent"));
      await refreshProfileRelations();
      if (App.currentView === "S12_NOTIFICATIONS") await renderNotifications();
      closeModal();
    } else {
      toast(t("groups.toast.inviteFailed"));
    }
  } catch (err) {
    console.error("inviteFriendToSelectedGroup failed", err);
    toast(err?.userMessage || t("groups.toast.inviteFailed"));
  }
}


async function openGroupPeopleScreen() {
  App.groupInviteTab = App.groupInviteTab || "invite";
  const canInvite = canInviteFriendsToGroup();
  if (!canInvite && App.groupInviteTab === "invite") {
    App.groupInviteTab = "members";
  }

  if (!window._lastFriendsList || window._lastFriendsList.length === 0) {
    try {
      await refreshProfileRelations();
    } catch (_) {}
  }

  const allGroups = [...(App.myGroups || []), ...(App.groups || [])];
  const g = allGroups.find(x => String(x.id) === String(App.selectedGroupId));
  if (!g) return;

  safeSetText("groupPeopleTitle", t("groups.menu.people"));
  safeSetText("groupPeopleTagline", g.title ? `${g.title}${g.interestTag ? ` • #${g.interestTag}` : ""}` : (g.interestTag ? `#${g.interestTag}` : ""));

  let groupPeople = { members: [], invited: [] };
  try {
    const peopleRes = await apiFetch(`/groups/${g.id}/people`);
    const peopleData = peopleRes?.data || peopleRes || {};
    groupPeople = {
      members: Array.isArray(peopleData.members) ? peopleData.members : [],
      invited: Array.isArray(peopleData.invited) ? peopleData.invited : [],
    };
    window._lastGroupPeople = groupPeople;
  } catch (err) {
    console.error("group people load failed", err);
  }

  const allFriends = (window._lastFriendsList || []);
  const memberIds = new Set((groupPeople.members || []).map(x => String(x.id)));
  const invitedIds = new Set((groupPeople.invited || []).map(x => String(x.id)));
  const myId = String(App.currentUserId || "");
  const tag = String(g.interestTag || "").toLowerCase();

  const similarFriends = allFriends
    .filter(f => {
      const id = String(f.id || "");
      if (!Array.isArray(f.interests)) return false;
      if (!f.interests.map(x => x.toLowerCase()).includes(tag)) return false;
      if (!id || id === myId) return false;
      if (memberIds.has(id)) return false;
      if (invitedIds.has(id)) return false;
      return true;
    })
    .slice(0, 24);

  const members = Array.isArray(groupPeople.members) ? [...groupPeople.members] : [];
  members.sort((a, b) => {
    if (!!a.is_founder !== !!b.is_founder) return a.is_founder ? -1 : 1;
    return String(a.nick || "").localeCompare(String(b.nick || ""), "pl", { sensitivity: "base" });
  });

  const invited = Array.isArray(groupPeople.invited) ? [...groupPeople.invited] : [];
  invited.sort((a, b) => String(a.nick || "").localeCompare(String(b.nick || ""), "pl", { sensitivity: "base" }));

  const inviteHtml = similarFriends.map(p => `
        <div class="listItem groupPeopleRow" style="margin-bottom:10px; cursor:default;">
          <div class="groupPeopleMain">
            <div class="listAvatar">${p.avatarUrl ? `<img src="${String(p.avatarUrl).startsWith("http") ? p.avatarUrl : `${API_BASE_URL}${p.avatarUrl}`}" alt="${p.nick}" style="width:100%;height:100%;object-fit:cover;border-radius:inherit;" />` : p.emoji}</div>
            <div class="groupPeopleText">
              <div class="listTitle">${p.nick}</div>
              <div class="listMeta">${t("groupPeople.shared", { tags: commonInterests(p).slice(0,3).map(x => `#${x}`).join(" ") })}</div>
            </div>
          </div>
          <div class="groupPeopleAction">
            <button class="btn small" type="button" onclick="inviteFriendToSelectedGroup('${p.id}')">${t("groupPeople.invite")}</button>
          </div>
        </div>
      `).join("") || `<div class="tMuted">${t("groupPeople.emptyInvite")}</div>`;

  const membersHtml = members.map(p => `
        <div class="listItem groupPeopleRow" style="margin-bottom:10px; cursor:pointer;" onclick="${String(p.id) === myId ? "" : `openPerson('${String(p.id)}')`}">
          <div class="groupPeopleMain">
            <div class="listAvatar">${p.avatar_url ? `<img src="${String(p.avatar_url).startsWith("http") ? p.avatar_url : `${API_BASE_URL}${p.avatar_url}`}" alt="${p.nick}" style="width:100%;height:100%;object-fit:cover;border-radius:inherit;" />` : `<div class="userAvatarFallback" style="${premiumAvatarStyle(getAvatarGradient(p.nick || "U"))}" data-name="${escapeHtml(p.nick || "U")}">${avatarInitial(p.nick || "U")}</div>`}</div>
            <div class="groupPeopleText">
              <div class="listTitle">${p.nick}</div>
              <div class="listMeta">${p.city || t("groupPeople.memberFallback")}</div>
            </div>
          </div>
          <div class="groupPeopleAction">
            ${p.is_founder
              ? `<button class="btn secondary small" type="button" disabled>${t("groupPeople.founder")}</button>`
              : (String(p.id) === myId
                  ? `<button class="btn secondary small" type="button" disabled>${t("groupPeople.yourProfile")}</button>`
                  : `<button class="btn secondary small" type="button" onclick="event.stopPropagation(); openPerson('${String(p.id)}')">${t("groupPeople.viewProfile")}</button>`
                )
            }
          </div>
        </div>
      `).join("") || `<div class="tMuted">${t("groupPeople.emptyMembers")}</div>`;

  const invitedHtml = invited.map(p => `
        <div class="listItem groupPeopleRow" style="margin-bottom:10px; cursor:pointer;" onclick="openPerson('${String(p.id)}')">
          <div class="groupPeopleMain">
            <div class="listAvatar">${p.avatar_url ? `<img src="${String(p.avatar_url).startsWith("http") ? p.avatar_url : `${API_BASE_URL}${p.avatar_url}`}" alt="${p.nick}" style="width:100%;height:100%;object-fit:cover;border-radius:inherit;" />` : `<div class="userAvatarFallback" style="${premiumAvatarStyle(getAvatarGradient(p.nick || "U"))}" data-name="${escapeHtml(p.nick || "U")}">${avatarInitial(p.nick || "U")}</div>`}</div>
            <div class="groupPeopleText">
              <div class="listTitle">${p.nick}</div>
              <div class="listMeta">${p.city || t("groupPeople.invitePending")}</div>
            </div>
          </div>
          <div class="groupPeopleAction">
            <button class="btn secondary small" type="button" onclick="event.stopPropagation(); openPerson('${String(p.id)}')">${t("groupPeople.viewProfile")}</button>
          </div>
        </div>
      `).join("") || `<div class="tMuted">${t("groupPeople.emptyInvited")}</div>`;

  const activeHtml = App.groupInviteTab === "members"
    ? membersHtml
    : (App.groupInviteTab === "invited" ? invitedHtml : inviteHtml);

  const screen = $("groupPeopleScreen");
  if (screen) {
    const memberCount = members.length;
    const invitedCount = invited.length;
    const inviteCount = similarFriends.length;
    screen.innerHTML = `
      <div class="groupInviteModal">
        <div class="groupPeopleSummary">
          <div class="groupPeopleStat">
            <span>${memberCount}</span>
            <small>${t("groupPeople.membersTab")}</small>
          </div>
          <div class="groupPeopleStat">
            <span>${invitedCount}</span>
            <small>${t("groupPeople.invitedTab")}</small>
          </div>
          <div class="groupPeopleStat">
            <span>${canInvite ? inviteCount : 0}</span>
            <small>${t("groupPeople.inviteTab")}</small>
          </div>
        </div>

        ${canInvite ? "" : `<div class="groupPeopleNotice">${t("groupPeople.premiumOnly")}</div>`}

        <div class="segmented mt14">
          <button class="segBtn ${App.groupInviteTab === "invite" ? "on" : ""}" type="button" ${canInvite ? `onclick="App.groupInviteTab='invite'; openGroupPeopleScreen()"` : "disabled aria-disabled='true'"}>${t("groupPeople.inviteTab")}</button>
          <button class="segBtn ${App.groupInviteTab === "members" ? "on" : ""}" type="button" onclick="App.groupInviteTab='members'; openGroupPeopleScreen()">${t("groupPeople.membersTab")}</button>
          <button class="segBtn ${App.groupInviteTab === "invited" ? "on" : ""}" type="button" onclick="App.groupInviteTab='invited'; openGroupPeopleScreen()">${t("groupPeople.invitedTab")}</button>
        </div>

        <div class="mt14">
          ${activeHtml}
        </div>
      </div>
    `;
  }

  go("S8C_GROUP_PEOPLE");
}

async function openInviteFriendToGroup() {
  App.groupInviteTab = App.groupInviteTab || "invite";

  if (!window._lastFriendsList || window._lastFriendsList.length === 0) {
    try {
      await refreshProfileRelations();
    } catch (_) {}
  }

  const allGroups = [...(App.myGroups || []), ...(App.groups || [])];
  const g = allGroups.find(x => String(x.id) === String(App.selectedGroupId));
  if (!g) return;

  if (!canInviteFriendsToGroup()) {
    toast(t("groupPeople.toastPremium"));
    return;
  }

  let groupPeople = { members: [], invited: [] };
  try {
    const peopleRes = await apiFetch(`/groups/${g.id}/people`);
    const peopleData = peopleRes?.data || peopleRes || {};
    groupPeople = {
      members: Array.isArray(peopleData.members) ? peopleData.members : [],
      invited: Array.isArray(peopleData.invited) ? peopleData.invited : [],
    };
    window._lastGroupPeople = groupPeople;
  } catch (err) {
    console.error("group people load failed", err);
  }

  const allFriends = (window._lastFriendsList || []);
  const outgoingGroupInvites = Array.isArray(window._lastOutgoingGroupInvites) ? window._lastOutgoingGroupInvites : [];
  const pendingInviteUserIds = new Set(
    outgoingGroupInvites
      .filter(inv => String(inv?.group?.id || "") === String(g.id))
      .map(inv => String(inv?.user?.id || ""))
      .filter(Boolean)
  );
  const memberIds = new Set((groupPeople.members || []).map(x => String(x.id)));
  const invitedIds = new Set((groupPeople.invited || []).map(x => String(x.id)));
  const myId = String(App.user?.id || "");
  const tag = String(g.interestTag || "").toLowerCase();

  const similarFriends = allFriends
    .filter(f => {
      const id = String(f.id || "");
      if (!Array.isArray(f.interests)) return false;
      if (!f.interests.map(x => x.toLowerCase()).includes(tag)) return false;
      if (!id || id === myId) return false;
      if (memberIds.has(id)) return false;
      if (invitedIds.has(id)) return false;
      return true;
    })
    .slice(0, 6);

  const members = Array.isArray(groupPeople.members) ? [...groupPeople.members] : [];
  members.sort((a, b) => {
    if (!!a.is_founder !== !!b.is_founder) return a.is_founder ? -1 : 1;
    return String(a.nick || "").localeCompare(String(b.nick || ""), "pl", { sensitivity: "base" });
  });

  const invited = Array.isArray(groupPeople.invited) ? [...groupPeople.invited] : [];
  invited.sort((a, b) => String(a.nick || "").localeCompare(String(b.nick || ""), "pl", { sensitivity: "base" }));

  const inviteHtml = similarFriends.map(p => `
        <div class="listItem groupInviteCard" style="margin-bottom:10px; cursor:default;">
          <div class="groupInviteCardTop">
            <div class="listAvatar">${p.avatarUrl ? `<img src="${String(p.avatarUrl).startsWith("http") ? p.avatarUrl : `${API_BASE_URL}${p.avatarUrl}`}" alt="${p.nick}" style="width:100%;height:100%;object-fit:cover;border-radius:inherit;" />` : p.emoji}</div>
            <div class="groupInviteCardText">
              <div class="listTitle">${p.nick}</div>
              <div class="listMeta">${t("groupPeople.shared", { tags: commonInterests(p).slice(0,3).map(x => `#${x}`).join(" ") })}</div>
            </div>
          </div>
          <div class="groupInviteCardAction">
            <button class="btn small" type="button" onclick="inviteFriendToSelectedGroup('${p.id}')">${t("groupPeople.invite")}</button>
          </div>
        </div>
      `).join("") || `<div class="tMuted">${t("groupPeople.emptyInvite")}</div>`;

  const membersHtml = members.map(p => `
        <div class="listItem groupInviteCard" style="margin-bottom:10px; cursor:pointer;" onclick="openChatParticipantProfile('${String(p.id)}'); closeModal();">
          <div class="groupInviteCardTop">
            <div class="listAvatar">${p.avatar_url ? `<img src="${String(p.avatar_url).startsWith("http") ? p.avatar_url : `${API_BASE_URL}${p.avatar_url}`}" alt="${p.nick}" style="width:100%;height:100%;object-fit:cover;border-radius:inherit;" />` : `<div class="userAvatarFallback" style="${premiumAvatarStyle(getAvatarGradient(p.nick || "U"))}" data-name="${escapeHtml(p.nick || "U")}">${avatarInitial(p.nick || "U")}</div>`}</div>
            <div class="groupInviteCardText">
              <div class="listTitle">${p.nick}</div>
              <div class="listMeta">${p.city || t("groupPeople.memberFallback")}</div>
            </div>
          </div>
          <div class="groupInviteCardAction">
            ${p.is_founder
              ? `<button class="btn secondary small" type="button" disabled>${t("groupPeople.founder")}</button>`
              : `<button class="btn secondary small" type="button">${t("groupPeople.viewProfile")}</button>`
            }
          </div>
        </div>
      `).join("") || `<div class="tMuted">${t("groupPeople.emptyMembers")}</div>`;

  const invitedHtml = invited.map(p => `
        <div class="listItem groupInviteCard" style="margin-bottom:10px; cursor:default;">
          <div class="groupInviteCardTop">
            <div class="listAvatar">${p.avatar_url ? `<img src="${String(p.avatar_url).startsWith("http") ? p.avatar_url : `${API_BASE_URL}${p.avatar_url}`}" alt="${p.nick}" style="width:100%;height:100%;object-fit:cover;border-radius:inherit;" />` : `<div class="userAvatarFallback" style="${premiumAvatarStyle(getAvatarGradient(p.nick || "U"))}" data-name="${escapeHtml(p.nick || "U")}">${avatarInitial(p.nick || "U")}</div>`}</div>
            <div class="groupInviteCardText">
              <div class="listTitle">${p.nick}</div>
              <div class="listMeta">${p.city || t("groupPeople.invitePending")}</div>
            </div>
          </div>
          <div class="groupInviteCardAction">
            <button class="btn secondary small" type="button" disabled>${t("groupPeople.invitedTab")}</button>
          </div>
        </div>
      `).join("") || `<div class="tMuted">${t("groupPeople.emptyInvited")}</div>`;

  const activeHtml = App.groupInviteTab === "members"
    ? membersHtml
    : (App.groupInviteTab === "invited" ? invitedHtml : inviteHtml);

  openModal(t("groupPeople.inviteFriendModalTitle"), `
    <div class="groupInviteModal">
      <div class="tStrong">${t("groupPeople.pickFriend")}</div>
    <div class="sectionSub mt10">
      ${t("groupPeople.pickFriendSub")}
    </div>
    <div class="segmented mt12">
      <button class="segBtn ${App.groupInviteTab === "invite" ? "on" : ""}" type="button" onclick="App.groupInviteTab='invite'; openInviteFriendToGroup()">${t("groupPeople.inviteTab")}</button>
      <button class="segBtn ${App.groupInviteTab === "members" ? "on" : ""}" type="button" onclick="App.groupInviteTab='members'; openInviteFriendToGroup()">${t("groupPeople.membersTab")}</button>
      <button class="segBtn ${App.groupInviteTab === "invited" ? "on" : ""}" type="button" onclick="App.groupInviteTab='invited'; openInviteFriendToGroup()">${t("groupPeople.invitedTab")}</button>
    </div>
    <div class="mt16">
      ${activeHtml}
    </div>
    </div>
  `);
}

/* ------------------------- Organizer: create / events list -------------------------- */
function getPartnerEventSubmitBtn() {
  return document.querySelector('#S9_PARTNER_CREATE button[onclick="publishPartnerEvent()"]');
}

function syncPartnerPricingFields() {
  const paidMode = $("pePaidMode")?.value || "free";

  const priceInput = $("pePrice");
  const priceBox = priceInput?.parentElement;

  const priceFromInput = $("pePriceFrom");
  const priceFromBox = priceFromInput?.parentElement;

  const priceToInput = $("pePriceTo");
  const priceToLabel = priceToInput?.previousElementSibling;
  const ticketInput = $("peTicketLink");
  const ticketLabel = ticketInput?.previousElementSibling;

  const show = (el, display = "") => { if (el) el.style.display = display; };
  const hide = (el) => { if (el) el.style.display = "none"; };

  if (paidMode === "free") {
    hide(priceBox);
    hide(priceFromBox);
    hide(priceToLabel);
    hide(priceToInput);
    hide(ticketLabel);
    hide(ticketInput);

    if (priceInput) { priceInput.disabled = true; priceInput.required = false; priceInput.value = ""; }
    if (priceFromInput) { priceFromInput.disabled = true; priceFromInput.required = false; priceFromInput.value = ""; }
    if (priceToInput) { priceToInput.disabled = true; priceToInput.required = false; priceToInput.value = ""; }
    if (ticketInput) { ticketInput.disabled = true; ticketInput.required = false; ticketInput.value = ""; }
    return;
  }

  show(ticketLabel, "");
  show(ticketInput, "");
  if (ticketInput) { ticketInput.disabled = false; ticketInput.required = true; }

  if (paidMode === "paid_fixed") {
    show(priceBox, "");
    hide(priceFromBox);
    hide(priceToLabel);
    hide(priceToInput);

    if (priceInput) { priceInput.disabled = false; priceInput.required = true; }
    if (priceFromInput) { priceFromInput.disabled = true; priceFromInput.required = false; priceFromInput.value = ""; }
    if (priceToInput) { priceToInput.disabled = true; priceToInput.required = false; priceToInput.value = ""; }
    return;
  }

  hide(priceBox);
  show(priceFromBox, "");
  show(priceToLabel, "");
  show(priceToInput, "");

  if (priceInput) { priceInput.disabled = true; priceInput.required = false; priceInput.value = ""; }
  if (priceFromInput) { priceFromInput.disabled = false; priceFromInput.required = true; }
  if (priceToInput) { priceToInput.disabled = false; priceToInput.required = true; }
}

function syncPartnerCapacityFields() {
  const unlimited = $("peUnlimitedCapacity");
  const box = $("peCapacityBox");
  const input = $("peCapacity");
  if (!unlimited || !box || !input) return;

  if (unlimited.checked) {
    box.style.display = "none";
    input.disabled = true;
    input.required = false;
    input.value = "";
  } else {
    box.style.display = "block";
    input.disabled = false;
    input.required = true;
  }
}

function initPartnerPricingFields() {
  const mode = $("pePaidMode");
  if (mode && mode.dataset.bound !== "1") {
    mode.addEventListener("change", syncPartnerPricingFields);
    mode.dataset.bound = "1";
  }

  const unlimited = $("peUnlimitedCapacity");
  if (unlimited && unlimited.dataset.bound !== "1") {
    unlimited.addEventListener("change", syncPartnerCapacityFields);
    unlimited.dataset.bound = "1";
  }

  syncPartnerPricingFields();
  syncPartnerCapacityFields();
}

function syncPartnerEventSubmitBtn() {
  const btn = getPartnerEventSubmitBtn();
  const draftBtn = document.querySelector('#S9_PARTNER_CREATE button[onclick="savePartnerEventDraft()"]');
  const titleEl = document.querySelector('#S9_PARTNER_CREATE [data-i18n="partnerCreate.title"]');
  if (!btn) return;

  if (App.partnerEventFormMode === "published_edit") {
    btn.textContent = "Zaktualizuj wydarzenie";
    if (titleEl) titleEl.textContent = "Edytuj wydarzenie";
    if (draftBtn) draftBtn.style.display = "none";
    return;
  }

  if (App.partnerEventFormMode === "archived_edit") {
    btn.textContent = t("partnerCreate.resume");
    if (titleEl) titleEl.textContent = "Wznów wydarzenie";
    if (draftBtn) draftBtn.style.display = "none";
    return;
  }

  if (App.partnerEventFormMode === "draft_edit") {
    btn.textContent = t("partnerCreate.publishExisting");
    if (titleEl) titleEl.textContent = "Edytuj szkic";
    if (draftBtn) draftBtn.style.display = "";
    return;
  }

  if (draftBtn) draftBtn.style.display = "";
  if (titleEl) titleEl.textContent = t("partnerCreate.title");
  btn.textContent = t("partnerCreate.publish");
}

function resetPartnerEventFormMode() {
  App.selectedPartnerEventId = null;
  App.partnerEventFormMode = "create";
  syncPartnerEventSubmitBtn();
  const card = $("partnerEventParticipantsCard");
  const list = $("partnerEventParticipantsList");
  if (card) card.style.display = "none";
  if (list) list.innerHTML = "";
}

function clearPartnerEventForm() {
  resetPartnerEventFormMode();
  setPartnerEventInterestTags([]);
  renderPartnerEventInterestTags();
  ["peTitle","peCity","peWhen","peDate","peTime","peWhere","peAddress","peResolvedAddress","peLocationLat","peLocationLng","peInterest","peDesc","pePrice","pePriceFrom","pePriceTo","peTicketLink","peCapacity"].forEach(id => {
    const el = $(id);
    if (el) el.value = "";
  });
  const placeHint = $("peSelectedPlaceHint");
  if (placeHint) {
    placeHint.textContent = "";
    placeHint.hidden = true;
  }
  const placeResults = $("pePlaceResults");
  if (placeResults) placeResults.innerHTML = "";
  if ($("pePaidMode")) $("pePaidMode").value = "free";
  if ($("peUnlimitedCapacity")) $("peUnlimitedCapacity").checked = true;
  syncPartnerPricingFields();
  syncPartnerCapacityFields();
}

function openNewPartnerEventForm() {
  clearPartnerEventForm();
  go("S9_PARTNER_CREATE");
  setTimeout(renderPartnerEventInterestTags, 0);
}

async function renderPartnerEventParticipants() {
  const card = $("partnerEventParticipantsCard");
  const list = $("partnerEventParticipantsList");
  const broadcastBox = $("partnerEventBroadcastBox");
  if (!card || !list) return;

  const rules = getPartnerPlanRules();
  if (broadcastBox) {
    broadcastBox.style.display = rules.canBroadcastParticipants ? "block" : "none";
  }

  if (!App.selectedPartnerEventId) {
    card.style.display = "none";
    list.innerHTML = "";
    return;
  }

  card.style.display = "block";
  list.innerHTML = `<div class="tMuted">${t("partnerParticipants.loading")}</div>`;

  try {
    const data = await apiFetch(`/partners/events/${App.selectedPartnerEventId}/participants?limit=50`);
    const items = Array.isArray(data?.data?.items) ? data.data.items : [];

    if (!items.length) {
      list.innerHTML = `<div class="tMuted">${t("partnerParticipants.empty")}</div>`;
      return;
    }

    list.innerHTML = items.map(item => {
      const user = item?.user || {};
      const when = item?.signup?.created_at
        ? new Date(parseUslyTimestamp(item.signup.created_at)).toLocaleString("pl-PL")
        : "—";

      const canMessageParticipants = getPartnerPlanRules().canMessageParticipants;

      return `
        <div class="listItem">
          <div class="listTop">
            <div class="listLeft">
              <div class="listAvatar"><div class="userAvatarFallback" style="${premiumAvatarStyle(getAvatarGradient(user.nick || user.email || "U"))}" data-name="${escapeHtml(user.nick || user.email || "U")}">${avatarInitial(user.nick || user.email || "U")}</div></div>
              <div style="min-width:0;">
                <div class="listTitle">${user.nick || user.email || t("partnerParticipants.defaultUser", { id: user.id || "?" })}</div>
                <div class="listMeta">${t("partnerParticipants.signupLabel", { when })}</div>
              </div>
            </div>
            ${canMessageParticipants ? `
              <div class="listRight">
                <button class="btn secondary small" type="button" onclick="openPartnerParticipantMessageModal('${user.id}', '${(user.nick || user.email || '').replace(/'/g, "&apos;")}')">${t("partnerParticipants.write")}</button>
              </div>
            ` : ``}
          </div>
        </div>
      `;
    }).join("");
  } catch (err) {
    console.error("renderPartnerEventParticipants failed", err);
    list.innerHTML = `<div class="tMuted">${t("partnerParticipants.loadFailed")}</div>`;
  }
}

function openPartnerParticipantMessageModal(userId, userName) {
  const rules = getPartnerPlanRules();
  if (!rules.canMessageParticipants) {
    toast(t("partnerParticipants.messageLocked"));
    return;
  }

  openModal(t("partnerParticipants.modalTitle"), `
    <div class="sectionSub">${t("partnerParticipants.conversationWith")} <strong>${userName || t("partnerParticipants.defaultParticipant")}</strong></div>
    <textarea id="partnerParticipantMessageInput" class="mt12" maxlength="1000" placeholder="${t("partnerParticipantMessage.placeholder")}"></textarea>
    <div id="partnerParticipantMessageStatus" class="sectionSub mt10" style="display:none;"></div>
    <div class="row mt16">
      <button class="btn" type="button" onclick="sendPartnerParticipantMessage('${userId}')">${t("partnerParticipantMessage.send")}</button>
      <button class="btn secondary" type="button" onclick="closeModal()">${t("groups.create.cancel")}</button>
    </div>
  `);
}

async function sendPartnerParticipantMessage(userId) {
  if (sendPartnerParticipantMessage.__busy) return;

  const input = $("partnerParticipantMessageInput");
  const status = $("partnerParticipantMessageStatus");
  const sendBtn = document.querySelector('[onclick*="sendPartnerParticipantMessage"]');
  const text = input?.value?.trim();

  if (!text || !userId) return;

  sendPartnerParticipantMessage.__busy = true;

  if (status) {
    status.style.display = "block";
    status.style.opacity = ".82";
    status.style.border = "0";
    status.style.padding = "0";
    status.textContent = t("partnerParticipantMessage.checking");
  }
  if (input) input.disabled = true;
  if (sendBtn) sendBtn.disabled = true;

  try {
    await apiFetch("/messages/private", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        recipient_user_id: Number(userId),
        content: text,
      }),
    });

    closeModal();
    toast(t("partnerParticipants.sent"));
  } catch (err) {
    const rawMessage = String(err?.userMessage || err?.message || err?.detail || "");
    const rawStatus = String(err?.status || err?.statusCode || err?.response?.status || "");
    const isModerated =
      rawStatus === "422" ||
      rawMessage.includes("message_blocked") ||
      rawMessage.includes("message_empty") ||
      rawMessage.includes("422") ||
      rawMessage.toLowerCase().includes("moderac");

    const blockedReason = rawMessage.includes("message_blocked_link")
      ? t("partnerParticipantMessage.blockedLink")
      : t("partnerParticipantMessage.blockedContent");

    if (status && isModerated) {
      status.style.display = "block";
      status.style.opacity = ".72";
      status.style.border = "1px dashed rgba(255,120,120,.45)";
      status.style.borderRadius = "14px";
      status.style.padding = "10px 12px";
      status.textContent = `⚠️ ${blockedReason}`;
    } else {
      toast(err?.userMessage || t("chat.toast.sendFailed"));
      if (status) status.style.display = "none";
    }

    if (input) input.disabled = false;
  } finally {
    sendPartnerParticipantMessage.__busy = false;
    if (sendBtn) sendBtn.disabled = false;
  }
}

async function sendPartnerBroadcastMessage() {
  const rules = getPartnerPlanRules();
  if (!rules.canBroadcastParticipants) {
    toast(t("partnerBroadcast.locked"));
    return;
  }

  const input = $("partnerEventBroadcastInput");
  const btn = $("partnerEventBroadcastSendBtn");
  const text = input?.value?.trim();
  if (!text || !App.selectedPartnerEventId) return;

  const ev = (App.partnerEvents || []).find(x => String(x.id) === String(App.selectedPartnerEventId));
  const eventLabel = ev
    ? `${ev.title || t("personProfile.defaultEvent")}${ev.city ? `, ${ev.city}` : ""}`
    : t("personProfile.defaultEvent");

  try {
    if (btn) btn.disabled = true;

    const data = await apiFetch(`/partners/events/${App.selectedPartnerEventId}/participants?limit=100`);
    const items = Array.isArray(data?.data?.items) ? data.data.items : [];

    if (!items.length) {
      toast(t("partnerBroadcast.noParticipants"));
      return;
    }

    const content = `📣 ${ev?.title || t("personProfile.defaultEvent")}${ev?.city ? ` (${ev.city})` : ""}
— wiadomość od organizatora —

${text}`;
    let sent = 0;

    for (const item of items) {
      const userId = Number(item?.user?.id);
      if (!userId) continue;

      await apiFetch("/messages/private", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          recipient_user_id: userId,
          content,
        }),
      });
      sent += 1;
    }

    if (input) input.value = "";
    toast(sent > 0 ? t("partnerBroadcast.sent", { count: sent }) : t("partnerBroadcast.noParticipants"));
  } catch (err) {
    toast(err?.userMessage || t("partnerBroadcast.failed"));
  } finally {
    if (btn) btn.disabled = false;
  }
}

function openPartnerEventParticipantsView(eventId) {
  const ev = (App.partnerEvents || []).find(x => String(x.id) === String(eventId));
  if (!ev) return;

  App.selectedPartnerEventId = ev.id;
  go("S9_PARTNER_EVENT_PARTICIPANTS");
  renderPartnerEventParticipants();

  const btn = $("partnerEventBroadcastSendBtn");
  if (btn && btn.dataset.bound !== "1") {
    btn.addEventListener("click", sendPartnerBroadcastMessage);
    btn.dataset.bound = "1";
  }
}




async function searchPartnerEventPlace() {
  const address = $("peAddress")?.value?.trim() || "";
  const city = $("peCity")?.value?.trim() || "";
  const query = [address, city].filter(Boolean).join(", ");

  if (!query) {
    toast(t("partnerPlace.enterQuery"));
    return;
  }

  const btn = $("peFindPlaceBtn");
  if (btn) btn.disabled = true;

  try {
    const data = await apiFetch(`/partners/places/search?q=${encodeURIComponent(address)}&city=${encodeURIComponent(city)}`);
    const results = Array.isArray(data?.data?.items)
      ? data.data.items.filter(item => item.lat != null && item.lng != null)
      : [];

    if (!results.length) {
      renderPartnerPlaceResults([]);
      toast(t("partnerPlace.notFound"));
      return;
    }

    renderPartnerPlaceResults(results);
  } catch (e) {
    console.error("searchPartnerEventPlace error", e);
    toast(t("partnerPlace.searchFailed"));
  } finally {
    if (btn) btn.disabled = false;
  }
}


function renderPartnerPlaceResults(results = []) {
  const box = $("pePlaceResults");
  if (!box) return;

  if (!results.length) {
    box.innerHTML = "";
    return;
  }

  box.innerHTML = `
    <div class="card" style="padding:10px;display:flex;flex-direction:column;gap:10px;">
      ${results.map((place, idx) => `
        <button
          type="button"
          class="btn secondary"
          data-place-index="${idx}"
          style="justify-content:flex-start;text-align:left;"
        >
          <div style="display:flex;flex-direction:column;gap:4px;">
            <strong>${escapeHtml(place.name || t("partnerPlace.defaultPlace"))}</strong>
            <span style="font-size:12px;opacity:.75;">
              ${escapeHtml(place.address || "")}
            </span>
          </div>
        </button>
      `).join("")}
    </div>
  `;

  box.querySelectorAll("[data-place-index]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const place = results[Number(btn.dataset.placeIndex)];
      if (!place) return;

      const typedPlaceName = $("peAddress")?.value?.trim() || place.name || place.address || "";

      if ($("peAddress")) $("peAddress").value = place.name || typedPlaceName;
      if ($("peWhere")) $("peWhere").value = place.name || typedPlaceName;
      if ($("peResolvedAddress")) $("peResolvedAddress").value = place.address || "";
      if ($("peLocationLat")) $("peLocationLat").value = place.lat || "";
      if ($("peLocationLng")) $("peLocationLng").value = place.lng || "";

      const hint = $("peSelectedPlaceHint");
      if (hint) {
        hint.hidden = false;
        hint.innerHTML = `
          <span style="display:block;font-weight:900;">${t("partnerPlace.selectedLabel")} ${escapeHtml(place.name || place.address || t("partnerPlace.defaultLower"))}</span>
          ${place.address ? `<span style="display:block;font-size:12px;opacity:.75;margin-top:4px;">${escapeHtml(place.address)}</span>` : ""}
        `;
      }

      if (box) box.innerHTML = "";
      toast(t("partnerPlace.selectedToast"));
    });
  });
}





const PARTNER_EVENT_INTEREST_TAG_LIMITS = {
  free: 1,
  pro: 2,
  premium: 5,
  enterprise: 10,
};

function getPartnerEventInterestTagLimit() {
  const plan = String(App.partner?.plan || "free").toLowerCase();
  return PARTNER_EVENT_INTEREST_TAG_LIMITS[plan] || PARTNER_EVENT_INTEREST_TAG_LIMITS.free;
}

function getPartnerEventInterestTags() {
  if (!Array.isArray(App.partnerEventInterestTags)) {
    App.partnerEventInterestTags = [];
  }
  return App.partnerEventInterestTags;
}

function setPartnerEventInterestTags(tags) {
  const clean = [];
  const seen = new Set();
  (tags || []).forEach((raw) => {
    const tag = normalizeTag(String(raw || "").replaceAll("#", " ").trim());
    if (!tag || seen.has(tag.toLowerCase())) return;
    seen.add(tag.toLowerCase());
    clean.push(tag);
  });
  App.partnerEventInterestTags = clean;
  return clean;
}

function renderPartnerEventInterestTags() {
  const selected = $("peInterestSelected");
  const selectedText = $("peInterestSelectedText");
  const input = $("peInterest");
  const wrap = $("peInterestInputWrap");
  if (!selected || !selectedText || !input || !wrap) return;

  const tags = getPartnerEventInterestTags();
  const limit = getPartnerEventInterestTagLimit();

  selected.hidden = false;
  selectedText.innerHTML = tags.map((tag, index) => `
    <span class="chip eventInterestChip">
      #${escapeHtml(tag)}
      <button type="button" class="eventInterestChipRemove" data-index="${index}" aria-label="Usuń hashtag">×</button>
    </span>
  `).join("");

  input.disabled = tags.length >= limit;
  wrap.style.display = tags.length >= limit ? "none" : "";

  let counter = $("peInterestCounter");
  if (!counter) {
    counter = document.createElement("div");
    counter.id = "peInterestCounter";
    counter.className = "sectionSub mt8";
    selected.insertAdjacentElement("afterend", counter);
  }
  counter.textContent = `${tags.length}/${limit}`;
}

function getSingleEventTagValue() {
  const input = $("peInterest");
  if (!input) return "";

  return String(input.value || "")
    .replaceAll("#", " ")
    .split(/[\s,;]+/)
    .map(x => normalizeTag(x))
    .find(Boolean) || "";
}

function commitSingleEventTag() {
  const input = $("peInterest");
  if (!input) return;

  const tag = getSingleEventTagValue();
  if (!tag) return;

  const tags = getPartnerEventInterestTags();
  const limit = getPartnerEventInterestTagLimit();

  if (tags.map(x => x.toLowerCase()).includes(tag.toLowerCase())) {
    input.value = "";
    renderPartnerEventInterestTags();
    return;
  }

  if (tags.length >= limit) {
    toast(t("partnerEvent.interestLimitReached", { limit }));
    input.value = "";
    renderPartnerEventInterestTags();
    return;
  }

  setPartnerEventInterestTags([...tags, tag]);
  input.value = "";
  renderPartnerEventInterestTags();
}

function syncPartnerEventDateTimeFields() {
  const date = $("peDate")?.value?.trim() || "";
  const time = $("peTime")?.value?.trim() || "";
  const hidden = $("peWhen");
  if (!hidden) return;
  hidden.value = date && time ? `${date}T${time}` : "";
}

function setPartnerEventDateTimeFields(value) {
  const normalized = String(value || "").trim().replace(" ", "T").slice(0, 16);
  const date = normalized.slice(0, 10);
  const time = normalized.slice(11, 16);
  if ($("peWhen")) $("peWhen").value = date && time ? `${date}T${time}` : "";
  if ($("peDate")) $("peDate").value = date || "";
  if ($("peTime")) $("peTime").value = time || "";
}

function resetSingleEventTag() {
  const input = $("peInterest");
  if (!input) return;

  setPartnerEventInterestTags([]);
  input.disabled = false;
  input.value = "";
  renderPartnerEventInterestTags();

  setTimeout(() => input.focus(), 50);
}

function normalizeSingleEventTagInput() {
  const input = $("peInterest");
  if (!input) return;

  const tag = getSingleEventTagValue();
  input.value = tag;
}

document.addEventListener("keydown", (e) => {
  if (e.target?.id !== "peInterest") return;

  if (e.key === "Enter") {
    e.preventDefault();
    e.stopPropagation();
    commitSingleEventTag();
  }
});

document.addEventListener("change", (e) => {
  if (e.target?.id === "peInterest") {
    commitSingleEventTag();
    return;
  }

  if (e.target?.id === "peDate" || e.target?.id === "peTime") {
    syncPartnerEventDateTimeFields();
  }
});

document.addEventListener("click", (e) => {
  const btn = e.target?.closest?.("#peFindPlaceBtn");
  if (!btn) return;
  e.preventDefault();
  searchPartnerEventPlace();
});

function openPartnerEventEditor(eventId) {
  const ev = (App.partnerEvents || []).find(x => String(x.id) === String(eventId));
  if (!ev) return;

  App.selectedPartnerEventId = ev.id;
  const eventStatus = String(ev.status || "").toLowerCase();
  App.partnerEventFormMode = eventStatus === "published"
    ? "published_edit"
    : (eventStatus === "archived" ? "archived_edit" : "draft_edit");
  syncPartnerEventSubmitBtn();

  if ($("peTitle")) $("peTitle").value = ev.title || "";
  if ($("peCity")) $("peCity").value = ev.city || "";
  if (ev.start_at) {
    setPartnerEventDateTimeFields(String(ev.start_at).trim().replace(" ", "T").slice(0, 16));
  } else {
    setPartnerEventDateTimeFields("");
  }
  if ($("peWhere")) $("peWhere").value = ev.where || ev.location || "";
  if ($("peAddress")) $("peAddress").value = ev.where || ev.address || ev.location || "";
  if ($("peResolvedAddress")) $("peResolvedAddress").value = ev.address || "";
  if ($("peLocationLat")) $("peLocationLat").value = ev.location_lat ?? "";
  if ($("peLocationLng")) $("peLocationLng").value = ev.location_lng ?? "";
  setPartnerEventInterestTags(Array.isArray(ev.interest_tags) && ev.interest_tags.length ? ev.interest_tags : [ev.interest_tag || ev.interest || ""]);
  if ($("peInterest")) $("peInterest").value = "";
  renderPartnerEventInterestTags();
  if ($("peDesc")) $("peDesc").value = ev.description || "";

  const pricingTypeMap = {
    free: "free",
    paid_fixed: "paid_fixed",
    paid_range: "paid_range",
  };
  if ($("pePaidMode")) $("pePaidMode").value = pricingTypeMap[ev.pricing_type] || "free";
  if ($("pePrice")) $("pePrice").value = ev.price_fixed != null ? (ev.price_fixed / 100) : "";
  if ($("pePriceFrom")) $("pePriceFrom").value = ev.price_min != null ? (ev.price_min / 100) : "";
  if ($("pePriceTo")) $("pePriceTo").value = ev.price_max != null ? (ev.price_max / 100) : "";
  if ($("peTicketLink")) $("peTicketLink").value = ev.payment_link || "";
  if ($("peUnlimitedCapacity")) $("peUnlimitedCapacity").checked = ev.capacity == null;
  if ($("peCapacity")) $("peCapacity").value = ev.capacity != null ? ev.capacity : "";
  syncPartnerPricingFields();
  syncPartnerCapacityFields();

  toast(t("partnerEvent.editorOpened"));
  go("S9_PARTNER_CREATE");
  renderPartnerEventParticipants();
}


async function savePartnerEventDraft() {
  if (App.role !== "partner") {
    toast(t("partnerEvent.partnerOnly"));
    return;
  }

  commitSingleEventTag();
  syncPartnerEventDateTimeFields();

  const title = $("peTitle")?.value?.trim();
  const city = normalizeCity($("peCity")?.value);
  const when = $("peWhen")?.value?.trim();
  const where = $("peWhere")?.value?.trim();
  const address = $("peResolvedAddress")?.value?.trim() || $("peAddress")?.value?.trim() || null;
  const locationLat = $("peLocationLat")?.value ? Number($("peLocationLat")?.value) : null;
  const locationLng = $("peLocationLng")?.value ? Number($("peLocationLng")?.value) : null;
  const interestTags = getPartnerEventInterestTags();
  const interest = interestTags[0] || normalizeTag($("peInterest")?.value?.trim());
  const desc = $("peDesc")?.value?.trim();

  if (!title || !city || !when || !where || !interest) {
    toast(t("partnerEvent.draftRequired"));
    return;
  }

  const startAt = new Date(when);
  if (Number.isNaN(startAt.getTime())) {
    toast(t("partnerEvent.invalidDate"));
    return;
  }

  const endAt = new Date(startAt.getTime() + 60 * 60 * 1000);

  const paidMode = $("pePaidMode")?.value || "free";
  const price = Number($("pePrice")?.value || 0);
  const priceFrom = Number($("pePriceFrom")?.value || 0);
  const priceTo = Number($("pePriceTo")?.value || 0);
  const ticketLink = $("peTicketLink")?.value?.trim() || null;
  const unlimitedCapacity = $("peUnlimitedCapacity")?.checked !== false;
  const capacityRaw = $("peCapacity")?.value?.trim() || "";
  const capacityValue = capacityRaw ? Number(capacityRaw) : 0;

  if (!unlimitedCapacity) {
    if (!Number.isInteger(capacityValue) || capacityValue < 1) {
      toast(t("partnerEvent.invalidCapacity"));
      return;
    }
  }

  if (paidMode === "paid_fixed") {
    if (!ticketLink) {
      toast(t("partnerEvent.ticketRequired"));
      return;
    }
    if (!(price > 0)) {
      toast(t("partnerEvent.invalidPrice"));
      return;
    }
  }

  if (paidMode === "paid_range") {
    if (!ticketLink) {
      toast(t("partnerEvent.ticketRequired"));
      return;
    }
    if (!(priceFrom > 0) || !(priceTo > 0)) {
      toast(t("partnerEvent.invalidPriceRange"));
      return;
    }
    if (priceFrom > priceTo) {
      toast(t("partnerEvent.priceRangeOrder"));
      return;
    }
  }

  const pricingTypeMap = {
    free: "free",
    paid_fixed: "paid_fixed",
    paid_range: "paid_range",
  };

  const payload = {
    title,
    description: desc || "",
    city,
    where,
    address,
    location_lat: locationLat,
    location_lng: locationLng,
    interest_tag: interest,
    interest_tags: interestTags.length ? interestTags : [interest],
    start_at: toLocalApiDateTime(when),
    end_at: addHourToLocalDateTime(when),
    pricing_type: pricingTypeMap[paidMode] || "free",
    payment_link: ticketLink,
    capacity: unlimitedCapacity ? null : capacityValue,
  };

  if (payload.pricing_type === "paid_fixed") {
    payload.price_fixed = Math.round(price * 100);
  } else if (payload.pricing_type === "paid_range") {
    payload.price_min = Math.round(priceFrom * 100);
    payload.price_max = Math.round(priceTo * 100);
  }

  try {
    if (App.selectedPartnerEventId) {
      const data = await apiFetch(`/partners/events/${App.selectedPartnerEventId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!data?.success || !data?.data) {
        toast(data?.error?.message || t("partnerEvent.draftSaveFailed"));
        return;
      }

      await loadPartnerEvents();
      toast(t("partnerEvent.draftSaved"));
    } else {
      const data = await apiFetch("/partners/events", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!data?.success || !data?.data) {
        toast(data?.error?.message || t("partnerEvent.draftSaveFailed"));
        return;
      }

      await loadPartnerEvents();
      toast(t("partnerEvent.createdAsDraft"));
    }

    resetPartnerEventFormMode();
    setPartnerEventInterestTags([]);
    renderPartnerEventInterestTags();
    ["peTitle","peCity","peWhen","peDate","peTime","peWhere","peInterest","peDesc","pePrice","pePriceFrom","pePriceTo","peTicketLink"].forEach(id => {
      const el = $(id);
      if (el) el.value = "";
    });

    go("S9_PARTNER_EVENTS");
  } catch (err) {
    toast(err?.userMessage || t("partnerEvent.draftSaveFailed"));
  }
}


function getPartnerActivePublishedEventsCount() {
  const now = new Date();
  return (Array.isArray(App.partnerEvents) ? App.partnerEvents : []).filter((ev) => {
    const status = String(ev?.status || "").toLowerCase();
    const endAt = ev?.end_at ? new Date(ev.end_at) : null;
    return status === "published" && endAt && !Number.isNaN(endAt.getTime()) && endAt >= now;
  }).length;
}

function getPartnerPublishLimitBlockMessage() {
  const rules = getPartnerPlanRules();
  if (rules.maxActiveEvents == null) return null;

  const activeCount = getPartnerActivePublishedEventsCount();
  if (activeCount < rules.maxActiveEvents) return null;

  return t("partnerEvent.publishLimitReached", { plan: String(rules.plan || "free").toUpperCase(), limit: rules.maxActiveEvents });
}


async function publishPartnerEvent() {
  if (App.role !== "partner") {
    toast(t("partnerEvent.partnerOnly"));
    return;
  }

  const title = $("peTitle")?.value?.trim();
  const city = normalizeCity($("peCity")?.value);
  const when = $("peWhen")?.value?.trim();
  const where = $("peWhere")?.value?.trim();
  const address = $("peResolvedAddress")?.value?.trim() || $("peAddress")?.value?.trim() || null;
  const locationLat = $("peLocationLat")?.value ? Number($("peLocationLat")?.value) : null;
  const locationLng = $("peLocationLng")?.value ? Number($("peLocationLng")?.value) : null;
  const interestTags = getPartnerEventInterestTags();
  const interest = interestTags[0] || normalizeTag($("peInterest")?.value?.trim());
  const desc = $("peDesc")?.value?.trim();

  if (App.selectedPartnerEventId) {
    if (!title || !city || !when) {
      toast(t("partnerEvent.publishRequiredExisting"));
      return;
    }
  } else {
    if (!title || !city || !when || !where || !interest) {
      toast(t("partnerEvent.publishRequiredNew"));
      return;
    }
  }

  const startAt = new Date(when);
  if (Number.isNaN(startAt.getTime())) {
    toast(t("partnerEvent.invalidDate"));
    return;
  }

  const endAt = new Date(startAt.getTime() + 60 * 60 * 1000);

  const paidMode = $("pePaidMode")?.value || "free";
  const price = Number($("pePrice")?.value || 0);
  const priceFrom = Number($("pePriceFrom")?.value || 0);
  const priceTo = Number($("pePriceTo")?.value || 0);
  const ticketLink = $("peTicketLink")?.value?.trim() || null;
  const unlimitedCapacity = $("peUnlimitedCapacity")?.checked !== false;
  const capacityRaw = $("peCapacity")?.value?.trim() || "";
  const capacityValue = capacityRaw ? Number(capacityRaw) : 0;

  if (!unlimitedCapacity) {
    if (!Number.isInteger(capacityValue) || capacityValue < 1) {
      toast(t("partnerEvent.invalidCapacity"));
      return;
    }
  }

  if (paidMode === "paid_fixed") {
    if (!ticketLink) {
      toast(t("partnerEvent.ticketRequired"));
      return;
    }
    if (!(price > 0)) {
      toast(t("partnerEvent.invalidPrice"));
      return;
    }
  }

  if (paidMode === "paid_range") {
    if (!ticketLink) {
      toast(t("partnerEvent.ticketRequired"));
      return;
    }
    if (!(priceFrom > 0) || !(priceTo > 0)) {
      toast(t("partnerEvent.invalidPriceRange"));
      return;
    }
    if (priceFrom > priceTo) {
      toast(t("partnerEvent.priceRangeOrder"));
      return;
    }
  }

  const pricingTypeMap = {
    free: "free",
    paid_fixed: "paid_fixed",
    paid_range: "paid_range",
  };

  const payload = {
    title,
    description: desc || "",
    city,
    where,
    address,
    location_lat: locationLat,
    location_lng: locationLng,
    interest_tag: interest,
    interest_tags: interestTags.length ? interestTags : [interest],
    start_at: toLocalApiDateTime(when),
    end_at: addHourToLocalDateTime(when),
    pricing_type: pricingTypeMap[paidMode] || "free",
    payment_link: ticketLink,
    capacity: unlimitedCapacity ? null : capacityValue,
  };

  if (payload.pricing_type === "paid_fixed") {
    payload.price_fixed = Math.round(price * 100);
  } else if (payload.pricing_type === "paid_range") {
    payload.price_min = Math.round(priceFrom * 100);
    payload.price_max = Math.round(priceTo * 100);
  }

  try {
    if (App.selectedPartnerEventId) {
      const data = await apiFetch(`/partners/events/${App.selectedPartnerEventId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!data?.success || !data?.data) {
        toast(data?.error?.message || t("partnerEvent.saveChangesFailed"));
        return;
      }

      if (App.partnerEventFormMode === "published_edit") {
        await loadPartnerEvents();
        toast(t("partnerEvent.updated"));
      } else {
        const publishBlockMessage = getPartnerPublishLimitBlockMessage();
        if (publishBlockMessage) {
          toast(publishBlockMessage);
          await loadPartnerEvents();
          return;
        }

        const publishData = await apiFetch(`/partners/events/${App.selectedPartnerEventId}/publish`, {
          method: "POST",
        });

        if (!publishData?.success || !publishData?.data) {
          toast(publishData?.error?.message || t("partnerEvent.draftSavedPublishFailed"));
          await loadPartnerEvents();
          return;
        }

        await loadPartnerEvents();
        toast(App.partnerEventFormMode === "archived_edit" ? t("partnerEvent.resumed") : t("partnerEvent.published"));
      }
    } else {
      const data = await apiFetch("/partners/events", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!data?.success || !data?.data) {
        toast(data?.error?.message || t("partnerEvent.createFailed"));
        return;
      }

      const createdEventId = data?.data?.id;
      if (!createdEventId) {
        toast(t("partnerEvent.createdMissingId"));
        return;
      }

      const publishBlockMessage = getPartnerPublishLimitBlockMessage();
      if (publishBlockMessage) {
        toast(publishBlockMessage);
        await loadPartnerEvents();
        return;
      }

      const publishData = await apiFetch(`/partners/events/${createdEventId}/publish`, {
        method: "POST",
      });

      if (!publishData?.success || !publishData?.data) {
        toast(publishData?.error?.message || t("partnerEvent.createdPublishFailed"));
        await loadPartnerEvents();
        return;
      }

      await loadPartnerEvents();
      toast(t("partnerEvent.createdAndPublished"));
      resetPartnerEventFormMode();
      go("S9_PARTNER_EVENTS");
      return;
    }

    resetPartnerEventFormMode();
    ["peTitle","peCity","peWhen","peDate","peTime","peWhere","peInterest","peDesc","pePrice","pePriceFrom","pePriceTo","peTicketLink"].forEach(id => {
      const el = $(id);
      if (el) el.value = "";
    });

    go("S9_PARTNER_EVENTS");
  } catch (err) {
    toast(err?.userMessage || t("partnerEvents.saveFailed"));
  }
}

/* ------------------------- Notifications -------------------------- */

let notificationsVisibleLimit = 10;
let notificationsRenderInFlight = false;
let partnerNotifBadgeRefreshInFlight = false;
let partnerNotifBadgeLastRefreshAt = 0;
const PARTNER_NOTIF_BADGE_REFRESH_MIN_INTERVAL_MS = 30000;
let groupBadgeRefreshInFlight = false;
let groupBadgeLastRefreshAt = 0;
const GROUP_BADGE_REFRESH_MIN_INTERVAL_MS = 30000;

function getNotificationIcon(title = "", body = "") {
  const text = `${title} ${body}`.toLowerCase();

  const icons = {
    check: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12.5l4.2 4.2L19 7.5"/></svg>`,
    eye: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M2.8 12s3.5-6 9.2-6 9.2 6 9.2 6-3.5 6-9.2 6-9.2-6-9.2-6z"/><circle cx="12" cy="12" r="2.8"/></svg>`,
    calendar: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 3v4M17 3v4M4.5 9h15M6 5.5h12a2 2 0 0 1 2 2v11a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-11a2 2 0 0 1 2-2z"/></svg>`,
    shield: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3.5l7 3v5.2c0 4.4-2.8 8.3-7 9.8-4.2-1.5-7-5.4-7-9.8V6.5l7-3z"/></svg>`,
    info: `<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 10.5v6M12 7.5h.01"/></svg>`,
    userPlus: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M10 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM3.5 20c.8-3.3 3.2-5 6.5-5 1.7 0 3.1.4 4.2 1.2M18 8v6M15 11h6"/></svg>`,
    users: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 11a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7zM2.8 20c.7-3.2 2.9-4.8 6.2-4.8 3.2 0 5.4 1.6 6.2 4.8M16.5 11a3 3 0 1 0 0-6M17 15.2c2.5.3 4.1 1.9 4.7 4.8"/></svg>`,
  };

  if (text.includes("zapis") || text.includes("signup") || text.includes("signed up")) return { icon: icons.check, className: "notifIconSuccess" };
  if (text.includes("obserw") || text.includes("follow")) return { icon: icons.eye, className: "notifIconObserve" };
  if (text.includes("grup") || text.includes("group")) return { icon: icons.users, className: "notifIconGroup" };
  if (text.includes("znajom") || text.includes("friend")) return { icon: icons.userPlus, className: "notifIconFriend" };

  if (
    text.includes("jutro") ||
    text.includes("za 2 dni") ||
    text.includes("przypominamy")
  ) return { icon: icons.calendar, className: "notifIconEvent" };

  if (
    text.includes("godziny") ||
    text.includes("miejsce") ||
    text.includes("wydarzenia")
  ) return { icon: icons.calendar, className: "notifIconEvent" };

  if (
    text.includes("weryfik") ||
    text.includes("bezpieczeń") ||
    text.includes("ostrzeż")
  ) return { icon: icons.shield, className: "notifIconWarning" };

  if (
    text.includes("zgłoszen") ||
    text.includes("pracujemy") ||
    text.includes("błąd")
  ) return { icon: icons.info, className: "notifIconInfo" };

  return { icon: icons.info, className: "notifIconDefault" };
}



function showMoreNotifications() {
  notificationsVisibleLimit += 10;
  renderNotifications();
}

async function renderNotifications() {
  const list = $("notifList");
  if (!list) return;
  if (notificationsRenderInFlight) return;
  notificationsRenderInFlight = true;

  let items = [];
  updateNotifBadges(0);

  try {
    if (App.role === "partner") {
      const evRes = await apiFetch("/partners/events?limit=100");
      const events = Array.isArray(evRes?.data?.items) ? evRes.data.items : [];

      const notifBatches = await Promise.all(events.map(async (ev) => {
        const out = [];
        const endedAt = parseUslyTimestamp(ev?.end_at);
        const archivedNotificationsCutoff = Date.now() - 30 * 24 * 60 * 60 * 1000;
        if (endedAt && endedAt < archivedNotificationsCutoff) {
          return out;
        }

        try {
          const res = await apiFetch(`/partners/events/${ev.id}/participants?limit=20`);
          const rows = Array.isArray(res?.data?.items) ? res.data.items : [];
          out.push(...rows.map((row) => ({
            type: "signup",
            eventId: ev.id,
            eventTitle: ev.title || t("notifications.defaultEvent"),
            userNick: row?.user?.nick || row?.user?.email || `${t("notifications.defaultUser")} #${row?.user?.id || "?"}`,
            createdAt: row?.signup?.created_at || null,
          })));
        } catch (err) {
          console.error(`partner notifications participants failed for event ${ev.id}`, err);
        }

        try {
          const res = await apiFetch(`/partners/events/${ev.id}/observers?limit=20`);
          const rows = Array.isArray(res?.data?.items) ? res.data.items : [];
          out.push(...rows.map((row) => ({
            type: "observer",
            eventId: ev.id,
            eventTitle: ev.title || t("notifications.defaultEvent"),
            userNick: row?.user?.nick || row?.user?.email || `${t("notifications.defaultUser")} #${row?.user?.id || "?"}`,
            createdAt: row?.saved?.created_at || null,
          })));
        } catch (err) {
          console.error(`partner notifications observers failed for event ${ev.id}`, err);
        }

        return out;
      }));

      items = notifBatches
        .flat()
        .sort((a, b) => {
          const ad = parseUslyTimestamp(a?.createdAt);
          const bd = parseUslyTimestamp(b?.createdAt);
          return bd - ad;
        })
        .slice(0, 50)
        .map((item) => ({
          title: item.type === "observer" ? t("notifications.partner.newObserverTitle") : t("notifications.partner.newSignupTitle"),
          body: item.type === "observer"
            ? t("notifications.partner.newObserverBody", { user: item.userNick, event: item.eventTitle })
            : t("notifications.partner.newSignupBody", { user: item.userNick, event: item.eventTitle }),
          targetView: "S9_PARTNER_EVENTS",
          createdAt: item.createdAt || null,
        }));
    } else {
      const [reqReq, groupInvReq, eventNotifReq] = await Promise.allSettled([
        apiFetch("/friends/requests"),
        apiFetch("/group-invitations"),
        apiFetch("/users/me/notifications?limit=50"),
      ]);

      const reqRes = reqReq.status === "fulfilled" ? reqReq.value : null;
      const groupInvRes = groupInvReq.status === "fulfilled" ? groupInvReq.value : null;
      const eventNotifRes = eventNotifReq.status === "fulfilled" ? eventNotifReq.value : null;

      const incoming = Array.isArray(reqRes?.data?.incoming) ? reqRes.data.incoming : [];
      const incomingGroupInvites = Array.isArray(groupInvRes?.data?.incoming) ? groupInvRes.data.incoming : [];
      const eventNotifItems = Array.isArray(eventNotifRes?.data?.items) ? eventNotifRes.data.items : [];

      incoming.forEach((req) => {
        const nick = req?.user?.nick || req?.user?.email || t("notifications.defaultNewPerson");
        items.push({
          title: t("notifications.friendRequestTitle"),
          body: t("notifications.friendRequestBody", { user: nick }),
          targetView: "S10E_PROFILE_INVITES",
          createdAt: req?.created_at || null,
        });
      });

      eventNotifItems.forEach((row) => {
        const notification = row?.notification || {};
        if (notification.type === "friend_request") return;
        const event = row?.event || {};

        const userReportTitles = {
          admin_user_report_in_review: t("notifications.admin.userReportInReview"),
          admin_user_report_resolved: t("notifications.admin.userReportResolved"),
          admin_user_report_rejected: t("notifications.admin.userReportRejected"),
          admin_event_report_in_review: t("notifications.admin.eventReportInReview"),
          admin_event_report_resolved: t("notifications.admin.eventReportResolved"),
          admin_event_report_rejected: t("notifications.admin.eventReportRejected"),
          admin_user_warning_warning_profile: t("notifications.admin.warningProfile"),
          admin_user_warning_warning_content: t("notifications.admin.warningContent"),
          admin_user_warning_warning_behavior: t("notifications.admin.warningBehavior"),
          admin_bug_report_accepted: t("notifications.admin.bugAccepted"),
          admin_bug_report_in_progress: t("notifications.admin.bugInProgress"),
          admin_bug_report_fixed: t("notifications.admin.bugFixed"),
          admin_bug_report_resolved: t("notifications.admin.bugResolved"),
          admin_bug_report_not_reproducible: t("notifications.admin.bugNotReproducible"),
        };

        if (userReportTitles[notification.type]) {
          const isWarning = String(notification.type || "").startsWith("admin_user_warning_");
          const isBugReport = String(notification.type || "").startsWith("admin_bug_report_");
          const isEventReport = String(notification.type || "").startsWith("admin_event_report_");
          items.push({
            title: userReportTitles[notification.type],
            body: isWarning
              ? t("notifications.admin.warningBody")
              : isBugReport
                ? t("notifications.admin.bugBody")
                : isEventReport
                  ? t("notifications.admin.eventReportBody")
                  : t("notifications.admin.reportBody"),
            targetView: "S12_NOTIFICATIONS",
            createdAt: notification?.created_at || null,
          });
          return;
        }
        const isTimeAndLocationChange = notification.type === "event_time_and_location_changed";
        const isTimeChange = notification.type === "event_time_changed";
        const isLocationChange = notification.type === "event_location_changed";
        const isLegacyUpdate = notification.type === "event_updated";
        const isAdminUnderReview = notification.type === "admin_event_under_review";
        const isAdminSafetyNotice = notification.type === "admin_event_safety_notice";
        const isAdminArchived = notification.type === "admin_event_archived";
        const isReminder2d = notification.type === "event_reminder_2d";
        const isReminder1d = notification.type === "event_reminder_1d";

        if (
          !isTimeAndLocationChange &&
          !isTimeChange &&
          !isLocationChange &&
          !isLegacyUpdate &&
          !isAdminUnderReview &&
          !isAdminSafetyNotice &&
          !isAdminArchived &&
          !isReminder2d &&
          !isReminder1d
        ) return;

        const title = event?.title || t("notifications.defaultEvent");
        const place = [event?.city, event?.where].filter(Boolean).join(", ");
        const when = event?.start_at
          ? String(event.start_at).trim().replace("T", " ").slice(0, 16)
          : "";
        const eventContext = [when, place].filter(Boolean).join(" • ");

        items.push({
          title: isReminder2d
            ? t("notifications.event.reminder2dTitle")
            : isReminder1d
              ? t("notifications.event.reminder1dTitle")
              : isTimeAndLocationChange
                ? t("notifications.event.timeAndLocationChangedTitle")
                : isTimeChange
              ? t("notifications.event.timeChangedTitle")
              : isLocationChange
                ? t("notifications.event.locationChangedTitle")
                : isAdminUnderReview
                  ? t("notifications.event.underReviewTitle")
                  : isAdminSafetyNotice
                    ? t("notifications.event.safetyNoticeTitle")
                    : isAdminArchived
                      ? t("notifications.event.archivedTitle")
                      : t("notifications.event.updatedTitle"),
          body: isReminder2d
            ? t("notifications.event.reminder2dBody", { event: title, context: eventContext ? ` ${eventContext}` : "" })
            : isReminder1d
              ? t("notifications.event.reminder1dBody", { event: title, context: eventContext ? ` ${eventContext}` : "" })
              : isAdminUnderReview
                ? t("notifications.event.underReviewBody", { event: title, context: eventContext ? ` ${eventContext}` : "" })
                : isAdminSafetyNotice
              ? t("notifications.event.safetyNoticeBody", { event: title, context: eventContext ? ` ${eventContext}` : "" })
              : isAdminArchived
                ? t("notifications.event.archivedBody", { event: title, context: eventContext ? ` ${eventContext}` : "" })
                : place || when
                  ? `${title} — ${eventContext}`
                  : t("notifications.event.updatedBody", { event: title }),
          targetView: "S7_EVENTS",
          createdAt: notification?.created_at || null,
        });
      });

      incomingGroupInvites.forEach((inv) => {
        const nick = inv?.user?.nick || inv?.user?.email || t("notifications.defaultUser");
        const groupTitle = inv?.group?.title || t("notifications.defaultGroup");
        items.push({
          title: t("notifications.groupInviteTitle"),
          body: t("notifications.groupInviteBody", { user: nick, group: groupTitle }),
          targetView: "S10E_PROFILE_INVITES",
          createdAt: inv?.created_at || null,
        });
      });

      items.sort((a, b) => {
        const ad = parseUslyTimestamp(a?.createdAt);
        const bd = parseUslyTimestamp(b?.createdAt);
        return bd - ad;
      });
    }

  } catch (e) {
    console.error("notifications error", e);
  }

  const seenAtRaw = localStorage.getItem(
    App.role === "partner" ? "usly_partner_notifications_seen_at" : "usly_user_notifications_seen_at"
  );
  const seenAt = parseUslyTimestamp(seenAtRaw);

  if (items.length === 0) {
    list.innerHTML = `
      <div class="card">
        <div class="sectionSub">${t("notifications.empty")}</div>
      </div>
    `;
    updateNotifBadges(0);
    notificationsRenderInFlight = false;
    return;
  }

  const visibleItems = items.slice(0, notificationsVisibleLimit);

  list.innerHTML = visibleItems.map(n => {
    const isNew = parseUslyTimestamp(n?.createdAt) > seenAt;
    const ts = n?.createdAt
      ? new Date(parseUslyTimestamp(n.createdAt)).toLocaleString("pl-PL", {
          day: "2-digit",
          month: "2-digit",
          hour: "2-digit",
          minute: "2-digit",
        })
      : "";
    return `
    <div class="notificationItem ${isNew ? 'notifNew' : ''}" onclick="go('${n.targetView}')">

      <div class="notificationIcon ${getNotificationIcon(n.title, n.body).className}">
        ${getNotificationIcon(n.title, n.body).icon}
      </div>

      <div class="notificationContent">
        <div class="notificationTop">
          <div class="notificationTitle">
            ${isNew ? '<span class="notificationNewDot"></span>' : ''}
            ${escapeHtml(n.title)}
          </div>

          <div class="notificationTime">${escapeHtml(ts)}</div>
        </div>

        <div class="notificationBody">${escapeHtml(n.body)}</div>
      </div>

    </div>
  `;
  }).join("") + (
    items.length > notificationsVisibleLimit
      ? `<button class="btn secondary mt12" type="button" onclick="showMoreNotifications()">${t("notifications.loadMore")} (${items.length - notificationsVisibleLimit})</button>`
      : ""
  );

  if (App.role === "partner") {
    localStorage.setItem("usly_partner_notifications_seen_at", new Date().toISOString());
    updateNotifBadges(0);
  } else {
    localStorage.setItem("usly_user_notifications_seen_at", new Date().toISOString());
    updateNotifBadges(0);
  }

  notificationsRenderInFlight = false;
}




function updateNotifBadges(count) {
  const buttons = document.querySelectorAll('button[id^="notifBtn"]');
  buttons.forEach(btn => {
    if (count > 0) {
      btn.classList.add("hasBadge");
      btn.setAttribute("data-badge", String(count));
    } else {
      btn.classList.remove("hasBadge");
      btn.removeAttribute("data-badge");
    }
  });
}

function parseUslyTimestamp(value) {
  if (!value) return 0;
  const normalized = typeof value === "string" && !/[zZ]|[+-]\d\d:\d\d$/.test(value)
    ? `${value}Z`
    : value;
  const ts = new Date(normalized).getTime();
  return Number.isFinite(ts) ? ts : 0;
}

async function refreshNotifBadgeCount() {
  if (!App.isLoggedIn || App.role !== "user") {
    updateNotifBadges(0);
    return;
  }

  if (App.currentView === "S10E_PROFILE_INVITES" || App.currentView === "S12_NOTIFICATIONS") {
    updateNotifBadges(0);
    return;
  }

  try {
    const seenAtRaw = localStorage.getItem("usly_user_notifications_seen_at");
    const seenAt = parseUslyTimestamp(seenAtRaw);

    const [reqReq, groupInvReq, eventNotifReq] = await Promise.allSettled([
      apiFetch("/friends/requests"),
      apiFetch("/group-invitations"),
      apiFetch("/users/me/notifications?limit=50"),
    ]);

    const reqRes = reqReq.status === "fulfilled" ? reqReq.value : null;
    const groupInvRes = groupInvReq.status === "fulfilled" ? groupInvReq.value : null;
    const eventNotifRes = eventNotifReq.status === "fulfilled" ? eventNotifReq.value : null;

    const incoming = Array.isArray(reqRes?.data?.incoming) ? reqRes.data.incoming : [];
    const incomingGroupInvites = Array.isArray(groupInvRes?.data?.incoming) ? groupInvRes.data.incoming : [];
    const eventNotifItems = Array.isArray(eventNotifRes?.data?.items) ? eventNotifRes.data.items : [];

    const totalUnread =
      incoming.filter((req) => {
        const createdAt = parseUslyTimestamp(req?.created_at);
        return createdAt > seenAt;
      }).length +
      incomingGroupInvites.filter((inv) => {
        const createdAt = parseUslyTimestamp(inv?.created_at);
        return createdAt > seenAt;
      }).length +
      eventNotifItems.filter((row) => {
        const notification = row?.notification || {};
        if (notification.type === "friend_request" || notification.type === "group_invitation") return false;
        const createdAt = parseUslyTimestamp(notification?.created_at);
        return createdAt > seenAt;
      }).length;

    updateNotifBadges(totalUnread);
  } catch (e) {
    console.error("notif badge refresh error", e);
  }
}

async function refreshPartnerMsgBadgeCount() {
  const badge = $("badgePartnerMsgs");
  if (!badge) return;

  if (!App.isLoggedIn || App.role !== "partner") {
    badge.style.display = "none";
    return;
  }

  if (App.currentView === "S9_PARTNER_MESSAGES" || App.currentView === "S6B_CHAT_THREAD") {
    badge.style.display = "none";
    return;
  }

  try {
    const data = await apiFetch("/messages/private");
    const items = Array.isArray(data?.data?.items) ? data.data.items : [];
    const totalUnread = items.reduce((sum, item) => {
      const chatId = `pm_${item?.other_user_id}`;
      const muted = isChatMuted(chatId);
      return sum + (muted ? 0 : Number(item?.unread_count || 0));
    }, 0);

    badge.textContent = String(totalUnread);
    badge.style.display = totalUnread > 0 ? "inline-flex" : "none";
  } catch (e) {
    console.error("partner msg badge refresh error", e);
    badge.style.display = "none";
  }
}

function getGroupSeenMapStorageKey() {
  return `usly_group_seen_map_${App.role || "user"}_${App.currentUserId || "guest"}`;
}

function getMutedGroupsStorageKey() {
  return `usly_muted_groups_${App.role || "user"}_${App.currentUserId || "guest"}`;
}

function getMutedChatsStorageKey() {
  return `usly_muted_chats_${App.role || "user"}_${App.currentUserId || "guest"}`;
}

function getChatSeenMapStorageKey() {
  return `usly_chat_seen_map_${App.role || "user"}_${App.currentUserId || "guest"}`;
}

function readChatSeenMap() {
  try {
    const raw = localStorage.getItem(getChatSeenMapStorageKey());
    const parsed = raw ? JSON.parse(raw) : {};
    return parsed && typeof parsed === "object" ? parsed : {};
  } catch (_) {
    return {};
  }
}

function writeChatSeenMap(map) {
  try {
    localStorage.setItem(getChatSeenMapStorageKey(), JSON.stringify(map || {}));
  } catch (_) {}
}

function markChatAsSeen(chatId) {
  if (!chatId) return;
  const seenMap = readChatSeenMap();
  seenMap[String(chatId)] = new Date().toISOString();
  writeChatSeenMap(seenMap);
}

function readMutedChatsMap() {
  try {
    const raw = localStorage.getItem(getMutedChatsStorageKey());
    const parsed = raw ? JSON.parse(raw) : {};
    return parsed && typeof parsed === "object" ? parsed : {};
  } catch (_) {
    return {};
  }
}

function writeMutedChatsMap(map) {
  try {
    localStorage.setItem(getMutedChatsStorageKey(), JSON.stringify(map || {}));
  } catch (_) {}
}

function isChatMuted(chatId) {
  if (!chatId) return false;
  const map = readMutedChatsMap();
  return !!map[String(chatId)];
}

function setChatMuted(chatId, muted) {
  if (!chatId) return;
  const map = readMutedChatsMap();
  if (muted) {
    map[String(chatId)] = true;
  } else {
    delete map[String(chatId)];
  }
  writeMutedChatsMap(map);
}

function readMutedGroupsMap() {
  try {
    const raw = localStorage.getItem(getMutedGroupsStorageKey());
    const parsed = raw ? JSON.parse(raw) : {};
    return parsed && typeof parsed === "object" ? parsed : {};
  } catch (_) {
    return {};
  }
}

function writeMutedGroupsMap(map) {
  try {
    localStorage.setItem(getMutedGroupsStorageKey(), JSON.stringify(map || {}));
  } catch (_) {}
}

function isGroupMuted(groupId) {
  if (!groupId) return false;
  const mutedMap = readMutedGroupsMap();
  return !!mutedMap[String(groupId)];
}

function setGroupMuted(groupId, muted) {
  if (!groupId) return;
  const mutedMap = readMutedGroupsMap();
  if (muted) {
    mutedMap[String(groupId)] = true;
  } else {
    delete mutedMap[String(groupId)];
  }
  writeMutedGroupsMap(mutedMap);
}

function readGroupSeenMap() {
  try {
    const raw = localStorage.getItem(getGroupSeenMapStorageKey());
    const parsed = raw ? JSON.parse(raw) : {};
    return parsed && typeof parsed === "object" ? parsed : {};
  } catch (_) {
    return {};
  }
}

function writeGroupSeenMap(map) {
  try {
    localStorage.setItem(getGroupSeenMapStorageKey(), JSON.stringify(map || {}));
  } catch (_) {}
}

function markGroupAsSeen(groupId) {
  if (!groupId) return;
  const seenMap = readGroupSeenMap();
  seenMap[String(groupId)] = new Date().toISOString();
  writeGroupSeenMap(seenMap);
}

async function getGroupUnreadSummary() {
  if (!App.isLoggedIn || App.role !== "user") {
    return { totalGroupsWithUnread: 0, byGroupId: {} };
  }

  const seenMap = readGroupSeenMap();
  const myGroups = Array.isArray(App.myGroups) ? App.myGroups : [];
  const byGroupId = {};
  let totalGroupsWithUnread = 0;

  for (const g of myGroups) {
    try {
      const data = await apiFetch(`/messages/group/${g.id}`);
      const items = Array.isArray(data?.data?.items) ? data.data.items : [];
      const seenAt = parseUslyTimestamp(seenMap[String(g.id)]);
      const unreadCount = items.filter((m) => {
        const createdAt = parseUslyTimestamp(m?.created_at);
        return createdAt > seenAt && String(m?.sender_user_id) !== String(App.currentUserId);
      }).length;

      const muted = isGroupMuted(g.id);
      const finalUnread = muted ? 0 : unreadCount;

      byGroupId[String(g.id)] = finalUnread;
      if (finalUnread > 0) totalGroupsWithUnread += 1;
    } catch (_) {
      byGroupId[String(g.id)] = 0;
    }
  }

  return { totalGroupsWithUnread, byGroupId };
}


async function refreshGroupBadgeCount() {
  const badge = $("badgeGroups");
  if (!badge) return;

  if (!App.isLoggedIn || App.role !== "user") {
    badge.style.display = "none";
    return;
  }

  const now = Date.now();
  if (groupBadgeRefreshInFlight) return;
  if (now - groupBadgeLastRefreshAt < GROUP_BADGE_REFRESH_MIN_INTERVAL_MS) return;

  groupBadgeRefreshInFlight = true;
  groupBadgeLastRefreshAt = now;

  try {
    const summary = await getGroupUnreadSummary();
    const count = Number(summary?.totalGroupsWithUnread || 0);

    badge.textContent = String(count);
    badge.style.display = count > 0 ? "inline-flex" : "none";
  } catch (e) {
    console.error("group badge refresh error", e);
    badge.style.display = "none";
  } finally {
    groupBadgeRefreshInFlight = false;
  }
}

async function refreshPartnerNotifBadgeCount() {
  if (!App.isLoggedIn || App.role !== "partner") {
    updateNotifBadges(0);
    return;
  }

  if (App.currentView === "S12_NOTIFICATIONS") {
    updateNotifBadges(0);
    return;
  }

  const now = Date.now();
  if (partnerNotifBadgeRefreshInFlight) return;
  if (now - partnerNotifBadgeLastRefreshAt < PARTNER_NOTIF_BADGE_REFRESH_MIN_INTERVAL_MS) return;

  partnerNotifBadgeRefreshInFlight = true;
  partnerNotifBadgeLastRefreshAt = now;

  try {
    const seenAtRaw = localStorage.getItem("usly_partner_notifications_seen_at");
    const seenAt = seenAtRaw ? new Date(seenAtRaw).getTime() : 0;

    const evRes = await apiFetch("/partners/events?limit=100");
    const events = Array.isArray(evRes?.data?.items) ? evRes.data.items : [];

    const notifBatches = await Promise.all(events.map(async (ev) => {
      const out = [];
      const endedAt = parseUslyTimestamp(ev?.end_at);
      const archivedNotifCutoff = Date.now() - 30 * 24 * 60 * 60 * 1000;
      if (endedAt && endedAt < archivedNotifCutoff) {
        return out;
      }

      try {
        const res = await apiFetch(`/partners/events/${ev.id}/participants?limit=20`);
        const rows = Array.isArray(res?.data?.items) ? res.data.items : [];
        out.push(...rows.map((row) => ({
          createdAt: row?.signup?.created_at || null,
        })));
      } catch (err) {
        if (![403, 404].includes(Number(err?.status))) {
          console.warn(`partner notif badge participants failed for event ${ev.id}`, err);
        }
      }

      try {
        const res = await apiFetch(`/partners/events/${ev.id}/observers?limit=20`);
        const rows = Array.isArray(res?.data?.items) ? res.data.items : [];
        out.push(...rows.map((row) => ({
          createdAt: row?.saved?.created_at || null,
        })));
      } catch (err) {
        if (![403, 404].includes(Number(err?.status))) {
          console.warn(`partner notif badge observers failed for event ${ev.id}`, err);
        }
      }

      return out;
    }));

    const totalUnread = notifBatches
      .flat()
      .filter((row) => {
        const createdAt = parseUslyTimestamp(row?.createdAt);
        return createdAt > seenAt;
      })
      .length;

    updateNotifBadges(totalUnread);
  } catch (e) {
    console.error("partner notif badge refresh error", e);
    updateNotifBadges(0);
  } finally {
    partnerNotifBadgeRefreshInFlight = false;
  }
}

function getEventCapacityCopy(ev) {
  const signups = Number(ev?.signupsCount || 0);
  const capacity = ev?.capacity ?? null;
  const spotsLeft = ev?.spotsLeft ?? null;

  if (capacity == null) {
    return {
      line: t("eventCapacity.signed", { count: signups }),
      alert: "",
      full: false,
    };
  }

  const usedLine = t("eventCapacity.used", { taken: signups, capacity });

  if (spotsLeft === 0) {
    return {
      line: usedLine,
      alert: t("eventCapacity.full"),
      full: true,
    };
  }

  if (typeof spotsLeft === "number" && spotsLeft > 0 && spotsLeft <= 3) {
    return {
      line: usedLine,
      alert: spotsLeft === 1 ? t("eventCapacity.lastOne") : t("eventCapacity.lastFew", { count: spotsLeft }),
      full: false,
    };
  }

  return {
    line: usedLine,
    alert: "",
    full: false,
  };
}

/* ------------------------- Rendering Lists -------------------------- */
function renderNearby() {
  initNearbyMap();
  renderNearbyMapMarkers();

  // People list in nearby tab
  const pList = $("nearbyPeopleList");
  if (pList) {
    const people = getNearbyPeopleForView();

    if (!people.length) {
      pList.innerHTML = `<div class="tMuted">${t("nearby.emptyPeople")}</div>`;
    } else {
      pList.innerHTML = people.map(p => `
      <div class="listItem nearbyPersonCard" onclick="openPerson('${p.id}')">
        <div class="listTop">
          <div class="listLeft">
            <div class="listAvatar nearbyPersonAvatar">${p.avatarUrl ? `<img src="${String(p.avatarUrl).startsWith("http") ? p.avatarUrl : `${API_BASE_URL}${p.avatarUrl}`}" alt="${p.nick}" style="width:100%;height:100%;object-fit:cover;border-radius:inherit;" />` : `<div class="userAvatarFallback" style="${premiumAvatarStyle(getAvatarGradient(p.nick || "U"))}" data-name="${escapeHtml(p.nick || "U")}">${avatarInitial(p.nick || "U")}</div>`}</div>
            <div style="min-width:0;">
              <div class="listTitle">${escapeHtml(p.nick || t("friends.defaultUser", { id: p.id || "—" }))}</div>
              ${(() => {
                const tags = Array.isArray(p.trainerInterests) ? p.trainerInterests : [];
                return tags.length ? `<div class="nearbyTrainerLine">🎓 ${t("profileInterests.leadsNearbyLabel")}</div>` : "";
              })()}
              <div class="listMeta">${p.distance_km != null ? (p.distance_km < 1 ? t("nearby.distanceUnder1", "< 1 km od Ciebie") : t("nearby.distanceKm", { km: String(p.distance_km).replace(".", ",") })) : t("nearby.inArea", "W okolicy")}${p.age ? ` • ${t("personProfile.ageYears", { age: p.age })}` : ""}</div>
            </div>
          </div>
          <div class="listRight">
            <div class="listTag nearbyMatchTag">${sharedScore(p)}%</div>
          </div>
        </div>
        <div class="nearbyInterestChips">${(p.interests || []).slice(0,3).map(t => `<span class="nearbyInterestChip">#${escapeHtml(t)}</span>`).join("")}</div>
      </div>
    `).join("");
    }
  }

  // Events list in nearby tab
  const eList = $("nearbyEventsList");
  if (eList) {
    const events = (App.nearbyEvents || [])
      .filter(ev => matchesUserEventInterest(ev) && isEventInNearbyRadius(ev))
      .slice(0, 8);

    if (!events.length) {
      eList.innerHTML = `<div class="tMuted">${t("nearby.emptyEvents")}</div>`;
      return;
    }

    eList.innerHTML = events.map(ev => `
      <div class="listItem" onclick="openEvent('${ev.id}')">
        <div class="listTop">
          <div class="listLeft">
            <div class="listAvatar">${premiumIcon("calendar", ev.title || ev.name || "Wydarzenie")}</div>
            <div style="min-width:0;">
              <div class="listTitle">${ev.title}</div>
              <div class="listMeta">${ev.city} • ${ev.where} • ${ev.when}</div>
            </div>
          </div>
          <div class="listRight">
            <div class="listTag ${ev.paidMode === 'free' ? '' : 'paid'}">
              ${ev.paidMode === "free" ? t("eventDetail.ticketFree") : t("eventDetail.ticketPaid")}
            </div>
          </div>
        </div>
        <div class="listBody">
        #${ev.interest} • ${getEventCapacityCopy(ev).line}${getEventCapacityCopy(ev).alert ? ` • ${getEventCapacityCopy(ev).alert}` : ""}
        ${(ev.saved || ev.interested) ? `<div class="chips" style="margin-top:8px;">
          ${ev.saved ? `<div class="chip">${t("eventDetail.savedChip")}</div>` : ``}
          ${ev.interested ? `<div class="chip">${t("eventDetail.interestedChip")}</div>` : ``}
        </div>` : ``}
      </div>
      </div>
    `).join("");
  }
}

function renderEventsList() {
  const list = $("eventsList");
  if (!list) return;

  const q = ($("eventsSearch")?.value || "").trim().toLowerCase();

  let events = App.events.slice();
  if (App.eventsTab === "followed") {
    events = events.filter(e => e.saved || e.interested);
  } else {
    events = events.filter(e =>
      matchesUserEventInterest(e) &&
      !isEventInNearbyRadius(e) &&
      !e.saved &&
      !e.interested
    );
  }

  if (q) {
    const qClean = q.replace("#", "");
    events = events.filter(e =>
      e.title.toLowerCase().includes(q) ||
      e.interest.toLowerCase().includes(qClean)
    );
  }

  if (!events.length) {
    list.innerHTML = `<div class="tMuted">${t(App.eventsTab === "followed" ? "events.emptyFollowed" : "events.emptyForYou")}</div>`;
    return;
  }

  list.innerHTML = events.map(ev => `
    <div class="listItem" onclick="openEvent('${ev.id}')">
      <div class="listTop">
        <div class="listLeft">
          <div class="listAvatar">${premiumIcon("calendar", ev.title || ev.name || "Wydarzenie")}</div>
          <div style="min-width:0;">
            <div class="listTitle">${ev.title}</div>
            <div class="listMeta">${ev.city} • ${ev.where} • ${ev.when}</div>
          </div>
        </div>
        <div class="listRight">
          <div class="listTag ${ev.paidMode === 'free' ? '' : 'paid'}">
            ${ev.paidMode === "free" ? t("eventDetail.ticketFree") : t("eventDetail.ticketPaid")}
          </div>
        </div>
      </div>

      <div class="listBody">
        #${ev.interest} • ${getEventCapacityCopy(ev).line}${getEventCapacityCopy(ev).alert ? ` • ${getEventCapacityCopy(ev).alert}` : ""}

        ${(ev.saved || ev.interested) ? `
          <div class="chips" style="margin-top:8px;">
            ${ev.saved ? `<div class="chip">${t("eventDetail.savedChip")}</div>` : ``}
            ${ev.interested ? `<div class="chip">${t("eventDetail.interestedChip")}</div>` : ``}
          </div>
        ` : ``}
      </div>
    </div>
  `).join("");
}

async function renderGroups() {
  const list = $("groupList");
  if (!list) return;

  refreshCreateGroupUi();

  const q = ($("groupSearch")?.value || "").trim().toLowerCase().replace("#", "");

  let myGroups = Array.isArray(App.myGroups) ? [...App.myGroups] : [];
  let suggestedGroups = Array.isArray(App.groups) ? [...App.groups] : [];
  const unreadSummary = await getGroupUnreadSummary().catch(() => ({ totalGroupsWithUnread: 0, byGroupId: {} }));
  const unreadByGroupId = unreadSummary?.byGroupId || {};

  const myInterestTags = (Array.isArray(App.user?.interests) ? App.user.interests : [])
    .map(x => normalizeTag(String(x)))
    .filter(Boolean);

  if (myInterestTags.length) {
    suggestedGroups = suggestedGroups.filter(g =>
      myInterestTags.includes(normalizeTag(String(g.interestTag || "")))
    );
  } else {
    suggestedGroups = [];
  }

  if (q) {
    myGroups = myGroups.filter(g =>
      (g.title || "").toLowerCase().includes(q) ||
      (g.interestTag || "").toLowerCase().includes(q)
    );

    suggestedGroups = suggestedGroups.filter(g =>
      (g.title || "").toLowerCase().includes(q) ||
      (g.interestTag || "").toLowerCase().includes(q)
    );
  }

  const renderGroupCard = (g) => {
    const unread = Number(unreadByGroupId[String(g.id)] || 0);
    const muted = isGroupMuted(g.id);
    const m = Number(g.members);
const membersLabel = m === 1
  ? t("groups.memberOne")
  : (m >= 2 && m <= 4)
    ? t("groups.memberFew", { count: m })
    : t("groups.memberMany", { count: m });
    return `
      <div class="listItem ${unread > 0 ? 'unread' : ''}" onclick="openGroup('${g.id}')" style="position:relative; padding-bottom:36px;">
        ${g.isCreator ? `<div style="
  position:absolute;
  bottom:10px;
  right:12px;
  max-width:110px;
  padding:6px 8px;
  border-radius:12px;
  font-size:10.5px;
  font-weight:900;
  line-height:1.15;
  text-align:center;
  word-break:break-word;
  color:#f4f8ff;
  background: rgba(9,12,24,.55);
  border:1px solid rgba(255,255,255,.14);
  box-shadow:
    0 6px 16px rgba(0,0,0,.35),
    0 0 0 1px rgba(255,255,255,.04) inset,
    0 0 12px rgba(52,230,255,.18);
  backdrop-filter: blur(6px);
">${t("groups.createdByYouHtml")}</div>` : ``}
        <div class="listTop">
          <div class="listLeft">
            <div class="listAvatar">${premiumIcon("group", g.title || "Grupa")}</div>
            <div style="min-width:0;">
              <div class="listTitle">${g.title}</div>
              <div class="listMeta">#${g.interestTag} • ${membersLabel}</div>
            </div>
          </div>
          <div class="listRight">
            ${muted ? `<div style="font-size:14px;opacity:.7;">🔕</div>` : ``}
            ${unread > 0 ? `<div class="badgeMini">${unread}</div>` : ``}
          </div>
        </div>
        <div class="listBody">${g.desc}</div>
      </div>
    `;
  };

  let html = "";

  if (myGroups.length) {
    html += `
      <div class="card">
        <div class="sectionTitle">${t("groups.yourGroups", "Twoje grupy")}</div>
        <div class="sectionSub">${t("groups.yourGroupsSub")}</div>
        <div class="col mt12">
          ${myGroups.map(renderGroupCard).join("")}
        </div>
      </div>
    `;
  }

  html += `
    <div class="card ${myGroups.length ? "mt16" : ""}">
      <div class="sectionTitle">${t("groups.suggestedGroups", "Proponowane grupy")}</div>
      <div class="sectionSub">${t("groups.suggestedGroupsSub")}</div>
      <div class="col mt12">
        ${suggestedGroups.length ? suggestedGroups.map(renderGroupCard).join("") : `<div class="tMuted">${t("groups.noSuggestedGroups", "Brak proponowanych grup")}</div>`}
      </div>
    </div>
  `;

  list.innerHTML = html;

  const sug = $("groupPeopleSuggestions");
  if (sug) {
    sug.innerHTML = "";
    sug.style.display = "none";
  }
}

async function refreshChatBadgeCount() {
  const badge = $("badgeChats");
  if (!badge) return;

  if (!App.isLoggedIn || App.role !== "user") {
    badge.style.display = "none";
    return;
  }

  try {
    const data = await apiFetch("/messages/private");
    const items = Array.isArray(data?.data?.items) ? data.data.items : [];
    const unreadTotal = items.reduce((sum, c) => {
      const chatId = `pm_${c?.other_user_id}`;
      const muted = isChatMuted(chatId);
      return sum + (muted ? 0 : Number(c?.unread_count || 0));
    }, 0);

    if (unreadTotal > 0) {
      badge.textContent = String(unreadTotal);
      badge.style.display = "inline-flex";
    } else {
      badge.textContent = "0";
      badge.style.display = "none";
    }
  } catch (err) {
    console.error("chat badge refresh error", err);
    badge.style.display = "none";
  }
}

async function renderChatList() {
  const list = $("chatList");
  const q = ($("chatSearch")?.value || "").trim().toLowerCase();

  try {
    const data = await apiFetch("/messages/private");
    const items = Array.isArray(data?.data?.items) ? data.data.items : [];

    const chats = items
      .filter(c => !q || String(c.other_user_name || "").toLowerCase().includes(q))
      .map(c => {
        const existing = App.chats.find(x => String(x.with?.id) === String(c.other_user_id));
        const chatId = existing?.id || `pm_${c.other_user_id}`;
        const isPartner = String(c.other_user_role || existing?.with?.role || "").toLowerCase() === "partner";
        const displayName = isPartner
          ? (c.other_user_company || existing?.with?.company || c.other_user_name || `Organizator #${c.other_user_id}`)
          : (c.other_user_name || existing?.with?.nick || `${t("partnerMessages.defaultUser")} #${c.other_user_id}`);

        if (!existing) {
          App.chats.unshift({
            id: chatId,
            with: {
              id: c.other_user_id,
              nick: displayName,
              role: isPartner ? "partner" : "user",
              company: c.other_user_company || "",
              city: c.other_user_city || "",
              category: c.other_user_category || "",
              bio: c.other_user_bio || "",
              avatarUrl: c.other_user_avatar_url || "",
              logoUrl: c.other_user_logo_url || c.other_user_avatar_url || "",
              emoji: isPartner ? "" : "",
            },
            last: c.last_message || "",
            unread: Number(c.unread_count || 0),
            messages: [],
          });
        } else {
          existing.with = {
            ...(existing.with || {}),
            id: c.other_user_id,
            nick: displayName,
            role: isPartner ? "partner" : (existing.with?.role || "user"),
            company: c.other_user_company || existing.with?.company || "",
            city: c.other_user_city || existing.with?.city || "",
            category: c.other_user_category || existing.with?.category || "",
            bio: c.other_user_bio || existing.with?.bio || "",
            avatarUrl: c.other_user_avatar_url || existing.with?.avatarUrl || "",
            logoUrl: c.other_user_logo_url || existing.with?.logoUrl || c.other_user_avatar_url || existing.with?.avatarUrl || "",
            emoji: isPartner ? "" : (existing.with?.emoji || ""),
          };
          existing.last = c.last_message || existing.last || "";
          existing.unread = Number(c.unread_count || existing.unread || 0);
        }

        const rawUnread = Number(c.unread_count || 0);
        const muted = isChatMuted(chatId);
        const visualUnread = rawUnread;
        const badgeUnread = muted ? 0 : rawUnread;

        return {
          id: chatId,
          with: {
            ...(existing?.with || {}),
            id: c.other_user_id,
            nick: displayName,
            role: isPartner ? "partner" : (existing?.with?.role || "user"),
            company: c.other_user_company || existing?.with?.company || "",
            city: c.other_user_city || existing?.with?.city || "",
            category: c.other_user_category || existing?.with?.category || "",
            bio: c.other_user_bio || existing?.with?.bio || "",
            avatarUrl: c.other_user_avatar_url || existing?.with?.avatarUrl || "",
            logoUrl: c.other_user_logo_url || existing?.with?.logoUrl || c.other_user_avatar_url || existing?.with?.avatarUrl || "",
            emoji: isPartner ? "" : (existing?.with?.emoji || ""),
          },
          last: c.last_message || "",
          unread: visualUnread,
          badgeUnread,
          rawUnread,
        };
      });

    const finalChats = chats;

    if (list) {
      if (!(finalChats || []).length) {
        list.innerHTML = `<div class="tMuted">${t("partnerMessages.empty")}</div>`;
      } else {
        list.innerHTML = (finalChats || []).map(c => {
        const muted = isChatMuted(c.id);
        return `
        <div class="listItem ${c.unread > 0 ? 'unread' : ''}" onclick="openChat('${c.id}')">
          <div class="listTop">
            <div class="listLeft">
              <div class="listAvatar" style="border-radius:999px;overflow:hidden;border:2px solid rgba(255,255,255,.18);box-shadow:0 10px 26px rgba(0,0,0,.22);">${(() => {
                const avatarSrc = c.with.logoUrl || c.with.avatarUrl || "";
                if (avatarSrc) {
                  const src = String(avatarSrc).startsWith("http") ? avatarSrc : `${API_BASE_URL}${avatarSrc}`;
                  return `<img src="${src}" alt="${escapeHtml(c.with.nick || "Rozmowa")}" style="width:100%;height:100%;object-fit:cover;border-radius:999px;" />`;
                }
                if (c.with.role === "partner") return premiumIcon("org", c.with.company || c.with.nick || "Organizator");
                return `<div class="userAvatarFallback" style="border-radius:999px;${premiumAvatarStyle(getAvatarGradient(c.with.nick || "U"))}" data-name="${escapeHtml(c.with.nick || "U")}">${avatarInitial(c.with.nick || "U")}</div>`;
              })()}</div>
              <div style="min-width:0;">
                <div class="listTitle">${c.with.nick}</div>
                <div class="listMeta">${c.last || "—"}</div>
              </div>
            </div>
            ${(muted || c.unread > 0) ? `<div class="listRight">${muted ? `<div style="font-size:14px;opacity:.7;">🔕</div>` : ``}${c.unread > 0 ? `<div class="badgeMini">${c.unread}</div>` : ``}</div>` : ``}
          </div>
        </div>
      `;
      }).join("");
      }
    }

    const badge = $("badgeChats");
    if (badge) {
      const unreadTotal = (finalChats || []).reduce((sum, c) => sum + Number(c.badgeUnread || 0), 0);
      if (unreadTotal > 0) {
        badge.textContent = String(unreadTotal);
        badge.style.display = "inline-flex";
      } else {
        badge.textContent = "0";
        badge.style.display = "none";
      }
    }
  } catch (err) {
    console.error("renderChatList failed", err);

    const fallbackChats = (App.chats || []).filter(c =>
      c?.with?.id != null &&
      (!q || String(c.with?.nick || "").toLowerCase().includes(q))
    );

    if (list) {
      if (!fallbackChats.length) {
        list.innerHTML = `<div class="tMuted">${t("partnerMessages.loadFailed")}</div>`;
      } else {
        list.innerHTML = fallbackChats.map(c => `
        <div class="listItem" onclick="openChat('${c.id}')">
          <div class="listTop">
            <div class="listLeft">
              <div class="listAvatar">${premiumIcon("chat", c.with?.nick || "Czat")}</div>
              <div style="min-width:0;">
                <div class="listTitle">${c.with?.nick || "Czat"}</div>
                <div class="listMeta">${c.last || "—"}</div>
              </div>
            </div>
          </div>
        </div>
      `).join("");
      }
    }
  }
}

function renderPartnerEvents() {
  const list = $("partnerEventsList");
  if (!list) return;

  list.innerHTML = `<div class="tMuted">${t("partnerEvent.loading")}</div>`;

  const events = Array.isArray(App.partnerEvents) ? App.partnerEvents : [];

  const now = new Date();

  const formatWhen = (value) => {
    if (!value) return "Brak daty";
    const d = new Date(value);
    if (Number.isNaN(d.getTime())) return String(value);
    return d.toLocaleString("pl-PL", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const priceText = (ev) => {
    if (ev.pricing_type === "free") return t("eventDetail.ticketFree");
    if (ev.pricing_type === "paid_fixed") {
      return ev.price_fixed != null ? `${Math.round(Number(ev.price_fixed) / 100)} zł` : t("eventDetail.ticketPaid");
    }
    if (ev.pricing_type === "paid_range") {
      if (ev.price_min != null && ev.price_max != null) {
        return `${Math.round(Number(ev.price_min) / 100)}-${Math.round(Number(ev.price_max) / 100)} zł`;
      }
      return t("eventDetail.ticketPaid");
    }
    return "—";
  };

  const getLifecycleLabel = (ev) => {
    const status = String(ev.status || "draft").toLowerCase();
    const endAt = ev?.end_at ? new Date(ev.end_at) : null;

    if (status === "archived") return t("partnerEvent.sectionArchivedTitle");
    if (status === "draft") return t("partnerEvent.statusDraft");
    if (status === "published" && endAt && !Number.isNaN(endAt.getTime()) && endAt < now) return t("partnerEvent.sectionFinishedTitle");
    if (status === "published") return t("partnerEvent.sectionActiveTitle");
    return status;
  };

    const renderEventCard = (ev) => {
      const isFeatured = getPartnerPlanRules().canFeatureEvents;
      const signups = Number(ev.signups_count || 0);
      const saves = Number(ev.saves_count || 0);
      const capacityText = ev.capacity != null
        ? t("partnerEvent.capacityShort", { used: signups, capacity: ev.capacity })
        : t("partnerEvent.noCapacityLimit");
      const freeSpotsText = ev.capacity != null
        ? t("partnerEvent.freeSpotsShort", { count: ev.spots_left != null ? ev.spots_left : "—" })
        : "";
      const archiveLabel = (() => {
        const endAt = ev?.end_at ? new Date(ev.end_at) : null;
        return endAt && !Number.isNaN(endAt.getTime()) && endAt < now
          ? t("partnerEvent.archiveShort")
          : t("partnerEvent.closeShort");
      })();
      return `
      <div class="listItem ${isFeatured ? "isFeatured" : ""}" onclick="openPartnerEventEditor('${ev.id}')">
        <div class="listTop">
          <div class="listLeft">
            <div class="listAvatar">${premiumIcon("calendar", "Wydarzenie")}</div>
            <div style="min-width:0;">
              <div class="listTitle">${ev.title || "Bez nazwy"}</div>
              <div class="listMeta">📅 ${formatWhen(ev.start_at)}</div>
              <div class="listMeta">📍 ${ev.where || "Brak miejsca"}${ev.city ? ` · ${ev.city}` : ""}</div>
              ${isFeatured ? `<div class="mt12"><span class="listTag featured">${t("partnerEvent.featured")}</span></div>` : ""}
            </div>
          </div>
          <div class="listRight">
            <div class="listTag ${ev.pricing_type === 'free' ? '' : 'paid'}">${priceText(ev)}</div>
          </div>
        </div>
        <div class="listBody" style="display:flex;flex-wrap:wrap;gap:8px;align-items:center;">
          <span class="eventStatusBadge">${getLifecycleLabel(ev)}</span>
          <span class="listTag">👥 ${t("partnerEvent.signupsShort", { count: signups })}</span>
          <span class="listTag">👁 ${t("partnerEvent.observersShort", { count: saves })}</span>
          <span class="listTag">${capacityText}</span>
          ${freeSpotsText ? `<span class="listTag">${freeSpotsText}</span>` : ""}
        </div>
        ${String(ev.status || "").toLowerCase() === "draft" ? `
          <div class="row mt12">
            <button class="btn" type="button" onclick="event.stopPropagation(); quickPublishPartnerEvent('${ev.id}')">Opublikuj</button>
          </div>
        ` : ""}
        ${String(ev.status || "").toLowerCase() !== "draft" ? `
          <div class="row mt12" style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
            <button class="btn secondary small" type="button" onclick="event.stopPropagation(); openPartnerEventParticipantsView('${ev.id}')">${t("partnerEvent.participantsAction")}</button>
            ${String(ev.status || "").toLowerCase() === "published" ? `<button class="btn secondary small" style="border-color:rgba(255,120,160,.42);" type="button" onclick="event.stopPropagation(); quickArchivePartnerEvent('${ev.id}')">${archiveLabel}</button>` : ""}
          </div>
        ` : ""}
      </div>
    `;
    };

  const drafts = [];
  const active = [];
  const finished = [];
  const archived = [];

  events.forEach((ev) => {
    const status = String(ev.status || "draft").toLowerCase();
    const endAt = ev?.end_at ? new Date(ev.end_at) : null;

    if (status === "archived") {
      archived.push(ev);
    } else if (status === "draft") {
      drafts.push(ev);
    } else if (status === "published" && endAt && !Number.isNaN(endAt.getTime()) && endAt < now) {
      finished.push(ev);
    } else {
      active.push(ev);
    }
  });

  App.partnerEventSectionsOpen = App.partnerEventSectionsOpen || {};

  const eventCountLabel = (count) => {
    const n = Math.abs(Number(count || 0));
    if (n === 1) return t("partnerEvent.countOne");
    if (n % 10 >= 2 && n % 10 <= 4 && !(n % 100 >= 12 && n % 100 <= 14)) return t("partnerEvent.countFew", { count: n });
    return t("partnerEvent.countMany", { count: n });
  };

  const sectionCopy = {
    active: {
      title: t("partnerEvent.sectionActiveTitle"),
      desc: t("partnerEvent.sectionActiveDesc"),
      icon: "📅",
    },
    drafts: {
      title: t("partnerEvent.sectionDraftsTitle"),
      desc: t("partnerEvent.sectionDraftsDesc"),
      icon: "✎",
    },
    finished: {
      title: t("partnerEvent.sectionFinishedTitle"),
      desc: t("partnerEvent.sectionFinishedDesc"),
      icon: "✓",
    },
    archived: {
      title: t("partnerEvent.sectionArchivedTitle"),
      desc: t("partnerEvent.sectionArchivedDesc"),
      icon: '<span class="partnerEventArchiveIcon" aria-hidden="true"></span>',
    },
  };

  const renderSection = (key, items, defaultOpen = false) => {
    const count = items.length;
    const isOpen = App.partnerEventSectionsOpen[key] ?? defaultOpen;
    const copy = sectionCopy[key];

    return `
      <div class="card mt16 partnerEventSection ${isOpen ? "isOpen" : "isCollapsed"}" data-section="${key}">
        <button class="partnerEventSectionHeader" type="button" onclick="togglePartnerEventSection('${key}')">
          <div>
            <div class="partnerEventSectionIcon">${copy.icon}</div>
            <div class="partnerEventSectionText">
              <div class="partnerEventSectionTitle">${copy.title}</div>
              <div class="partnerEventSectionDesc">${copy.desc}</div>
              <div class="partnerEventSectionMeta">${eventCountLabel(count)}</div>
            </div>
          </div>
          <div class="partnerEventSectionChevron">${isOpen ? "−" : "+"}</div>
        </button>

        ${isOpen ? `
          <div class="col mt12">
            ${items.length
              ? items.map(renderEventCard).join("")
              : `<div class="tMuted">${t("partnerEvent.emptySection")}</div>`}
          </div>
        ` : ""}
      </div>
    `;
  };

  list.innerHTML = [
    renderSection("active", active, true),
    renderSection("drafts", drafts, drafts.length > 0),
    renderSection("finished", finished, false),
    renderSection("archived", archived, false),
  ].join("");
}

function togglePartnerEventSection(key) {
  App.partnerEventSectionsOpen = App.partnerEventSectionsOpen || {};
  App.partnerEventSectionsOpen[key] = !(App.partnerEventSectionsOpen[key] ?? false);
  renderPartnerEvents();
}

async function quickPublishPartnerEvent(eventId) {
  if (!eventId) return;

  try {
    const publishBlockMessage = getPartnerPublishLimitBlockMessage();
    if (publishBlockMessage) {
      toast(publishBlockMessage);
      return;
    }

    const data = await apiFetch(`/partners/events/${eventId}/publish`, {
      method: "POST",
    });

    if (!data?.success || !data?.data) {
      toast(data?.error?.message || t("partnerEvent.publishFailed"));
      return;
    }

    await loadPartnerEvents();
    if (App.currentView === "S9_PARTNER_EVENTS") renderPartnerEvents();
    toast(t("partnerEvent.quickPublished"));
  } catch (err) {
    toast(err?.userMessage || t("partnerEvent.publishFailed"));
  }
}


async function quickArchivePartnerEvent(eventId) {
  if (!eventId) return;

  try {
    const data = await apiFetch(`/partners/events/${eventId}/archive`, {
      method: "POST",
    });

    if (!data?.success || !data?.data) {
      toast(data?.error?.message || t("partnerEvent.archiveFailed"));
      return;
    }

    await loadPartnerEvents();
    if (App.currentView === "S9_PARTNER_EVENTS") renderPartnerEvents();
    toast(t("partnerEvent.archived"));
  } catch (err) {
    toast(err?.userMessage || t("partnerEvent.archiveFailed"));
  }
}


async function renderPartnerMsgList() {
  const list = $("partnerMsgList");
  if (!list) return;

  const q = ($("partnerMsgSearch")?.value || "").trim().toLowerCase();

  list.innerHTML = `<div class="tMuted">${t("partnerMessages.loading")}</div>`;

  try {
    const data = await apiFetch("/messages/private");
    const items = Array.isArray(data?.data?.items) ? data.data.items : [];

    const chats = items
      .filter(c => !q || String(c.other_user_name || "").toLowerCase().includes(q))
      .map(c => {
        const rawUnread = Number(c.unread_count || 0);
        const existing = App.chats.find(x => String(x.with?.id) === String(c.other_user_id));
        const chatId = existing?.id || `pm_${c.other_user_id}`;
        const muted = isChatMuted(chatId);
        const unread = rawUnread;
        const badgeUnread = muted ? 0 : rawUnread;

        if (!existing) {
          App.chats.unshift({
            id: chatId,
            with: {
              id: c.other_user_id,
              nick: c.other_user_name || `${t("partnerMessages.defaultUser")} #${c.other_user_id}`,
              role: c.other_user_role || "user",
              company: c.other_user_company || "",
              bio: c.other_user_bio || "",
              avatarUrl: c.other_user_avatar_url || "",
              emoji: c.other_user_role === "partner" ? "" : "",
            },
            last: c.last_message || "",
            unread,
            badgeUnread,
            rawUnread,
            messages: [],
          });
        } else {
          existing.with = {
            ...(existing.with || {}),
            id: c.other_user_id,
            nick: c.other_user_name || existing.with?.nick || `${t("partnerMessages.defaultUser")} #${c.other_user_id}`,
            role: c.other_user_role || existing.with?.role || "user",
            company: c.other_user_company || existing.with?.company || "",
            bio: c.other_user_bio || existing.with?.bio || "",
            avatarUrl: c.other_user_avatar_url || existing.with?.avatarUrl || "",
            emoji: existing.with?.emoji || (c.other_user_role === "partner" ? "" : ""),
          };
          existing.last = c.last_message || existing.last || "";
          existing.unread = unread;
          existing.badgeUnread = badgeUnread;
          existing.rawUnread = rawUnread;
        }

        return {
          id: chatId,
          with: {
            id: c.other_user_id,
            nick: c.other_user_name || `${t("partnerMessages.defaultUser")} #${c.other_user_id}`,
            role: c.other_user_role || "user",
            company: c.other_user_company || "",
            bio: c.other_user_bio || "",
            avatarUrl: c.other_user_avatar_url || "",
            emoji: "",
          },
          last: c.last_message || "",
          unread,
          badgeUnread,
          rawUnread,
        };
      });

    const finalChats = chats;

    if (!(finalChats || []).length) {
      list.innerHTML = `<div class="tMuted">${t("partnerMessages.empty")}</div>`;
    } else {
      list.innerHTML = (finalChats || []).map(c => {
        const muted = isChatMuted(c.id);
        return `
        <div class="listItem ${c.unread > 0 ? 'unread' : ''}" onclick="openChat('${c.id}')">
          <div class="listTop">
            <div class="listLeft">
              <div class="listAvatar">${premiumIcon("mail", c.with?.nick || "Rozmowa")}</div>
              <div style="min-width:0;">
                <div class="listTitle">${c.with.nick}</div>
                <div class="listMeta">${c.last || "—"}</div>
              </div>
            </div>
            ${(muted || c.unread > 0) ? `<div class="listRight">${muted ? `<div style="font-size:14px;opacity:.7;">🔕</div>` : ``}${c.unread > 0 ? `<div class="badgeMini">${c.unread}</div>` : ``}</div>` : ``}
          </div>
        </div>
      `;
      }).join("");
    }

    const badge = $("badgePartnerMsgs");
    if (badge) {
      const totalUnread = (finalChats || []).reduce((sum, c) => sum + Number(c.badgeUnread || 0), 0);
      badge.textContent = String(totalUnread);
      badge.style.display = totalUnread > 0 ? "inline-flex" : "none";
    }
  } catch (err) {
    console.error("renderPartnerMsgList failed", err);
    list.innerHTML = `<div class="tMuted">${t("partnerMessages.loadFailed")}</div>`;
  }
}

/* ------------------------- Interests (chips + suggestions) -------------------------- */
/**
 * We support 3 areas:
 * - Registration user: regInterestInput + regInterestChips + regInterestTypeahead
 * - Profile setup: interestInput + interestChips + interestTypeahead
 * - Settings: setInterestInput + setInterestChips + setInterestTypeahead
 *
 * Input behavior:
 * - User types (optionally with #)
 * - Press Enter or comma => add chip
 * - Clicking suggestion => add chip
 */
function initInterestInputs() {
  const configs = [
    { inputId: "regInterestInput", chipsId: "regInterestChips", taId: "regInterestTypeahead", target: "user" },
    { inputId: "interestInput", chipsId: "interestChips", taId: "interestTypeahead", target: "user" },
    { inputId: "setInterestInput", chipsId: "setInterestChips", taId: "setInterestTypeahead", target: "user" },
    { inputId: "peInterest", chipsId: null, taId: null, target: "event" }, // organizer create uses datalist only
  ];

  const suggestions = getInterestSuggestionsFromDatalist();

  configs.forEach(cfg => {
    const input = $(cfg.inputId);
    if (!input) return;
    const addBtn =
      cfg.inputId === "regInterestInput" ? $("regInterestAddBtn") :
      cfg.inputId === "interestInput" ? $("interestAddBtn") :
      cfg.inputId === "setInterestInput" ? $("setInterestAddBtn") :
      null;
    if (addBtn && !addBtn.dataset.bound) {
      addBtn.addEventListener("click", () => {
        const val = input.value.trim();
        if (!val) return;

        const parts = val
          .split(/[;,\n]+/)
          .map(x => normalizeTag(x))
          .filter(Boolean);

        if (!parts.length) return;

        parts.forEach(tag => addUserInterest(tag, cfg.chipsId));
        input.value = "";
        hideTypeahead(cfg.taId);
        renderAll();
      });
      addBtn.dataset.bound = "1";
    }

    // Key handlers
    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === "," ) {
        e.preventDefault();

        if (cfg.target === "event") {
          commitSingleEventTag();
          return;
        }

        const val = input.value.trim();
        const parts = val
          .split(/[;,\n]+/)
          .map(x => normalizeTag(x))
          .filter(Boolean);

        if (!parts.length) return;

        parts.forEach(tag => addUserInterest(tag, cfg.chipsId));
        input.value = "";
        hideTypeahead(cfg.taId);
        renderAll();
      }
      if (e.key === "Escape") hideTypeahead(cfg.taId);
    });

    input.addEventListener("input", () => {
      if (!cfg.taId) return; // no typeahead needed
      const q = normalizeTag(input.value.trim());
      if (!q) { hideTypeahead(cfg.taId); return; }
      const items = suggestions
        .filter(s => s.toLowerCase().startsWith(q.toLowerCase()))
        .slice(0, 12);
      renderTypeahead(cfg.taId, items, (picked) => {
        addUserInterest(picked, cfg.chipsId);
        input.value = "";
        hideTypeahead(cfg.taId);
        renderAll();
      });
    });
  });

  // initial chips render
  renderInterestChips("regInterestChips");
  renderInterestChips("interestChips");
  refreshInterestUi();
  renderInterestChips("setInterestChips");
}

function getInterestSuggestionsFromDatalist() {
  const dl = $("interestsDatalist");
  if (!dl) return [];
  const opts = Array.from(dl.querySelectorAll("option"))
    .map(o => (o.getAttribute("value") || "").trim())
    .filter(Boolean);
  return Array.from(new Set(opts));
}

const INTEREST_CANONICAL_ALIASES = {
  "ai": "AI",
  "artificial intelligence": "AI",
  "ux/ui": "UX",
  "ui/ux": "UX",
  "user experience": "UX",
  "coffee": "kawa",
  "cafe": "kawiarnie",
  "tea": "herbata",
  "matcha tea": "matcha",
  "movies": "kino",
  "movie": "kino",
  "films": "filmy",
  "series": "seriale",
  "tv series": "seriale",
  "concert": "koncerty",
  "concerts": "koncerty",
  "festival": "festiwale",
  "festivals": "festiwale",
  "photography": "fotografia",
  "photo": "fotografia",
  "gym": "siłownia",
  "running": "bieganie",
  "walks": "spacer",
  "walking": "spacer",
  "hiking": "trekking",
  "mountains": "góry",
  "climbing": "wspinaczka",
  "yoga": "joga",
  "pilates workout": "pilates",
  "swimming": "pływanie",
  "dance": "taniec",
  "martial arts": "sztuki walki",
  "boxing": "boks",
  "technology": "technologia",
  "tech": "technologia",
  "programming": "programowanie",
  "coding": "programowanie",
  "board games": "planszówki",
  "boardgaming": "planszówki",
  "rpg games": "RPG",
  "esport": "e-sport",
  "anime shows": "anime",
  "mangas": "manga",
  "reading": "czytanie",
  "books": "książki",
  "personal growth": "rozwój osobisty",
  "languages": "nauka języków",
  "language learning": "nauka języków",
  "meditation": "medytacja",
  "science": "nauka",
  "drawing": "rysunek",
  "painting": "malarstwo",
  "graphics": "grafika",
  "illustration": "ilustracja",
  "ceramics": "ceramika",
  "crafts": "rękodzieło",
  "writing": "pisanie",
  "travel": "podróże",
  "travels": "podróże",
  "city breaks": "city break",
  "camping trips": "camping",
  "dogs": "psy",
  "cats": "koty",
  "animals": "zwierzęta",
  "plants": "rośliny",
  "volunteering": "wolontariat",
  "events": "eventy",
  "network": "networking",
  "business": "biznes",
  "content creation": "tworzenie treści",
  "video editing": "montaż wideo",
  "podcasts": "podcasty",
  "podcasting": "podcast",
  "standup": "stand-up",
  "comedy": "komedia",
  "cafes": "kawiarnie",
  "urban culture": "kultura miejska",
  "architecture": "architektura",
  "fashion": "moda",
  "skincare": "pielęgnacja",
  "tattoos": "tatuaże",
  "cars": "motoryzacja",
  "motorcycles": "motocykle",
  "vinyl": "winyle",
  "logic games": "gry logiczne",
  "crosswords": "krzyżówki",
  "puzzles": "łamigłówki",
  "escape rooms": "escape roomy",
  "crypto": "kryptowaluty",
  "personal finance": "finanse osobiste",
  "investing": "inwestowanie",
  "real estate": "nieruchomości",
  "healthy food": "zdrowe jedzenie",
  "meal prep sunday": "meal prep",
  "eco": "ekologia",
  "recycling": "recykling",
  "planning": "planowanie",
  "organization": "organizacja",
  "mindset work": "mindset",
};

function normalizeTag(val) {
  if (!val) return "";

  const raw = val.replace(/^#/, "").trim().replace(/\s+/g, " ").slice(0, 40);
  if (!raw) return "";

  const suggestions = getInterestSuggestionsFromDatalist();
  const canonicalByLower = new Map(suggestions.map(x => [x.toLowerCase(), x]));

  const lower = raw.toLowerCase();
  if (canonicalByLower.has(lower)) {
    return canonicalByLower.get(lower);
  }

  const aliasTarget = INTEREST_CANONICAL_ALIASES[lower];
  if (aliasTarget) {
    return canonicalByLower.get(aliasTarget.toLowerCase()) || aliasTarget;
  }

  return raw;
}


function normalizeCity(raw) {
  const value = String(raw || "")
    .replace(/\s+/g, " ")
    .trim();

  if (!value) return "";

  const aliases = {
    "wawa": "Warszawa",
    "warszawa": "Warszawa",
    "krakow": "Kraków",
    "kraków": "Kraków",
    "gdansk": "Gdańsk",
    "gdańsk": "Gdańsk",
    "wroclaw": "Wrocław",
    "wrocław": "Wrocław",
    "poznan": "Poznań",
    "poznań": "Poznań"
  };

  const lower = value.toLocaleLowerCase("pl-PL");
  if (aliases[lower]) return aliases[lower];

  return value
    .toLocaleLowerCase("pl-PL")
    .replace(/(^|[\s-])([\p{L}])/gu, (_, sep, ch) => sep + ch.toLocaleUpperCase("pl-PL"));
}

async function syncUserInterests() {
  if (!App.isLoggedIn || App.role !== "user") return;

  try {
    const data = await apiFetch("/users/me", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify((() => {
        const payload = {
          zainteresowania: Array.isArray(App.user.interests) ? App.user.interests : [],
        };
        const trainerPlan = ["premium", "vip"].includes(String(App.user.plan || "").toLowerCase());
        const trainerInterests = Array.isArray(App.user.trainerInterests) ? App.user.trainerInterests : [];
        if (trainerPlan && trainerInterests.length) {
          payload.trainer_interests = trainerInterests;
        }
        return payload;
      })()),
    });

    if (data?.success && data?.data) {
      const backendInterests = Array.isArray(data.data.zainteresowania) ? data.data.zainteresowania : [];
      App.user.interests = backendInterests;
      App.user.trainerInterests = Array.isArray(data.data.trainer_interests) ? data.data.trainer_interests : [];
      try { localStorage.setItem("usly_user_interests", JSON.stringify(backendInterests)); } catch(_) {}
      renderInterestChips("setInterestChips");
      renderInterestChips("interestChips");
      renderInterestChips("regInterestChips");
      renderTrainerInterestBoxes();
    }
  } catch (err) {
    console.error("syncUserInterests failed", err);
  }
}

function addUserInterest(tag, chipsId) {
  const cleanTag = normalizeTag(tag);
  if (!cleanTag) return;
  const exists = App.user.interests.some(x => x.toLowerCase() === cleanTag.toLowerCase());
  if (exists) {
    toast(t("profileInterests.alreadyAdded"));
    return;
  }
  const count = Array.isArray(App.user.interests) ? App.user.interests.length : 0;
  if (!canAddMoreInterests(count)) {
    toast(t("profileInterests.limitToast"));
    return;
  }

  App.user.interests.push(cleanTag);
  try { localStorage.setItem("usly_user_interests", JSON.stringify(App.user.interests)); } catch(_) {}
  renderInterestChips(chipsId);
  syncUserInterests();
  toast(t("profileInterests.addedToast", { tag: cleanTag }));
}

function removeUserInterest(tag, chipsId) {
  const cleanTag = normalizeTag(tag);
  App.user.interests = App.user.interests.filter(x => x.toLowerCase() !== cleanTag.toLowerCase());
  App.user.trainerInterests = (Array.isArray(App.user.trainerInterests) ? App.user.trainerInterests : [])
    .filter(x => String(x).toLowerCase() !== cleanTag.toLowerCase());
  try { localStorage.setItem("usly_user_interests", JSON.stringify(App.user.interests)); } catch(_) {}
  refreshInterestUi();
  renderInterestChips(chipsId);
  syncUserInterests();
  toast(t("profileInterests.removedToast", { tag: cleanTag }));
}

function renderInterestChips(chipsId) {
  const box = $(chipsId);
  if (!box) return;

  box.innerHTML = "";
  App.user.interests.forEach(t => {
    const chip = makeChip(`#${t}`, () => removeUserInterest(t, chipsId));
    box.appendChild(chip);
  });
  renderTrainerInterestBoxes();
  refreshInterestUi();
}

function getTrainerInterestLimit() {
  const plan = String(App.user?.plan || "free").toLowerCase();
  if (plan === "vip") return 5;
  if (plan === "premium") return 2;
  return 0;
}

function isTrainerPlan() {
  return getTrainerInterestLimit() > 0;
}

function toggleTrainerInterest(tag) {
  const clean = normalizeTag(tag);
  if (!clean || !isTrainerPlan()) return;

  const current = Array.isArray(App.user.trainerInterests) ? App.user.trainerInterests : [];
  const exists = current.some(x => String(x).toLowerCase() === clean.toLowerCase());

  if (exists) {
    App.user.trainerInterests = current.filter(x => String(x).toLowerCase() !== clean.toLowerCase());
  } else {
    const limit = getTrainerInterestLimit();
    if (current.length >= limit) {
      toast(t("profileInterests.trainerLimitToast"));
      return;
    }
    App.user.trainerInterests = [...current, clean];
  }

  renderTrainerInterestBoxes();
  syncUserInterests();
}

function renderTrainerInterestBox(boxId) {
  const box = $(boxId);
  if (!box) return;

  const interests = Array.isArray(App.user.interests) ? App.user.interests : [];
  const trainerInterests = Array.isArray(App.user.trainerInterests) ? App.user.trainerInterests : [];
  const limit = getTrainerInterestLimit();

  if (!interests.length) {
    box.innerHTML = "";
    return;
  }

  if (!isTrainerPlan()) {
    box.innerHTML = `
      <div class="trainerInterestHeader">
        <div class="trainerInterestTitle">🎓 ${t("profileInterests.trainerTitle")}</div>
        <div class="trainerInterestSub">${t("profileInterests.trainerLocked")}</div>
      </div>
    `;
    return;
  }

  const limitText = String(App.user?.plan || "").toLowerCase() === "vip"
    ? t("profileInterests.trainerVipLimit")
    : t("profileInterests.trainerPremiumLimit");

  box.innerHTML = `
    <div class="trainerInterestHeader">
      <div class="trainerInterestTitle">🎓 ${t("profileInterests.trainerTitle")}</div>
      <div class="trainerInterestSub">${t("profileInterests.trainerSubtitle")}</div>
      <div class="trainerInterestLimit">${limitText} • ${trainerInterests.length}/${limit}</div>
    </div>
    <div class="trainerInterestChoices">
      ${interests.map(tag => {
        const active = trainerInterests.some(x => String(x).toLowerCase() === String(tag).toLowerCase());
        return `<button class="trainerInterestChip ${active ? "active" : ""}" type="button" onclick="toggleTrainerInterest(decodeURIComponent('${encodeURIComponent(String(tag))}'))">${active ? "🎓 " : ""}#${escapeHtml(tag)}</button>`;
      }).join("")}
    </div>
  `;
}

function renderTrainerInterestBoxes() {
  renderTrainerInterestBox("setTrainerInterestBox");
  renderTrainerInterestBox("setupTrainerInterestBox");
}

function renderPersonTrainerInterests(person) {
  const panel = $("personTrainerPanel");
  const content = $("personTrainerContent");
  if (!panel || !content) return;

  const trainerTags = Array.isArray(person?.trainerInterests) ? person.trainerInterests : [];
  if (!trainerTags.length) {
    panel.hidden = true;
    content.innerHTML = "";
    return;
  }

  panel.hidden = false;
  content.innerHTML = `
    <div class="personTrainerBox">
      <div class="personTrainerTitle">🎓 ${t("profileInterests.leadsClassesTitle")}</div>
      <div class="personTrainerChips">
        ${trainerTags.map(tag => `<span class="personTrainerChip">#${escapeHtml(tag)}</span>`).join("")}
      </div>
    </div>
  `;
}

function makeChip(text, onRemove) {
  const span = document.createElement("div");
  span.className = "chip";
  span.textContent = text;
  if (onRemove) {
    span.title = t("profileInterests.removeTitle");
    span.addEventListener("click", onRemove);
  }
  return span;
}

function getPartnerCategoryLabel(value) {
  const key = String(value || "").trim().toLowerCase();
  return key ? t(`partnerCategory.${key}`, String(value || "").trim()) : "";
}

function renderTypeahead(taId, items, onPick) {
  const box = $(taId);
  if (!box) return;
  if (!items.length) { hideTypeahead(taId); return; }

  box.classList.add("open");
  box.innerHTML = items.map(x => `<div class="taItem" data-val="${escapeHtml(x)}">#${escapeHtml(x)}</div>`).join("");

  Array.from(box.querySelectorAll(".taItem")).forEach(item => {
    item.addEventListener("click", () => {
      const val = item.getAttribute("data-val") || "";
      onPick?.(val);
    });
  });
}

function hideTypeahead(taId) {
  const box = $(taId);
  if (!box) return;
  box.classList.remove("open");
  box.innerHTML = "";
}

function escapeHtml(s) {
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

/* ------------------------- Age sliders -------------------------- */
function initAgeSliders() {
  // Registration
  const regFrom = $("regPrefAgeFrom");
  const regTo = $("regPrefAgeTo");
  const regFromVal = $("regPrefAgeFromVal");
  const regToVal = $("regPrefAgeToVal");

  if (regFrom && regTo) {
    const upd = () => {
      const f = Number(regFrom.value || 16);
      const t = Number(regTo.value || 99);
      if (regFromVal) regFromVal.textContent = String(f);
      if (regToVal) regToVal.textContent = String(t);
    };
    regFrom.addEventListener("input", upd);
    regTo.addEventListener("input", upd);
    upd();
  }

  // Settings
  const setFrom = $("setPrefAgeFrom");
  const setTo = $("setPrefAgeTo");
  const setFromVal = $("setPrefAgeFromVal");
  const setToVal = $("setPrefAgeToVal");

  if (setFrom && setTo) {
    const setAgeAny = $("setAgeAny");
    const syncAgeAnyUi = () => {
      const disabled = !!setAgeAny?.checked;
      setFrom.disabled = disabled;
      setTo.disabled = disabled;
      setFrom.style.opacity = disabled ? ".55" : "";
      setTo.style.opacity = disabled ? ".55" : "";
      setFrom.style.cursor = disabled ? "not-allowed" : "";
      setTo.style.cursor = disabled ? "not-allowed" : "";
    };

    const upd2 = () => {
      const f = Number(setFrom.value || 16);
      const t = Number(setTo.value || 99);
      if (setFromVal) setFromVal.textContent = String(f);
      if (setToVal) setToVal.textContent = String(t);
      syncAgeAnyUi();
    };
    setFrom.addEventListener("input", upd2);
    setTo.addEventListener("input", upd2);
    setAgeAny?.addEventListener("change", syncAgeAnyUi);
    upd2();
  }

  // Setup ageAny toggle
  const setupAgeAny = $("setupAgeAny");
  const setupFrom = $("setupPrefAgeFrom");
  const setupTo = $("setupPrefAgeTo");

  if (setupAgeAny && setupFrom && setupTo) {
    const updateSetupAgeState = () => {
      const disabled = !!setupAgeAny.checked;
      setupFrom.disabled = disabled;
      setupTo.disabled = disabled;
      setupFrom.style.opacity = disabled ? "0.5" : "1";
      setupTo.style.opacity = disabled ? "0.5" : "1";
      setupFrom.style.cursor = disabled ? "not-allowed" : "";
      setupTo.style.cursor = disabled ? "not-allowed" : "";
    };

    setupAgeAny.addEventListener("change", updateSetupAgeState);
    updateSetupAgeState();
  }
}

/* ------------------------- Char counters -------------------------- */
function initCharCounters() {
  // Setup bio
  const setupBio = $("setupBio");
  if (setupBio) {
    setupBio.addEventListener("input", () => safeSetText("bioCount", String(setupBio.value.length)));
    safeSetText("bioCount", String(setupBio.value.length));
  }

  // Settings bio
  const setBio = $("setBio");
  if (setBio) {
    setBio.addEventListener("input", () => safeSetText("setBioCount", String(setBio.value.length)));
    safeSetText("setBioCount", String(setBio.value.length));
  }

  // Partner about
  const regOrgAbout = $("regOrgAbout");
  if (regOrgAbout) {
    regOrgAbout.addEventListener("input", () => safeSetText("regOrgAboutCount", String(regOrgAbout.value.length)));
    safeSetText("regOrgAboutCount", String(regOrgAbout.value.length));
  }
  const setOrgAbout = $("setOrgAbout");
  if (setOrgAbout) {
    setOrgAbout.addEventListener("input", () => safeSetText("setOrgAboutCount", String(setOrgAbout.value.length)));
    safeSetText("setOrgAboutCount", String(setOrgAbout.value.length));
  }
}

/* ------------------------- Geolocation (punkt 12) -------------------------- */
function approximateCoordinate(value) {
  const number = Number(value);
  return Number.isFinite(number) ? Math.round(number * 100) / 100 : null;
}

function initGeolocation() {
  // REQUIRED: bind by id="btnUseLocation" without inline onclick
  const btn = $("btnUseLocation");
  if (!btn) return;

  btn.addEventListener("click", useCurrentLocationForCity);
}

// Global function name as requested (punkt 12)
function useCurrentLocationForCity() {
  if (!navigator.geolocation) {
    toast(t("geo.unavailable"));
    return;
  }

  toast(t("geo.fetching"));
  navigator.geolocation.getCurrentPosition(
    (pos) => {
      const lat = approximateCoordinate(pos.coords.latitude);
      const lng = approximateCoordinate(pos.coords.longitude);
      if (lat == null || lng == null) {
        toast(t("geo.failed"));
        return;
      }

      // Save to hidden fields (backend-ready)
      const latEl = $("regGeoLat");
      const lngEl = $("regGeoLng");
      if (latEl) latEl.value = String(lat);
      if (lngEl) lngEl.value = String(lng);

      App.user.geo.lat = String(lat);
      App.user.geo.lng = String(lng);

      const city = $("regCity");
      if (city && App.role === "user") city.value = t("geo.fetchingCity");

      fetch(`https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${encodeURIComponent(lat)}&lon=${encodeURIComponent(lng)}&zoom=10&addressdetails=1`)
        .then((r) => r.ok ? r.json() : null)
        .then((geoData) => {
          const a = geoData?.address || {};
          const cityName = a.city || a.town || a.village || a.municipality || a.county || "";
          if (cityName) {
            App.user.city = cityName;
            if (city && App.role === "user") city.value = cityName;
          } else if (city && App.role === "user") {
            city.value = t("geo.locationFetched");
          }
          toast(t("geo.locationSet"));
        })
        .catch(() => {
          if (city && App.role === "user") city.value = t("geo.locationFetched");
          toast(t("geo.locationSet"));
        });
    },
    () => {
      const city = $("regCity");
      if (city && App.role === "user") city.value = t("geo.enableLocation");
      toast(t("geo.failed"));
    },
    { enableHighAccuracy: true, timeout: 8000, maximumAge: 120000 }
  );
}

/* ------------------------- Tabbar + Active states -------------------------- */
function updateTabbars() {
  const userBar = $("tabbarUser");
  const partnerBar = $("tabbarPartner");

  const publicViews = ["S0_WELCOME", "S1_LOGIN", "S2_REGISTER"];
  if (!App.isLoggedIn || publicViews.includes(App.currentView) || App.role === "admin") {
    hide(userBar);
    hide(partnerBar);
    return;
  }

  // Show only relevant bar
  if (App.role === "user") {
    show(userBar);
    hide(partnerBar);
  } else {
    hide(userBar);
    show(partnerBar);
  }

  // Active tab highlight based on current view
  setActiveTabs();
}

function setActiveTabs() {
  // clear
  document.querySelectorAll(".tabbar button").forEach(b => b.classList.remove("active", "on"));

  const v = App.currentView;

  // User tabs
  if (App.role === "user") {
    if (v.startsWith("S4")) $("tabNearby")?.classList.add("active");
    else if (v.startsWith("S6")) $("tabChats")?.classList.add("active");
    else if (v.startsWith("S7")) $("tabEvents")?.classList.add("active");
    else if (v.startsWith("S8")) $("tabGroups")?.classList.add("active");
    else if (v.startsWith("S10")) $("tabSettingsUser")?.classList.add("active");
  } else {
    // Partner tabs — keep behavior consistent with user tabbar on nested partner views.
    if (v === "S9_PARTNER") $("ptabDash")?.classList.add("active");
    else if (v === "S9_PARTNER_CREATE") $("ptabCreate")?.classList.add("active");
    else if (v.startsWith("S9_PARTNER_EVENT") || v === "S9_PARTNER_EVENTS") $("ptabMyEvents")?.classList.add("active");
    else if (v.startsWith("S9_PARTNER_MESSAGE")) $("ptabMsgs")?.classList.add("active");
    else if (v.startsWith("S10")) $("ptabSettings")?.classList.add("active");
  }
}

/* ------------------------- Helpers: matching interests -------------------------- */
function commonInterests(person) {
  const a = (App.user.interests || []).map(x => x.toLowerCase());
  const b = (person.interests || []).map(x => x.toLowerCase());
  return a.filter(x => b.includes(x));
}

function sharedScore(person) {
  const common = commonInterests(person).length;
  const base = Math.max(1, App.user.interests.length);
  return Math.min(99, Math.round((common / base) * 100));
}


function distanceKm(lat1, lng1, lat2, lng2) {
  const R = 6371;
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLng = (lng2 - lng1) * Math.PI / 180;
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
    Math.sin(dLng / 2) * Math.sin(dLng / 2);
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

function formatDistanceFromMe(person) {
  const rawMyLat = App.user?.geo?.lat;
  const rawMyLng = App.user?.geo?.lng;
  const rawLat = person?.location_lat;
  const rawLng = person?.location_lng;

  const myLat = Number(rawMyLat);
  const myLng = Number(rawMyLng);
  const lat = Number(rawLat);
  const lng = Number(rawLng);

  const rawDistance = person?.distance_km;
  let d = rawDistance != null && rawDistance !== "" ? Number(rawDistance) : NaN;

  if (
    rawMyLat != null && rawMyLat !== "" &&
    rawMyLng != null && rawMyLng !== "" &&
    rawLat != null && rawLat !== "" &&
    rawLng != null && rawLng !== "" &&
    Number.isFinite(myLat) &&
    Number.isFinite(myLng) &&
    Number.isFinite(lat) &&
    Number.isFinite(lng)
  ) {
    const toRad = value => value * Math.PI / 180;
    const R = 6371;
    const dLat = toRad(lat - myLat);
    const dLng = toRad(lng - myLng);
    const a =
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos(toRad(myLat)) * Math.cos(toRad(lat)) *
      Math.sin(dLng / 2) * Math.sin(dLng / 2);
    d = R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  }

  if (!Number.isFinite(d)) return "";
  if (d < 1) return t("nearby.distanceUnder1", "< 1 km od Ciebie");
  return t("nearby.distanceKm", { km: String(Math.round(d * 10) / 10).replace(".", ",") });
}

function suggestPeopleByInterest(tag) {
  const t = tag.toLowerCase();
  return App.people.filter(p => (p.interests || []).map(x => x.toLowerCase()).includes(t));
}

function matchesUserEventInterest(ev) {
  const mine = (App.user.interests || []).map(x => normalizeTag(String(x || ""))).filter(Boolean);
  const eventTags = Array.isArray(ev?.interests) && ev.interests.length
    ? ev.interests
    : [ev?.interest];

  const normalizedEventTags = eventTags.map(x => normalizeTag(String(x || ""))).filter(Boolean);
  return normalizedEventTags.some(tag => mine.includes(tag));
}

function getUserNearbyRadiusKm() {
  const raw = App.user?.nearbyRadiusKm || App.user?.nearby_radius_km || 25;
  const n = Number(raw);
  return Number.isFinite(n) && n > 0 ? n : 25;
}

function getEventDistanceKm(ev) {
  const myLat = Number(App.user?.geo?.lat);
  const myLng = Number(App.user?.geo?.lng);
  const evLat = Number(ev?.location_lat);
  const evLng = Number(ev?.location_lng);

  if (!Number.isFinite(myLat) || !Number.isFinite(myLng) || !Number.isFinite(evLat) || !Number.isFinite(evLng)) {
    return null;
  }

  return distanceKm(myLat, myLng, evLat, evLng);
}

function isEventInNearbyRadius(ev) {
  const d = getEventDistanceKm(ev);
  if (d == null) return false;
  return d <= getUserNearbyRadiusKm();
}

function priceLabel(ev) {
  if (ev.paidMode === "paid_fixed") return `${ev.price} zł`;
  if (ev.paidMode === "paid_range") return `${ev.priceFrom}–${ev.priceTo} zł`;
  return "0 zł";
}

function mapApiPersonToViewModel(p) {
  return {
    id: String(p.user_id),
    nick: p.nick || "Uzytkownik",
    city: p.miasto || "",
    age: Number.isFinite(Number(p.age)) ? Number(p.age) : 0,
    emoji: "",
    interests: Array.isArray(p.zainteresowania) ? p.zainteresowania : [],
    trainerInterests: Array.isArray(p.trainer_interests) ? p.trainer_interests : [],
    sharedTrainerInterests: Array.isArray(p.shared_trainer_interests) ? p.shared_trainer_interests : [],
    bio: p.bio || "",
    avatarUrl: p.avatar_url || "",
    distance_km: p.distance_km ?? null,
    location_lat: p.location_lat ?? null,
    location_lng: p.location_lng ?? null,
  };
}

function normalizeBlockedReason(reason, fallbackKey = "chat.blocked.content") {
  const value = String(reason || "").trim();
  if (!value) return t(fallbackKey);

  const lower = value.toLowerCase();
  if (
    lower.includes("the content was blocked by usly moderation") ||
    lower.includes("content was blocked")
  ) {
    return t(fallbackKey);
  }

  if (
    lower.includes("links are currently blocked") ||
    lower.includes("message was not delivered")
  ) {
    return t("chat.blocked.link");
  }

  return value;
}

function mapApiGroupToViewModel(g) {
  return {
    id: String(g.id),
    title: g.title || "Grupa",
    interestTag: g.interest_tag || "",
    members: Number(g.members_count || 0),
    desc: g.description || "",
    isCreator: !!g.is_creator,
  };
}

function toLocalDateTimeInputValue(value) {
  if (!value) return "";
  const raw = String(value).trim().replace(" ", "T");
  const normalized = /[zZ]|[+-]\d\d:\d\d$/.test(raw) ? raw : `${raw}Z`;
  const d = new Date(normalized);
  if (Number.isNaN(d.getTime())) return raw.slice(0, 16);
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function toLocalApiDateTime(value) {
  if (!value) return null;
  const raw = String(value).trim();
  return raw.length === 16 ? `${raw}:00` : raw;
}

function addHourToLocalDateTime(value) {
  const raw = String(value || "").trim();
  const d = new Date(raw);
  if (Number.isNaN(d.getTime())) return null;
  const shifted = new Date(d.getTime() + 60 * 60 * 1000);
  const pad = (n) => String(n).padStart(2, "0");
  return `${shifted.getFullYear()}-${pad(shifted.getMonth() + 1)}-${pad(shifted.getDate())}T${pad(shifted.getHours())}:${pad(shifted.getMinutes())}:00`;
}

function mapApiEventToViewModel(e) {
  const start = e?.start_at ? new Date(e.start_at) : null;
  const when =
    start && !Number.isNaN(start.getTime())
      ? start.toLocaleString("pl-PL", {
          day: "2-digit",
          month: "2-digit",
          hour: "2-digit",
          minute: "2-digit",
        })
      : t("personProfile.eventSoon");

  const eventInterests = Array.isArray(e.interest_tags) && e.interest_tags.length
    ? e.interest_tags.map(x => normalizeTag(String(x || ""))).filter(Boolean)
    : [normalizeTag(e.interest_tag || e.interest || e.category || e.tag || "wydarzenie")].filter(Boolean);

  return {
    id: String(e.id),
    title: e.title || "Wydarzenie",
    city: e.city || "",
    when: when,
    where: e.where || e.location || "",
    address: e.address || "",
    location_lat: e.location_lat ?? null,
    location_lng: e.location_lng ?? null,
    interest: eventInterests[0] || "wydarzenie",
    interests: eventInterests,
    desc: e.description || "",
    status: e.status || "draft",
    start_at: e.start_at || null,
    end_at: e.end_at || null,
    paidMode: e.pricing_type || "free",
    price: typeof e.price_fixed === "number" ? Math.round(e.price_fixed / 100) : null,
    priceFrom: typeof e.price_min === "number" ? Math.round(e.price_min / 100) : null,
    priceTo: typeof e.price_max === "number" ? Math.round(e.price_max / 100) : null,
    ticketLink: e.payment_link || "#",
    saved: false,
    interested: false,
    capacity: e.capacity ?? null,
    signupsCount: Number(e.signups_count || 0),
    spotsLeft: e.spots_left ?? null,
    organizer: {
      id: String(e.partner_user_id || e.organizer_id || ""),
      name:
        e.partner_name ||
        e.organizer_name ||
        e.partner_company ||
        e.company ||
        "Organizator",
      category:
        e.partner_category ||
        e.organizer_category ||
        e.kategoria_organizatora ||
        "",
      bio:
        e.partner_bio ||
        e.organizer_bio ||
        "",
      logoUrl:
        e.partner_logo_url ||
        e.organizer_logo_url ||
        "",
    },
  };
}


function nearbyLocationQuery(lat, lng) {
  const radius = Number(App.user?.nearbyRadiusKm || 25);
  if (lat == null || lng == null) return "";
  return `&lat=${encodeURIComponent(lat)}&lng=${encodeURIComponent(lng)}&radius_km=${encodeURIComponent(radius)}`;
}

async function loadNearbyPeople(lat = null, lng = null) {
  try {
    const data = await apiFetch(`/users/nearby?limit=20${nearbyLocationQuery(lat, lng)}`);
    const items = Array.isArray(data?.data?.items) ? data.data.items : [];
    App.people = items.map(mapApiPersonToViewModel);
    return true;
  } catch (err) {
    console.error("loadNearbyPeople failed", err);
    return false;
  }
}

async function loadNearbyEvents(lat, lng) {
  try {
    const data = await apiFetch(`/events?limit=100${nearbyLocationQuery(lat, lng)}`);
    const items = Array.isArray(data?.data?.items) ? data.data.items : [];
    App.nearbyEvents = items.map(mapApiEventToViewModel);
    return true;
  } catch (err) {
    console.error("loadNearbyEvents failed", err);
    App.nearbyEvents = [];
    return false;
  }
}

async function loadEvents(lat = null, lng = null) {
  try {
    const data = await apiFetch(`/events?limit=100${nearbyLocationQuery(lat, lng)}`);
    const items = Array.isArray(data?.data?.items) ? data.data.items : [];

    let joinedIds = new Set();
    try {
      const mine = await apiFetch("/users/me/events?limit=100");
      const myItems = Array.isArray(mine?.data?.items) ? mine.data.items : [];
      joinedIds = new Set(
        myItems
          .map(x => x?.signup?.event_id ?? x?.event?.id)
          .filter(v => v != null)
          .map(v => String(v))
      );
    } catch (err) {
      console.error("loadEvents joined state failed", err);
    }

    let savedIds = new Set();
    try {
      const savedRes = await apiFetch("/users/me/saved-events?limit=100");
      const savedItems = Array.isArray(savedRes?.data?.items) ? savedRes.data.items : [];
      savedIds = new Set(
        savedItems
          .map(x => x?.saved?.event_id ?? x?.event?.id)
          .filter(v => v != null)
          .map(v => String(v))
      );
    } catch (err) {
      console.error("loadEvents saved state failed", err);
    }

    App.events = items.map(raw => {
      const ev = mapApiEventToViewModel(raw);
      ev.interested = joinedIds.has(String(ev.id));
      ev.saved = savedIds.has(String(ev.id));
      return ev;
    });

    return true;
  } catch (err) {
    console.error("loadEvents failed", err);
    return false;
  }
}


async function loadMyGroups() {
  try {
    const data = await apiFetch("/groups/my");
    const items = Array.isArray(data?.data?.items) ? data.data.items : [];
    App.myGroups = items.map(mapApiGroupToViewModel);
    return true;
  } catch (err) {
    console.error("loadMyGroups failed", err);
    App.myGroups = [];
    return false;
  }
}

async function loadGroups() {
  try {
    const data = await apiFetch("/groups/suggested");
    const items = Array.isArray(data?.data?.items) ? data.data.items : [];
    App.groups = items.map(mapApiGroupToViewModel);
    return true;
  } catch (err) {
    console.error("loadGroups failed", err);
    App.groups = [];
    return false;
  }
}

async function loadPartnerEvents() {
  try {
    const data = await apiFetch("/partners/events?limit=100");
    const items = Array.isArray(data?.data?.items) ? data.data.items : [];

    const enriched = await Promise.all(
      items.map(async (ev) => {
        const endedAt = parseUslyTimestamp(ev?.end_at);
        const archivedStatsCutoff = Date.now() - 30 * 24 * 60 * 60 * 1000;
        if (endedAt && endedAt < archivedStatsCutoff) {
          return {
            ...ev,
            signups_count: 0,
            spots_left: null,
            capacity: ev?.capacity ?? null,
          };
        }

        try {
          const stats = await apiFetch(`/partners/events/${ev.id}/stats`);
          return {
            ...ev,
            signups_count: Number(stats?.data?.signups_count || 0),
            spots_left: stats?.data?.spots_left ?? null,
            capacity: stats?.data?.capacity ?? null,
          };
        } catch (err) {
          console.error(`loadPartnerEvents stats failed for event ${ev.id}`, err);
          return {
            ...ev,
            signups_count: 0,
            spots_left: null,
            capacity: null,
          };
        }
      })
    );

    App.partnerEvents = enriched;
    return true;
  } catch (err) {
    console.error("loadPartnerEvents failed", err);
    App.partnerEvents = [];
    return false;
  }
}

/* ------------------------- Render All -------------------------- */
function renderAll() {
  applyI18n();

  // Keep role labels consistent
  safeSetText("roleLabelLogin", App.role === "user" ? t("login.user", "Towarzysz") : t("login.partner", "Organizator"));
  safeSetText("roleLabelRegister", App.role === "user" ? t("login.user", "Towarzysz") : t("login.partner", "Organizator"));

  // Plan pills
  safeSetText("planPillSetup", App.user.plan.toUpperCase());
  document.querySelectorAll("#partnerPlanPill").forEach((el) => {
    el.textContent = String(App.partner.plan || "free").toUpperCase();
  });

  [
    "uplan_free", "uplan_plus", "uplan_premium", "uplan_vip",
    "uplan_free_set", "uplan_plus_set", "uplan_premium_set", "uplan_vip_set",
  ].forEach((id) => {
    const b = $(id);
    if (!b) return;
    const isOn = b.dataset.plan === String(App.user.plan || "free");
    b.classList.toggle("on", isOn);
    b.classList.toggle("active", isOn);
  });

  [
    "pplan_free", "pplan_pro", "pplan_premium", "pplan_enterprise",
    "pplan_free_set", "pplan_pro_set", "pplan_premium_set", "pplan_enterprise_set",
  ].forEach((id) => {
    const b = $(id);
    if (!b) return;
    const isOn = b.dataset.plan === String(App.partner.plan || "free");
    b.classList.toggle("on", isOn);
    b.classList.toggle("active", isOn);
  });

  refreshUserPlanCardsUi();

  document.querySelectorAll('#S11_PLANS #plansPartnerOnly .card[data-plan]').forEach((card) => {
    const currentPlan = String(App.partner.plan || "free").toLowerCase();
    const isCurrent = String(card.dataset.plan || "").toLowerCase() === currentPlan;
    const isOnboarding = App.planScreenMode === "onboarding";
    card.classList.toggle("is-current", !isOnboarding && isCurrent);
    const btn = card.querySelector(".btn");
    if (btn && !isOnboarding) {
      const cardPlan = String(card.dataset.plan || "").toLowerCase();
      btn.textContent = cardPlan === "enterprise" ? t("plans.contact_us", "Napisz do nas") : (isCurrent ? t("plans.current", "Aktualny plan") : t("plans.choose", "Wybierz"));
    }
  });

  if (App.planScreenMode === "onboarding" && App.currentView === "S11_PLANS") {
    applyPlanScreenMode();
  }

  if (App.currentView === "S10B_PROFILE_EDIT") {
    if ($("setNearbyRadiusKm")) $("setNearbyRadiusKm").value = String(App.user.nearbyRadiusKm || 25);
  }

  if (App.currentView === "S3_PROFILE_SETUP") {
    if ($("setupNick")) $("setupNick").value = App.user.nick || "";
    const setupCity = $("setupCity");
    if (setupCity && App.user.city && setupCity.value !== "Pobieranie lokalizacji...") {
      setupCity.value = App.user.city;
    }
    if ($("setupBio")) $("setupBio").value = App.user.bio || "";
    if ($("setupNearbyRadiusKm")) $("setupNearbyRadiusKm").value = String(App.user.nearbyRadiusKm || 25);
    if ($("setPrefAgeFrom")) $("setPrefAgeFrom").value = String(App.user.prefAgeFrom);
    if ($("setPrefAgeTo")) $("setPrefAgeTo").value = String(App.user.prefAgeTo);
    safeSetText("setupAgeDisplay", t("settings.ageLabel", { age: App.user.age || "—" }));
    safeSetText("bioCount", String(($("setupBio")?.value || "").length));
  }

  // Partner plan line in dashboard
  const partnerHubName = $("partnerHubName");
  if (partnerHubName) {
    partnerHubName.textContent = App.partner.company || "Twoje miejsce";
  }

  const partnerHubMeta = $("partnerHubMeta");
  if (partnerHubMeta) {
    const categoryLabel = App.partner.category ? t(`partnerCategory.${App.partner.category}`, App.partner.category) : "";
    const meta = [categoryLabel, App.partner.city].filter(Boolean).join(" • ");
    partnerHubMeta.textContent = meta || t("partnerDash.meta");
  }

  const partnerHubLogoPreview = $("partnerHubLogoPreview");
  if (partnerHubLogoPreview) {
    if (App.partner.logoUrl) {
      const src = String(App.partner.logoUrl).startsWith("http")
        ? App.partner.logoUrl
        : `${API_BASE_URL}${App.partner.logoUrl}`;
      partnerHubLogoPreview.innerHTML = `<img src="${src}" alt="Logo organizatora" style="width:100%;height:100%;object-fit:cover;border-radius:inherit;" />`;
    } else {
      partnerHubLogoPreview.innerHTML = "";
      partnerHubLogoPreview.textContent = (App.partner.company || "U").trim().charAt(0).toUpperCase();
    }
  }

  const planLine = $("partnerPlanLine");
  if (planLine) {
    planLine.textContent = `Plan ${String(App.partner.plan || "free").toUpperCase()} jest teraz aktywny.`;
  }

  // Partner analytics in profile hub
  const partnerStatsGrid = $("partnerStatsGrid");
  if (partnerStatsGrid) {
    const metricCards = partnerStatsGrid.querySelectorAll(".metricCard");
    const partnerPlanOrder = ["free", "pro", "premium", "enterprise"];
    const currentPartnerPlan = String(App.partner?.plan || "free").toLowerCase();
    const currentPartnerPlanIndex = Math.max(0, partnerPlanOrder.indexOf(currentPartnerPlan));

    metricCards.forEach((card) => {
      const minPlan = String(card.dataset.minPlan || "free").toLowerCase();
      const minPlanIndex = Math.max(0, partnerPlanOrder.indexOf(minPlan));
      card.style.display = currentPartnerPlanIndex >= minPlanIndex ? "" : "none";
    });

    if (metricCards[0]) {
      const label = metricCards[0].querySelector(".metricLabel");
      const sub = metricCards[0].querySelector(".metricSub");
      if (label) label.textContent = t("partnerDash.metricActive");
      if (sub) sub.textContent = t("partnerDash.metricActiveSub");
    }

    if (metricCards[1]) {
      const label = metricCards[1].querySelector(".metricLabel");
      const sub = metricCards[1].querySelector(".metricSub");
      if (label) label.textContent = t("partnerDash.metricDrafts");
      if (sub) sub.textContent = t("partnerDash.metricDraftsSub");
    }

    if (metricCards[2]) {
      const label = metricCards[2].querySelector(".metricLabel");
      const sub = metricCards[2].querySelector(".metricSub");
      if (label) label.textContent = t("partnerDash.metricSignupsTotal");
      if (sub) sub.textContent = "Do aktywnych";
    }

    if (metricCards[3]) {
      const label = metricCards[3].querySelector(".metricLabel");
      const sub = metricCards[3].querySelector(".metricSub");
      if (label) label.textContent = "Frekwencja";
      if (sub) sub.textContent = "W aktywnych";
    }

    safeSetText("m_events_val", "—");
    safeSetText("m_views_val", "—");
    safeSetText("m_clicks_val", "—");
    safeSetText("m_conv_val", "—");

    const canLoadPartnerStats =
      App.isLoggedIn === true &&
      App.role === "partner" &&
      App.currentView === "S9_PARTNER" &&
      !!localStorage.getItem("usly_token");

    if (canLoadPartnerStats) {
      apiFetch("/partners/dashboard/stats")
        .then((res) => {
          if (!res?.success || !res?.data) return;

          safeSetText("m_events_val", String(res.data.total_events ?? 0));
          safeSetText("m_views_val", String(res.data.draft_events ?? 0));
          safeSetText("m_clicks_val", String(res.data.total_signups ?? 0));
          const signups = Number(res.data.total_signups ?? 0);
          const capacity = Number(res.data.total_capacity ?? 0);
          const freq = capacity > 0 ? Math.round((signups / capacity) * 100) : 0;
          safeSetText("m_conv_val", capacity > 0 ? `${freq}%` : "—");
        })
        .catch(() => {
          safeSetText("m_events_val", "—");
          safeSetText("m_views_val", "—");
          safeSetText("m_clicks_val", "—");
          safeSetText("m_conv_val", "—");
        });
    }
  }

  // Setup avatar
  const renderAvatarBox = (el) => {
    if (!el) return;
    if (App.user.avatarUrl) {
      const src = String(App.user.avatarUrl).startsWith("http")
        ? App.user.avatarUrl
        : `${API_BASE_URL}${App.user.avatarUrl}`;
      el.innerHTML = `<img src="${src}" alt="${t("chat.defaultUser")}" style="width:100%;height:100%;object-fit:cover;border-radius:inherit;" />`;
    } else {
      const name = App.user.nick || "U";
      el.innerHTML = `<div class="userAvatarFallback" style="${premiumAvatarStyle(getAvatarGradient(name))}">${avatarInitial(name)}</div>`;
    }
  };

  renderAvatarBox($("userAvatar"));
  renderAvatarBox($("settingsUserAvatarPreview"));

  // Fill settings inputs moved out of renderAll to avoid overwriting unsaved form edits

  // Settings range values
  if ($("setPrefAgeFrom")) $("setPrefAgeFrom").value = String(App.user.prefAgeFrom ?? 18);
  if ($("setPrefAgeTo")) $("setPrefAgeTo").value = String(App.user.prefAgeTo ?? 99);
  if ($("setAgeAny")) $("setAgeAny").checked = App.user.prefAgeFrom == null && App.user.prefAgeTo == null;
  safeSetText("setPrefAgeFromVal", String(App.user.prefAgeFrom ?? 18));
  safeSetText("setPrefAgeToVal", String(App.user.prefAgeTo ?? 99));
  $("setAgeAny")?.dispatchEvent(new Event("change"));

  // Partner settings
  if ($("setOrgCompany")) $("setOrgCompany").value = App.partner.company || "";
  if ($("setOrgCategory")) $("setOrgCategory").value = App.partner.category || "inne";
  if ($("setOrgCity")) $("setOrgCity").value = App.partner.city || "Warszawa";
  if ($("setOrgAbout")) $("setOrgAbout").value = App.partner.about || "";

  ["setOrgLogoPreview", "setupOrgLogoPreview"].forEach((previewId) => {
    const orgLogoPreview = $(previewId);
    if (!orgLogoPreview) return;

    if (App.partner.logoUrl) {
      const src = String(App.partner.logoUrl).startsWith("http")
        ? App.partner.logoUrl
        : `${API_BASE_URL}${App.partner.logoUrl}`;
      orgLogoPreview.innerHTML = `<img src="${src}" alt="Logo organizatora" style="width:100%;height:100%;object-fit:cover;border-radius:inherit;" />`;
    } else {
      orgLogoPreview.textContent = (App.partner.company || "U").trim().charAt(0).toUpperCase();
    }
  });

  // Interest chips in visible sections
  renderInterestChips("interestChips");
  refreshInterestUi();
  renderInterestChips("setInterestChips");
  renderInterestChips("regInterestChips");

  // Lists
  if (App.currentView === "S4_NEARBY") renderNearby();
  if (App.currentView === "S7_EVENTS") renderEventsList();
  if (App.currentView === "S8_GROUPS") renderGroups();
  if (App.currentView === "S6_CHATS_LIST") renderChatList();
  if (App.currentView === "S6B_CHAT_THREAD") renderChatThread();
  if (App.currentView === "S9_PARTNER_EVENTS") renderPartnerEvents();
  if (App.currentView === "S9_PARTNER_MESSAGES") renderPartnerMsgList();
  if (App.role === "user" && !["S2_REGISTER","S3_PROFILE_SETUP"].includes(App.currentView)) refreshNotifBadgeCount();
  if (App.role === "user" && !["S2_REGISTER","S3_PROFILE_SETUP"].includes(App.currentView)) refreshGroupBadgeCount();
  if (App.role === "partner") refreshPartnerNotifBadgeCount();
  if (App.role === "partner") refreshPartnerMsgBadgeCount();
  if (App.currentView === "S12_NOTIFICATIONS") renderNotifications();

  // Keep dynamic partner event form labels after i18n re-render
  if (App.currentView === "S9_PARTNER_CREATE") {
    syncPartnerEventSubmitBtn();
  }

  // tabbar active
  updateTabbars();
}

/* ------------------------- Search bindings -------------------------- */
function initSearchBindings() {
  $("nearbyPeopleSearch")?.addEventListener("input", renderNearby);
  $("eventsSearch")?.addEventListener("input", renderEventsList);
  $("groupSearch")?.addEventListener("input", renderGroups);
  $("chatSearch")?.addEventListener("input", renderChatList);

  // === polling wiadomości ===
  let inboxPollStarted = false;
  function startInboxPolling() {
    if (inboxPollStarted) return;
    inboxPollStarted = true;

    setInterval(async () => {
      if (!App.isLoggedIn) return;

      try {
        if (App.role === "partner") {
          await refreshPartnerNotifBadgeCount();
          await refreshPartnerMsgBadgeCount();

          if (App.currentView === "S12_NOTIFICATIONS") {
            await renderNotifications();
          }

          return;
        }

        await refreshNotifBadgeCount();

        if (App.currentView === "S10E_PROFILE_INVITES") {
          await refreshProfileRelations();
        }

        if (App.currentView === "S12_NOTIFICATIONS") {
          await renderNotifications();
        }

        if (App.currentView === "S6_CHATS_LIST") {
          await renderChatList();
        } else {
          await refreshChatBadgeCount();
        }
        if (App.currentView === "S6B_CHAT_THREAD" && App.selectedChatUserId) {
          await renderChatThread();
        }
      } catch (err) {
        console.error("inbox polling failed", err);
      }
    }, 10000);
  }

  startInboxPolling();
  $("partnerMsgSearch")?.addEventListener("input", renderPartnerMsgList);
}

/* ------------------------- App Init -------------------------- */
async function init() {
  // Start view
  go("S0_WELCOME");

  // init hooks
  initGeolocation();
  initAgeSliders();
  initCharCounters();
  initInterestInputs();
  initSearchBindings();
  initPartnerLogoUpload();
  initPartnerPricingFields();
  syncPartnerEventSubmitBtn();

  // Default role toggle UI
  selectRole(App.role);

  // Default plan selections are synced passively in renderAll()/session restore.

  const regBirthDate = $("regBirthDate");
  const ageError = $("ageError");
  if (regBirthDate && ageError && regBirthDate.dataset.bound !== "1") {
    regBirthDate.addEventListener("input", () => {
      ageError.style.display = "none";
      ageError.textContent = t("register.toast.age_under_18");
    });
    regBirthDate.dataset.bound = "1";
  }

  // Default events tab
  setEventsTab(App.eventsTab);
  refreshUserPlanCardsUi();

  // Default: logged out
  $("appRoot")?.classList.toggle("isLoggedIn", App.isLoggedIn);
  updateTabbars();

  const token = localStorage.getItem("usly_token");

  if (token) {
    try {
      const me = await apiFetch("/auth/me");
      App.currentUserId = me?.id ?? me?.data?.id ?? null;
      App.currentRevenueCatAppUserId =
        me?.data?.revenuecat_app_user_id ?? me?.revenuecat_app_user_id ?? null;
      App.role = (me?.data?.role || me?.role) === "partner" ? "partner" : "user";
      selectRole(App.role);
      syncAccountEmail(me?.data?.email || me?.email || "");
      App.isLoggedIn = true;
      $("appRoot")?.classList.add("isLoggedIn");
      updateTabbars();

      if (App.role === "user") {
        const profile = await apiFetch("/users/me");
        if (profile?.success && profile?.data) {
          App.user.nick = profile.data.nick || App.user.nick;
          App.user.city = profile.data.miasto || App.user.city;
          App.user.bio = profile.data.bio || "";
          App.user.interests = Array.isArray(profile.data.zainteresowania) ? profile.data.zainteresowania : [];
          App.user.prefAgeFrom = Object.prototype.hasOwnProperty.call(profile.data, "age_min") ? profile.data.age_min : App.user.prefAgeFrom;
          App.user.prefAgeTo = Object.prototype.hasOwnProperty.call(profile.data, "age_max") ? profile.data.age_max : App.user.prefAgeTo;
        App.user.nearbyRadiusKm = Object.prototype.hasOwnProperty.call(profile.data, "nearby_radius_km") ? profile.data.nearby_radius_km : App.user.nearbyRadiusKm;
          App.user.plan = profile.data.plan || App.user.plan;
          App.user.avatarUrl = profile.data.avatar_url || App.user.avatarUrl || "";
          try { localStorage.setItem(USLY_STORAGE_KEYS.userPlan, App.user.plan); } catch (_) {}
          refreshUserPlanCardsUi();
          }
        renderAll();
        bindMessageInputs();
        go("S4_NEARBY");

        Promise.allSettled([loadNearbyPeople(), loadEvents(), loadMyGroups(), loadGroups(), refreshChatBadgeCount()])
          .then(() => renderAll())
          .catch((err) => console.error("session restore background refresh failed", err));

        return;
      } else {
        await loadPartnerProfile();
        try { localStorage.setItem(USLY_STORAGE_KEYS.partnerPlan, App.partner.plan || "free"); } catch (_) {}
        await loadPartnerEvents();
        renderAll();
        bindMessageInputs();
        go("S9_PARTNER");
        return;
      }
    } catch (err) {
      console.error("init session restore failed", err);
      try { localStorage.removeItem("usly_token"); } catch (_) {}
      try { localStorage.removeItem(USLY_STORAGE_KEYS.userPlan); } catch (_) {}
      try { localStorage.removeItem(USLY_STORAGE_KEYS.partnerPlan); } catch (_) {}
      try { localStorage.removeItem("usly_user_interests"); } catch (_) {}
      App.isLoggedIn = false;
      App.currentUserId = null;
      App.currentRevenueCatAppUserId = null;
      App.user.interests = [];
      App.user.trainerInterests = [];
      $("appRoot")?.classList.remove("isLoggedIn");
      updateTabbars();
      go("S0_WELCOME");
    }
  }

  if (App.isLoggedIn) {
    Promise.all([loadNearbyPeople(), loadEvents(), loadMyGroups(), loadGroups(), renderChatList()]).finally(() => {
      renderAll();
      bindMessageInputs();
    });
  } else {
    renderAll();
    bindMessageInputs();
  }
}


// Run when DOM ready
document.addEventListener("DOMContentLoaded", init);


/* ------------------------- Leaflet Map -------------------------- */

let nearbyMap = null;
let nearbyMarkers = [];

function initNearbyMap() {
  const el = document.getElementById("nearbyMap");
  if (!el || nearbyMap) return;

  const lat = App.user?.geo?.lat ? Number(App.user.geo.lat) : 52.2297;
  const lng = App.user?.geo?.lng ? Number(App.user.geo.lng) : 21.0122;

  nearbyMap = L.map("nearbyMap").setView([lat, lng], 12);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "© OpenStreetMap"
  }).addTo(nearbyMap);
}

function renderNearbyMapMarkers() {
  if (!nearbyMap) return;

  nearbyMarkers.forEach(m => nearbyMap.removeLayer(m));
  nearbyMarkers = [];

  const baseLat = App.user?.geo?.lat ? Number(App.user.geo.lat) : 52.2297;
  const baseLng = App.user?.geo?.lng ? Number(App.user.geo.lng) : 21.0122;

  const buildEventIcon = (ev) => L.divIcon({
    className: "nearby-event-marker",
    html: `<div style="position:relative;width:48px;height:56px;display:flex;align-items:flex-start;justify-content:center;">
      <div style="width:40px;height:40px;border-radius:16px;display:flex;align-items:center;justify-content:center;font-size:24px;background:radial-gradient(circle at 28% 22%, rgba(255,255,255,.32), transparent 30%),linear-gradient(135deg,rgba(244,63,211,.85),rgba(66,213,255,.72));border:3px solid rgba(255,196,87,.96);box-shadow:0 12px 28px rgba(0,0,0,.34),0 0 0 4px rgba(255,196,87,.18);text-shadow:0 8px 18px rgba(0,0,0,.25);">${getEventTagIcon(ev?.interest || "")}</div>
      <div style="position:absolute;left:19px;top:36px;width:10px;height:10px;background:#fff;transform:rotate(45deg);box-shadow:4px 4px 10px rgba(0,0,0,.18);"></div>
    </div>`,
    iconSize: [48, 56],
    iconAnchor: [24, 48],
  });

  const seenCoords = {};

  getNearbyPeopleForView().forEach((person, index) => {
    const lat = Number(person.location_lat);
    const lng = Number(person.location_lng);
    if (!Number.isFinite(lat) || !Number.isFinite(lng)) return;

    const coordKey = `${lat.toFixed(5)},${lng.toFixed(5)}`;
    const sameCoordIndex = seenCoords[coordKey] || 0;
    seenCoords[coordKey] = sameCoordIndex + 1;
    const markerLat = lat + sameCoordIndex * 0.00012;
    const markerLng = lng + sameCoordIndex * 0.00012;

    const personInitial = avatarInitial(person.nick || "U");
    const personBg = getAvatarGradient(person.nick || "U");
    const personAvatarSrc = person.avatarUrl
      ? (String(person.avatarUrl).startsWith("http") ? person.avatarUrl : `${API_BASE_URL}${person.avatarUrl}`)
      : "";

    const hasTrainerBadge = Array.isArray(person.trainerInterests) && person.trainerInterests.length > 0;

    const dynamicIcon = L.divIcon({
      className: "nearby-person-marker",
      html: `<div style="position:relative;width:48px;height:56px;display:flex;align-items:flex-start;justify-content:center;">
        <div style="width:40px;height:40px;border-radius:999px;overflow:hidden;display:flex;align-items:center;justify-content:center;font-size:18px;color:#fff;font-weight:900;background:${personBg};border:3px solid rgba(110,231,255,.96);box-shadow:0 12px 28px rgba(0,0,0,.34),0 0 0 4px rgba(110,231,255,.16);">${personAvatarSrc ? `<img src="${personAvatarSrc}" alt="${escapeHtml(person.nick || t("chat.defaultUser"))}" style="width:100%;height:100%;object-fit:cover;" />` : personInitial}</div>
        ${hasTrainerBadge ? `<div style="position:absolute;right:0;top:-7px;width:23px;height:23px;border-radius:999px;background:linear-gradient(135deg,#fff4b8,#ffbf3f);border:2px solid rgba(255,255,255,.95);display:flex;align-items:center;justify-content:center;font-size:12px;line-height:1;box-shadow:0 8px 18px rgba(0,0,0,.34),0 0 0 4px rgba(255,215,102,.18);z-index:4;">🎓</div>` : ""}</div>
        <div style="position:absolute;left:19px;top:36px;width:10px;height:10px;background:#fff;transform:rotate(45deg);box-shadow:4px 4px 10px rgba(0,0,0,.18);"></div>
      </div>`,
      iconSize: [48, 56],
      iconAnchor: [24, 48],
    });

    const marker = L.marker([markerLat, markerLng], { icon: dynamicIcon })
      .addTo(nearbyMap);

    marker.on("click", () => openMapMarker("person", index));
    nearbyMarkers.push(marker);
  });

  const nearbyEventsForMap = (App.nearbyEvents || [])
    .filter(ev => matchesUserEventInterest(ev) && isEventInNearbyRadius(ev));

  nearbyEventsForMap.forEach((ev, index) => {
    const lat = Number(ev.location_lat);
    const lng = Number(ev.location_lng);
    if (!Number.isFinite(lat) || !Number.isFinite(lng)) return;

    const coordKey = `${lat.toFixed(5)},${lng.toFixed(5)}`;
    const sameCoordIndex = seenCoords[coordKey] || 0;
    seenCoords[coordKey] = sameCoordIndex + 1;
    const markerLat = lat + sameCoordIndex * 0.00012;
    const markerLng = lng + sameCoordIndex * 0.00012;

    const marker = L.marker([markerLat, markerLng], { icon: buildEventIcon(ev) })
      .addTo(nearbyMap);

    marker.on("click", () => openEvent(ev.id));
    nearbyMarkers.push(marker);
  });

}



function openProfileEdit(){
  go("S10B_PROFILE_EDIT");
}


function refreshInterestUi() {
  const count = Array.isArray(App.user.interests) ? App.user.interests.length : 0;
  const limit = getUserInterestLimit();

  const ensureHint = (preferredId, anchorId) => {
    let el = $(preferredId);
    if (el) return el;

    const anchor = $(anchorId);
    if (!anchor || !anchor.parentNode) return null;

    el = document.createElement("div");
    el.id = preferredId;
    el.className = "sectionSub";
    el.style.marginTop = "8px";
    anchor.parentNode.insertBefore(el, anchor.nextSibling);
    return el;
  };

  const hintTargets = [
    ensureHint("regInterestLimitHint", "regInterestChips"),
    $("interestLimitHint"),
    $("setupInterestLimitHint"),
    $("setInterestLimitHint")
  ].filter(Boolean);

  const hintText = limit === null
    ? `${count} • VIP`
    : `${count}/${limit}`;

  hintTargets.forEach((hint) => {
    hint.textContent = hintText;
  });

  const inputs = [
    $("regInterestInput"),
    $("interestInput"),
    $("setInterestInput")
  ].filter(Boolean);

  const canAdd = canAddMoreInterests(count);

  inputs.forEach((input) => {
    input.disabled = !canAdd;
    input.style.opacity = canAdd ? "1" : "0.6";

    if (!canAdd) {
      input.placeholder = t("profileInterests.limitPlaceholder");
      input.onclick = () => toast(t("profileInterests.limitToast"));
    } else {
      const placeholderKey = input.getAttribute("data-i18n-placeholder");
      if (placeholderKey) input.placeholder = t(placeholderKey);
      input.onclick = null;
    }
  });
}

function openProfileInterests(){
  go("S10C_PROFILE_INTERESTS");
}

function openChangePassword() {
  openModal(t("password.modalTitle"), `
    <div class="tStrong">${t("password.heading")}</div>
    <div class="sectionSub mt10">${t("password.subtitle")}</div>
    <label class="mt12">${t("password.current")}</label>
    <input id="changePasswordCurrent" type="password" placeholder="${t("password.currentPlaceholder")}" />
    <label class="mt12">${t("password.new")}</label>
    <input id="changePasswordNew" type="password" placeholder="${t("password.newPlaceholder")}" />
    <label class="mt12">${t("password.repeat")}</label>
    <input id="changePasswordRepeat" type="password" placeholder="${t("password.repeatPlaceholder")}" />
    <button class="btn mt16" type="button" onclick="submitChangePassword()">${t("password.save")}</button>
  `);
}

async function submitChangePassword() {
  const currentPassword = $("changePasswordCurrent")?.value?.trim() || "";
  const newPassword = $("changePasswordNew")?.value?.trim() || "";
  const repeatPassword = $("changePasswordRepeat")?.value?.trim() || "";

  if (!currentPassword || !newPassword || !repeatPassword) {
    toast(t("reset.toast.fill_passwords"));
    return;
  }

  if (newPassword !== repeatPassword) {
    toast(t("password.toastMismatch"));
    return;
  }

  if (newPassword.length < 8) {
    toast(t("password.toastMin"));
    return;
  }

  try {
    const res = await apiFetch("/auth/change-password", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        current_password: currentPassword,
        new_password: newPassword,
      }),
    });

    if (res?.success) {
      toast(t("reset.toast.success"));
      closeModal();
      return;
    }

    toast(res?.error?.message || t("reset.toast.change_error"));
  } catch (err) {
    const msg =
      err?.data?.detail === "CURRENT_PASSWORD_INVALID"
        ? t("password.toastCurrentInvalid")
        : err?.data?.detail === "NEW_PASSWORD_SAME_AS_CURRENT"
        ? t("password.toastSame")
        : err?.userMessage || t("reset.toast.change_error");
    toast(msg);
  }
}

function openDeleteAccount() {
  openModal(t("delete.modalTitle"), `
    <div class="tStrong">${t("delete.heading")}</div>
    <div class="sectionSub mt10">${t("delete.subtitle")}</div>
    <label class="mt12">${t("delete.password")}</label>
    <input id="deleteAccountPassword" type="password" placeholder="${t("delete.placeholder")}" />
    <button class="btn danger mt16" type="button" onclick="submitDeleteAccount()">${t("delete.confirm")}</button>
  `);
}

async function submitDeleteAccount() {
  const password = $("deleteAccountPassword")?.value?.trim() || "";

  if (!password) {
    toast(t("delete.toastFill"));
    return;
  }

  try {
    const res = await apiFetch("/auth/delete-account", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password }),
    });

    if (res?.success) {
      try { localStorage.removeItem("usly_token"); } catch (_) {}
      App.isLoggedIn = false;
      App.currentUserId = null;
      App.currentRevenueCatAppUserId = null;
      closeModal();
      toast(t("delete.toastSuccess"));
      go("S0_WELCOME");
      renderAll();
      return;
    }

    toast(res?.error?.message || t("delete.toastFailed"));
  } catch (err) {
    const msg =
      err?.data?.detail === "PASSWORD_INVALID"
        ? t("delete.toastInvalid")
        : err?.userMessage || t("delete.toastFailed");
    toast(msg);
  }
}


/* ------------------------- LIVE BUG REPORT OVERRIDE -------------------------- */
async function submitBugReport() {
  const ta = $("bugReportText");
  const message = (ta?.value || "").trim();
  if (!message) {
    toast(t("bugReport.toast.empty"));
    return;
  }

  const role = App.role === "partner" ? "Organizator" : "Towarzysz";
  const userId = App.currentUserId ?? null;
  const email =
    (App.role === "partner" ? App.partner?.email : App.user?.email) ||
    null;

  try {
    const res = await apiFetch("/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message,
        role,
        user_id: userId,
        email,
        current_view: App.currentView || null,
      }),
    });

    if (!res?.success || !res?.data?.ticket) {
      toast(res?.error?.message || t("bugReport.toast.failed"));
      return;
    }

    closeModal();
    if (res.data.emailed) {
      toast(t("bugReport.ticketSent", { ticket: res.data.ticket }));
    } else {
      toast(t("bugReport.ticketSaved", { ticket: res.data.ticket }));
    }
  } catch (err) {
    toast(err?.userMessage || t("bugReport.toast.failed"));
  }
}

async function submitResetPassword() {
  const newPassword = $("resetPasswordNew")?.value?.trim() || "";
  const repeatPassword = $("resetPasswordRepeat")?.value?.trim() || "";

  if (!newPassword || !repeatPassword) {
    toast(t("reset.toast.fill_passwords"));
    return;
  }

  if (newPassword !== repeatPassword) {
    toast(t("reset.toast.passwords_mismatch"));
    return;
  }

  if (newPassword.length < 8) {
    toast(t("reset.toast.password_too_short"));
    return;
  }

  if (!App.resetToken) {
    toast(t("reset.toast.missing_token"));
    return;
  }

  try {
    const res = await apiFetch("/auth/reset-password", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        token: App.resetToken,
        new_password: newPassword,
      }),
    });

    if (res?.success) {
      toast(t("reset.toast.success"));
      go("S1_LOGIN");
      return;
    }

    toast(res?.error?.message || t("reset.toast.change_error"));
  } catch (err) {
    toast(err?.userMessage || t("reset.toast.generic_error"));
  }
}

async function loadResetPasswordScreen(token) {
  const tokenValue = String(token || "").trim();

  if (!tokenValue) {
    toast(t("reset.toast.missing_link"));
    return false;
  }

  try {
    const res = await apiFetch("/auth/reset-password-info", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token: tokenValue }),
    });

    if (!res?.success || !res?.data?.email) {
      toast(t("reset.toast.invalid_link"));
      return false;
    }

    App.resetToken = tokenValue;
    App.resetEmail = String(res.data.email || "");

    closeModal();
    go("S3_RESET_PASSWORD");

    if ($("resetPasswordEmail")) $("resetPasswordEmail").value = App.resetEmail;
    if ($("resetPasswordNew")) $("resetPasswordNew").value = "";
    if ($("resetPasswordRepeat")) $("resetPasswordRepeat").value = "";

    return true;
  } catch (err) {
    toast(err?.userMessage || t("reset.toast.generic_error"));
    return false;
  }
}

async function verifyEmailFromToken(token) {
  const tokenValue = String(token || "").trim();

  if (!tokenValue) {
    toast("Brak tokenu weryfikacyjnego.");
    return false;
  }

  try {
    const res = await apiFetch(`/auth/verify-email?token=${encodeURIComponent(tokenValue)}`);
    if (res?.success) {
      toast("Email został potwierdzony. Możesz się zalogować.");
      go("S1_LOGIN");
      return true;
    }

    toast("Nie udało się potwierdzić emaila.");
    return false;
  } catch (err) {
    toast(err?.userMessage || "Nie udało się potwierdzić emaila.");
    return false;
  }
}

function handleAuthLinkUrl(rawUrl) {
  try {
    const current = window.location.href || "https://uslyapp.pl/";
    const url = new URL(String(rawUrl || current), current);
    const path = String(url.pathname || "").toLowerCase();
    const hash = String(url.hash || "").toLowerCase();
    const params = url.searchParams;
    const token = (params.get("reset_token") || params.get("token") || "").trim();

    if (!token) return false;

    const isResetLink = path.includes("reset-password") || hash.includes("reset-password") || params.has("reset_token");
    const isVerifyLink = path.includes("verify-email") || hash.includes("verify-email");

    if (isResetLink) {
      loadResetPasswordScreen(token).catch(() => {});
      return true;
    }

    if (isVerifyLink) {
      verifyEmailFromToken(token).catch(() => {});
      return true;
    }

    return false;
  } catch (_) {
    return false;
  }
}

function handleAuthLinkFromUrl() {
  setTimeout(() => {
    handleAuthLinkUrl(window.location.href);
  }, 0);
}

function setupCapacitorAuthLinkListener() {
  try {
    const CapacitorApp = window.Capacitor?.Plugins?.App;
    if (!CapacitorApp?.addListener) return;

    CapacitorApp.addListener("appUrlOpen", (event) => {
      if (event?.url) handleAuthLinkUrl(event.url);
    });

    if (CapacitorApp.getLaunchUrl) {
      CapacitorApp.getLaunchUrl()
        .then((event) => {
          if (event?.url) handleAuthLinkUrl(event.url);
        })
        .catch(() => {});
    }
  } catch (_) {}
}


let pushNotificationsSetupStarted = false;

async function setupPushNotifications() {
  if (pushNotificationsSetupStarted) return;
  if (!localStorage.getItem("usly_token")) return;
  pushNotificationsSetupStarted = true;

  try {
    const PushNotifications = window.Capacitor?.Plugins?.PushNotifications;
    if (!PushNotifications) return;

    const platform = window.Capacitor?.getPlatform?.();
    if (platform !== "android" && platform !== "ios") return;

    let permission = await PushNotifications.checkPermissions();
    if (permission.receive !== "granted") {
      permission = await PushNotifications.requestPermissions();
    }
    if (permission.receive !== "granted") return;

    await PushNotifications.register();

    PushNotifications.addListener("registration", async (token) => {
      const tokenValue = token?.value || token;
      console.info("USLY push token:", tokenValue);

      if (!tokenValue || typeof window.apiFetch !== "function") return;

      try {
        await window.apiFetch("/push/register-token", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            token: tokenValue,
            platform,
          }),
        });
        console.info("USLY push token registered");
      } catch (error) {
        console.error("USLY push token register failed", error);
      }
    });

    PushNotifications.addListener("registrationError", (error) => {
      console.error("USLY push registration error", error);
    });

    PushNotifications.addListener("pushNotificationReceived", (notification) => {
      console.info("USLY push received:", notification);
    });

    PushNotifications.addListener("pushNotificationActionPerformed", (action) => {
      console.info("USLY push action:", action);
    });
  } catch (error) {
    console.error("USLY push setup failed", error);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  handleAuthLinkFromUrl();
  setupCapacitorAuthLinkListener();
});

function passwordEyeIconHtml(isVisible) {
  return isVisible
    ? `<span aria-hidden="true" class="passwordEyeIcon"><svg viewBox="0 0 24 24"><path d="M3.6 3.6l16.8 16.8"></path><path d="M10.4 6.3A9.8 9.8 0 0 1 12 6.2c5.8 0 9.2 5.8 9.2 5.8a15.8 15.8 0 0 1-3.1 3.6"></path><path d="M14.1 14.1A2.9 2.9 0 0 1 9.9 9.9"></path><path d="M6.4 6.9A15.8 15.8 0 0 0 2.8 12s3.4 5.8 9.2 5.8c1.2 0 2.3-.25 3.3-.66"></path></svg></span>`
    : `<span aria-hidden="true" class="passwordEyeIcon"><svg viewBox="0 0 24 24"><path d="M2.8 12s3.4-5.8 9.2-5.8 9.2 5.8 9.2 5.8-3.4 5.8-9.2 5.8S2.8 12 2.8 12Z"></path><circle cx="12" cy="12" r="2.7"></circle></svg></span>`;
}

function togglePasswordVisibility(inputId, btn) {
  const input = $(inputId);
  if (!input) return;

  const show = input.type === "password";
  input.type = show ? "text" : "password";

  if (btn) {
    btn.classList.toggle("is-visible", show);
    btn.innerHTML = passwordEyeIconHtml(show);
    btn.setAttribute("aria-label", show ? (btn.dataset.hideLabel || "Ukryj hasło") : (btn.dataset.showLabel || "Pokaż hasło"));
  }
}



/* ------------------------- Admin reports recovery ------------------------- */

function escapeAdminHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}



document.addEventListener("click", (e) => {
  const chipRemove = e.target?.closest?.(".eventInterestChipRemove");
  if (chipRemove) {
    const index = Number(chipRemove.dataset.index);
    const tags = getPartnerEventInterestTags();
    if (Number.isInteger(index) && index >= 0 && index < tags.length) {
      setPartnerEventInterestTags(tags.filter((_, i) => i !== index));
      renderPartnerEventInterestTags();
    }
    return;
  }

  const removeBtn = e.target?.closest?.("#peInterestRemoveBtn");
  if (!removeBtn) return;

  resetSingleEventTag();
});

/* ------------------------- Global CTA bindings ------------------------- */
window.finishProfileSetup = finishProfileSetup;
window.finishPartnerSetup = finishPartnerSetup;
window.saveSettings = saveSettings;
window.toggleTrainerInterest = toggleTrainerInterest;
window.savePartnerSettings = savePartnerSettings;
window.restoreStorePurchases = restoreStorePurchases;
window.publishPartnerEvent = publishPartnerEvent;
window.savePartnerEventDraft = savePartnerEventDraft;
window.togglePasswordVisibility = togglePasswordVisibility;
