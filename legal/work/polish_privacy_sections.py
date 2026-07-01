from pathlib import Path

def replace_between(text, start_marker, end_marker, replacement):
    start = text.index(start_marker)
    end = text.index(end_marker, start)
    return text[:start] + replacement.strip() + "\n" + text[end:]

pl = Path("frontend/polityka-prywatnosci.html")
en = Path("frontend/privacy-policy.html")

pl_text = pl.read_text(encoding="utf-8")
en_text = en.read_text(encoding="utf-8")

pl_section_1 = """
<h2 id="1-informacje-og-lne">1. INFORMACJE OGÓLNE</h2>
<p>Niniejsza Polityka Prywatności określa zasady przetwarzania danych osobowych użytkowników aplikacji mobilnej USLY (dalej: „Aplikacja”).</p>
<p>USLY zapewnia procedury ochrony danych osobowych Użytkowników zgodnie z Rozporządzeniem Parlamentu Europejskiego i Rady (UE) 2016/679 z dnia 27 kwietnia 2016 r. oraz zgodnie z wdrożoną Polityką Prywatności.</p>
<p>Administratorem danych osobowych jest PUGUA Sp. z o.o. z siedzibą w Byszewska 37R, 92-770 Łódź, wpisana do Rejestru Przedsiębiorców KRS 0001175035, NIP: 7282900556 (dalej: „Administrator”).</p>
<p>W celu uzyskania informacji lub pomocy w zakresie danych osobowych Użytkownik może kontaktować się z nami na adres: <strong>kontakt@uslyapp.pl</strong>.</p>

<div class="definitionBox">
  <h3>Definicje</h3>
  <p><strong>Administrator</strong> – podmiot będący właścicielem oraz operatorem Aplikacji, który decyduje o celach i sposobach przetwarzania danych osobowych Użytkowników.</p>
  <p><strong>Aplikacja</strong> – aplikacja mobilna USLY, umożliwiająca Użytkownikom nawiązywanie kontaktów, poznawanie nowych osób oraz uczestniczenie w interakcjach społecznościowych.</p>
  <p><strong>Dane osobowe</strong> – wszelkie informacje o zidentyfikowanej lub możliwej do zidentyfikowania osobie fizycznej.</p>
  <p><strong>Konto</strong> – indywidualny profil Użytkownika utworzony w Aplikacji.</p>
  <p><strong>Lokalizacja</strong> – dane geograficzne dotyczące położenia Urządzenia Użytkownika, pozyskiwane za zgodą Użytkownika.</p>
  <p><strong>Naruszenie danych osobowych</strong> – zdarzenie prowadzące do przypadkowego lub bezprawnego zniszczenia, utraty, zmiany lub ujawnienia danych osobowych.</p>
  <p><strong>Polityka Prywatności</strong> – niniejszy dokument.</p>
  <p><strong>Profil</strong> – zestaw informacji udostępnionych przez Użytkownika w ramach Konta.</p>
  <p><strong>Przetwarzanie</strong> – operacje wykonywane na danych osobowych, takie jak zbieranie, utrwalanie, przechowywanie, organizowanie, modyfikowanie, udostępnianie lub usuwanie.</p>
  <p><strong>Regulamin</strong> – dokument określający zasady korzystania z Aplikacji.</p>
  <p><strong>Urządzenie</strong> – urządzenie elektroniczne, w szczególności smartfon lub tablet.</p>
  <p><strong>Usługa</strong> – usługi świadczone drogą elektroniczną przez Administratora za pośrednictwem Aplikacji.</p>
  <p><strong>Użytkownik</strong> – osoba fizyczna korzystająca z Aplikacji.</p>
  <p><strong>Wydarzenia lub Interakcje</strong> – działania podejmowane przez Użytkownika w Aplikacji lub między Użytkownikami.</p>
</div>

<p>Administrator przetwarza dane osobowe zgodnie z:</p>
<p class="letter-item">a) Rozporządzeniem Parlamentu Europejskiego i Rady (UE) 2016/679 (RODO),</p>
<p class="letter-item">b) ustawą o ochronie danych osobowych,</p>
<p class="letter-item">c) ustawą o świadczeniu usług drogą elektroniczną.</p>
"""

pl_section_3 = """
<h2 id="3-cele-przetwarzania-danych">3. CELE PRZETWARZANIA DANYCH</h2>
<p>Administrator przetwarza dane osobowe na podstawie obowiązujących przepisów prawnych, w celu zapewnienia dostępu do usług w Aplikacji.</p>
<p>Rodzaje gromadzonych informacji zależą od sposobu, w jaki Użytkownik korzysta z usług w Aplikacji.</p>
<p>Dane osobowe przetwarzane są w celu wdrożenia tzw. uzasadnionego interesu, rozumianego jako całkowicie zgodny z prawem cel przetwarzania danych, spójny z prawami Użytkownika, w tym między innymi:</p>
<p class="number-item">1) świadczenia usług drogą elektroniczną (prowadzenie konta w Aplikacji),</p>
<p class="number-item">2) autoryzacja dostępu i weryfikacja danych Użytkownika (w tym wieku i tożsamości),</p>
<p class="number-item">3) umożliwienia komunikacji między Użytkownikami,</p>
<p class="number-item">4) umożliwienia uczestnictwa w elementach Interakcji i obsługi Wydarzeń,</p>
<p class="number-item">5) realizacji subskrypcji i płatności,</p>
<p class="number-item">6) dostarczania informacji marketingowych (w tym spersonalizowanych),</p>
<p class="number-item">7) poprawy jakości i modyfikacji Aplikacji,</p>
<p class="number-item">8) zawiadamiania o zmianach dotyczących Usług,</p>
<p class="number-item">9) zapewnienia bezpieczeństwa i zapobiegania nadużyciom,</p>
<p class="number-item">10) rozpatrywanie skarg i informacji o naruszeniach,</p>
<p class="number-item">10) realizacji obowiązków prawnych Administratora.</p>
"""

en_section_1 = """
<h2 id="1-general-information">1. GENERAL INFORMATION</h2>
<p>This Privacy Policy sets out the rules for the processing of personal data of users of the USLY mobile application (hereinafter: “the App”).</p>
<p>USLY ensures procedures for the protection of Users’ personal data in accordance with Regulation (EU) 2016/679 of the European Parliament and of the Council of 27 April 2016 and in accordance with the implemented Privacy Policy.</p>
<p>The data controller is PUGUA Sp. z o.o., with its registered office at Byszewska 37R, 92-770 Łódź, Tax Identification Number (NIP): 7282900556, National Business Registry Number (KRS): 0001175035 (hereinafter: “the Controller”).</p>
<p>To obtain information or assistance regarding personal data, the User may contact us at: <strong>kontakt@uslyapp.pl</strong>.</p>

<div class="definitionBox">
  <h3>Definitions</h3>
  <p><strong>Controller</strong> – the entity that owns and operates the Application and determines the purposes and means of processing Users’ personal data.</p>
  <p><strong>Application</strong> – the USLY mobile application, enabling Users to make contacts, meet new people and participate in social interactions.</p>
  <p><strong>Personal Data</strong> – any information relating to an identified or identifiable natural person.</p>
  <p><strong>Account</strong> – a User’s individual profile created within the App.</p>
  <p><strong>Location</strong> – geographical data regarding the location of the User’s Device, obtained with the User’s consent.</p>
  <p><strong>Personal data breach</strong> – any incident leading to the accidental or unlawful destruction, loss, alteration or disclosure of personal data.</p>
  <p><strong>Privacy Policy</strong> – this document.</p>
  <p><strong>Profile</strong> – a set of information provided by the User as part of their Account.</p>
  <p><strong>Processing</strong> – operations performed on personal data, such as collection, recording, storage, organisation, modification, disclosure or erasure.</p>
  <p><strong>Terms and Conditions</strong> – a document setting out the rules for using the Application.</p>
  <p><strong>Device</strong> – an electronic device, in particular a smartphone or tablet.</p>
  <p><strong>Service</strong> – services provided electronically by the Controller via the Application.</p>
  <p><strong>User</strong> – a natural person using the App.</p>
  <p><strong>Events or Interactions</strong> – actions undertaken by a User within the Application or between Users.</p>
</div>

<p>The Controller processes personal data in accordance with:</p>
<p class="letter-item">a) Regulation (EU) 2016/679 of the European Parliament and of the Council (GDPR),</p>
<p class="letter-item">b) the Personal Data Protection Act,</p>
<p class="letter-item">c) the Act on the Provision of Electronic Services.</p>
"""

en_section_3 = """
<h2 id="3-purposes-of-data-processing">3. PURPOSES OF DATA PROCESSING</h2>
<p>The Controller processes personal data in accordance with applicable legal provisions, in order to provide access to services within the Application.</p>
<p>The types of information collected depend on how the User utilises the services within the Application.</p>
<p>Personal data is processed for the purpose of pursuing a so-called legitimate interest, understood as a fully lawful purpose of data processing that is consistent with the User’s rights, including, amongst others:</p>
<p class="number-item">1) the provision of electronic services (maintaining an account in the App),</p>
<p class="number-item">2) authorising access and verifying the User’s data (including age and identity),</p>
<p class="number-item">3) enabling communication between Users,</p>
<p class="number-item">4) enabling participation in Interactions and the management of Events,</p>
<p class="number-item">5) processing subscriptions and payments,</p>
<p class="number-item">6) providing marketing information (including personalised content),</p>
<p class="number-item">7) improving the quality and modifying the Application,</p>
<p class="number-item">8) notifying Users of changes to the Services,</p>
<p class="number-item">9) ensuring security and preventing abuse,</p>
<p class="number-item">10) handling complaints and reports of breaches,</p>
<p class="number-item">10) fulfilling the Controller’s legal obligations.</p>
"""

pl_text = replace_between(pl_text, '<h2 id="1-informacje-og-lne">', '<h2 id="2-zakres-przetwarzanych-danych">', pl_section_1)
pl_text = replace_between(pl_text, '<h2 id="3-cele-przetwarzania-danych">', '<h2 id="4-podstawy-prawne-przetwarzania">', pl_section_3)

en_text = replace_between(en_text, '<h2 id="1-general-information">', '<h2 id="2-scope-of-data-processed">', en_section_1)
en_text = replace_between(en_text, '<h2 id="3-purposes-of-data-processing">', '<h2 id="4-legal-basis-for-processing">', en_section_3)

pl.write_text(pl_text, encoding="utf-8")
en.write_text(en_text, encoding="utf-8")
print("OK polished privacy sections 1 and 3")
