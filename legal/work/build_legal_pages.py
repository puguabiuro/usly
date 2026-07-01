from pathlib import Path
import html
import re

ROOT = Path(".")
WORK = ROOT / "legal/work"

PAGES = [
    {
        "src": WORK / "regulamin_pl.txt",
        "out": ROOT / "frontend/regulamin.html",
        "lang": "pl",
        "title": "Regulamin aplikacji mobilnej USLY",
        "label": "Regulamin",
        "version": "1.0",
        "effective": "16 czerwca 2026",
        "switch_label": "English version",
        "switch_href": "/regulamin/en",
    },
    {
        "src": WORK / "regulamin_en.txt",
        "out": ROOT / "frontend/regulamin.en.html",
        "lang": "en",
        "title": "Terms and Conditions of the USLY Mobile App",
        "label": "Terms and Conditions",
        "version": "1.0",
        "effective": "16 June 2026",
        "switch_label": "Wersja polska",
        "switch_href": "/regulamin",
    },
    {
        "src": WORK / "privacy_pl.txt",
        "out": ROOT / "frontend/polityka-prywatnosci.html",
        "lang": "pl",
        "title": "Polityka prywatności aplikacji USLY",
        "label": "Polityka prywatności",
        "version": "1.1",
        "effective": "16 czerwca 2026",
        "switch_label": "English version",
        "switch_href": "/privacy-policy",
    },
    {
        "src": WORK / "privacy_en.txt",
        "out": ROOT / "frontend/privacy-policy.html",
        "lang": "en",
        "title": "USLY App Privacy Policy",
        "label": "Privacy Policy",
        "version": "1.1",
        "effective": "16 June 2026",
        "switch_label": "Wersja polska",
        "switch_href": "/polityka-prywatnosci",
    },
]

def clean_lines(path: Path):
    raw = path.read_text(encoding="utf-8").splitlines()
    lines = []
    for line in raw:
        s = line.strip()
        if not s:
            continue
        if s.startswith("--- PAGE"):
            continue
        s = re.sub(r"\s+", " ", s)
        lines.append(s)
    return lines

def is_heading(s, privacy=False):
    if s.startswith("§ "):
        return True
    if privacy and re.match(r"^\d+\.\s+[^a-ząćęłńóśźż]+$", s):
        return True
    return False

def is_new_block(s, privacy=False):
    if is_heading(s, privacy=privacy):
        return True
    if re.match(r"^\d+\.\s+", s):
        return True
    if re.match(r"^\d+\.\d+\.?\s+", s):
        return True
    if re.match(r"^[a-z]\)\s*", s):
        return True
    if s in {"-", "•", "●"}:
        return True
    if re.match(r"^[•●-]\s+", s):
        return True
    return False

def build_blocks(lines, privacy=False):
    blocks = []
    buf = ""

    def flush():
        nonlocal buf
        if buf.strip():
            blocks.append(buf.strip())
        buf = ""

    for s in lines:
        if s.upper() in {
            "REGULAMIN APLIKACJI MOBILNEJ USLY",
            "TERMS AND CONDITIONS OF THE USLY",
            "MOBILE APP",
            "USLY APP PRIVACY POLICY",
        }:
            continue
        if s.startswith("Obowiązuje od dnia:") or s.startswith("Effective from:") or s.startswith("Wersja:") or s.startswith("Version:"):
            continue

        if is_new_block(s, privacy=privacy):
            flush()
            buf = s
        else:
            if not buf:
                buf = s
            elif is_heading(buf, privacy=privacy):
                flush()
                buf = s
            else:
                sep = "" if buf.endswith(("-", "/", "–")) else " "
                buf += sep + s
    flush()

    # merge broken title from EN terms if it survived
    fixed = []
    for b in blocks:
        b = b.replace("  ", " ").strip()
        b = b.replace("PUGUA Sp. z o.o z", "PUGUA Sp. z o.o. z")
        b = b.replace("PUGUA Sp. z o.o.,", "PUGUA Sp. z o.o.,")
        fixed.append(b)
    return fixed

def block_html(block, privacy=False):
    esc = html.escape(block)
    if block.startswith("§ "):
        slug = re.sub(r"[^a-zA-Z0-9]+", "-", block.lower()).strip("-")
        return f'<h2 id="{slug}">{esc}</h2>'
    if privacy and re.match(r"^\d+\.\s+[^a-ząćęłńóśźż]+$", block):
        slug = re.sub(r"[^a-zA-Z0-9]+", "-", block.lower()).strip("-")
        return f'<h2 id="{slug}">{esc}</h2>'
    if re.match(r"^[a-z]\)\s*", block):
        return f'<p class="letter-item">{esc}</p>'
    if block.startswith(("-", "•", "●")):
        cleaned = re.sub(r"^[•●-]\s*", "", block)
        return f'<p class="bullet-item">{html.escape(cleaned)}</p>'
    if re.match(r"^\d+\.\d+\.?\s+", block):
        return f'<p class="subclause">{esc}</p>'
    if re.match(r"^\d+\.\s+", block):
        return f'<p class="clause">{esc}</p>'
    return f'<p>{esc}</p>'

def make_page(cfg):
    privacy = "privacy" in cfg["src"].name
    blocks = build_blocks(clean_lines(cfg["src"]), privacy=privacy)
    content = "\n".join(block_html(b, privacy=privacy) for b in blocks)
    headings = []
    for b in blocks:
        if b.startswith("§ ") or (privacy and re.match(r"^\d+\.\s+[^a-ząćęłńóśźż]+$", b)):
            slug = re.sub(r"[^a-zA-Z0-9]+", "-", b.lower()).strip("-")
            headings.append((slug, b))

    toc = "\n".join(f'<a href="#{slug}">{html.escape(text)}</a>' for slug, text in headings)

    html_doc = f'''<!doctype html>
<html lang="{cfg["lang"]}">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>{html.escape(cfg["label"])} | USLY</title>
  <link rel="stylesheet" href="/legal/legal.css" />
</head>
<body>
  <header class="legalHeader">
    <div class="wrap nav">
      <a class="brand" href="/">
        <img src="/assets/logo-usly.png" alt="USLY" onerror="this.style.display='none'" />
        <span>USLY</span>
      </a>
      <nav class="navLinks">
        <a href="/regulamin">Regulamin</a>
        <a href="/polityka-prywatnosci">Polityka prywatności</a>
        <a href="{cfg["switch_href"]}" class="pill">{cfg["switch_label"]}</a>
      </nav>
    </div>
  </header>

  <main class="wrap legalLayout">
    <aside class="tocCard">
      <div class="tocTitle">Spis treści</div>
      <nav class="toc">{toc}</nav>
    </aside>

    <article class="legalCard">
      <div class="eyebrow">Dokument prawny USLY</div>
      <h1>{html.escape(cfg["title"])}</h1>

      <div class="metaGrid">
        <div><span>Wersja</span><strong>{html.escape(cfg["version"])}</strong></div>
        <div><span>Obowiązuje od</span><strong>{html.escape(cfg["effective"])}</strong></div>
        <div><span>Administrator</span><strong>PUGUA Sp. z o.o.</strong></div>
      </div>

      <div class="notice">
        Aktualna publiczna wersja dokumentu. Oryginał dokumentu prawnego jest archiwizowany wewnętrznie.
      </div>

      <section class="legalContent">
        {content}
      </section>

      <section class="changeLog">
        <h2>Historia zmian</h2>
        <p><strong>{html.escape(cfg["version"])}</strong> — pierwsza publiczna wersja dokumentu opublikowana dla aplikacji USLY.</p>
      </section>
    </article>
  </main>

  <footer class="legalFooter">
    <div class="wrap">
      <p>© 2026 PUGUA Sp. z o.o. · USLY</p>
      <p><a href="/regulamin">Regulamin</a> · <a href="/polityka-prywatnosci">Polityka prywatności</a> · <a href="/kontakt">Kontakt</a></p>
    </div>
  </footer>

  <script src="/legal/legal.js"></script>
</body>
</html>
'''
    cfg["out"].write_text(html_doc, encoding="utf-8")
    print(f"OK {cfg['out']} blocks={len(blocks)} headings={len(headings)}")

def main():
    for cfg in PAGES:
        make_page(cfg)

if __name__ == "__main__":
    main()
