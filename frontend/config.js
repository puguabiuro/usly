/**
 * Publiczna konfiguracja aplikacji USLY.
 *
 * Ten plik jest dołączany do mobilnego buildu Capacitor i może zawierać
 * wyłącznie wartości publiczne, przeznaczone do działania w aplikacji klienta.
 *
 * Dozwolone:
 * - RevenueCat Public API Key dla Google Play, zaczynający się od "goog_",
 * - RevenueCat Public API Key dla App Store, zaczynający się od "appl_",
 * - inne jawne ustawienia aplikacji klienckiej.
 *
 * Zabronione:
 * - RevenueCat Secret API Key,
 * - RevenueCat API v2 secret key,
 * - sekret Authorization webhooka,
 * - hasła, tokeny serwerowe i prywatne dane uwierzytelniające.
 *
 * Plik musi zostać załadowany przed billing.js.
 */
window.USLY_CONFIG = Object.freeze({
  revenueCat: Object.freeze({
    androidPublicApiKey: "goog_jrfVwUwgRKZQdWQKobkbwFmasVP",
    iosPublicApiKey: "",
  }),
});
