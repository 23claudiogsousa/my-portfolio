#!/usr/bin/env python3
"""Small, dependency-free checks for the static portfolio site.

Usage:
    python3 test_site.py
    python3 test_site.py --url http://127.0.0.1:8000
    python3 test_site.py --skip-http  # check files without starting the server
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import URLError
from urllib.parse import unquote, urljoin, urlparse
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parent


class SiteParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: list[str] = []
        self.references: list[str] = []
        self.translations: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if values.get("id"):
            self.ids.append(values["id"] or "")
        for name in ("src", "href"):
            value = values.get(name)
            if value:
                self.references.append(value)
        if values.get("data-i18n"):
            self.translations.append(values["data-i18n"] or "")
        for name in ("data-i18n-aria-label", "data-i18n-alt"):
            if values.get(name):
                self.translations.append(values[name] or "")


def check(condition: bool, message: str, failures: list[str]) -> None:
    if condition:
        print(f"  PASS  {message}")
    else:
        print(f"  FAIL  {message}")
        failures.append(message)


def local_path(reference: str, base_file: Path = ROOT / "index.html") -> Path | None:
    parsed = urlparse(reference)
    if parsed.scheme or parsed.netloc or reference.startswith(("#", "data:")):
        return None
    relative = unquote(parsed.path)
    if not relative:
        return None
    return (base_file.parent / relative).resolve()


def translation_keys(source: str, language: str) -> set[str]:
    start = source.find("var strings = {")
    meta = source.find("\n  var meta = {", start)
    if start < 0 or meta < 0:
        return set()
    section = source[start:meta]
    if language == "en":
        split = section.find('"en": {')
        section = section[split:] if split >= 0 else ""
    else:
        split = section.find('"en": {')
        section = section[:split] if split >= 0 else section
    return set(re.findall(r'^\s*"([^"\n]+)"\s*:', section, re.MULTILINE))


def check_http(base_url: str, references: list[str], failures: list[str]) -> None:
    print(f"\nHTTP checks ({base_url})")
    refs = ["", "styles.css", "script.js", "i18n.js"]
    refs.extend(
        reference
        for reference in references
        if reference.startswith("assets/")
    )
    checked: set[str] = set()
    for reference in refs:
        target = urljoin(base_url.rstrip("/") + "/", reference)
        if target in checked:
            continue
        checked.add(target)
        try:
            with urlopen(target, timeout=4) as response:
                check(response.status == 200, f"HTTP 200 {target}", failures)
        except (URLError, TimeoutError, OSError) as error:
            check(False, f"conectividade com {target} ({error})", failures)


def main() -> int:
    parser = argparse.ArgumentParser(description="Testa os arquivos do portfólio.")
    parser.add_argument(
        "--url",
        default="http://127.0.0.1:8000",
        help="endereço do servidor local (padrão: http://127.0.0.1:8000)",
    )
    parser.add_argument(
        "--skip-http",
        action="store_true",
        help="executa apenas as verificações de arquivos, sem servidor",
    )
    args = parser.parse_args()

    failures: list[str] = []
    html_file = ROOT / "index.html"
    html = html_file.read_text(encoding="utf-8")
    parsed = SiteParser()
    parsed.feed(html)
    parsed.close()

    print("Verificações locais")
    duplicate_ids = sorted(key for key, count in Counter(parsed.ids).items() if count > 1)
    check(not duplicate_ids, "IDs do HTML são únicos" if not duplicate_ids else f"IDs duplicados: {', '.join(duplicate_ids)}", failures)

    missing = sorted(
        str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)
        for reference in parsed.references
        if (path := local_path(reference)) is not None and not path.is_file()
    )
    check(not missing, "referências locais do HTML existem" if not missing else f"arquivos ausentes: {', '.join(missing)}", failures)

    ids = set(parsed.ids)
    broken_anchors = sorted(
        reference
        for reference in parsed.references
        if reference.startswith("#") and reference[1:] not in ids
    )
    check(not broken_anchors, "âncoras internas apontam para IDs existentes" if not broken_anchors else f"âncoras inválidas: {', '.join(broken_anchors)}", failures)

    css = (ROOT / "styles.css").read_text(encoding="utf-8")
    css_refs = re.findall(r"url\([\"']?([^\"')]+)", css)
    missing_css = [
        ref for ref in css_refs
        if not unquote(ref).startswith("#")
        and (path := local_path(ref, ROOT / "styles.css")) is not None
        and not path.is_file()
    ]
    check(not missing_css, "referências locais do CSS existem" if not missing_css else f"arquivos ausentes no CSS: {', '.join(missing_css)}", failures)

    i18n = (ROOT / "i18n.js").read_text(encoding="utf-8")
    missing_translations = {
        language: sorted(set(parsed.translations) - translation_keys(i18n, language))
        for language in ("pt", "en")
    }
    absent = [f"{lang}: {', '.join(keys)}" for lang, keys in missing_translations.items() if keys]
    check(not absent, "todas as chaves de tradução existem em PT e EN" if not absent else f"traduções ausentes ({'; '.join(absent)})", failures)

    if not args.skip_http:
        check_http(args.url, parsed.references, failures)

    print(f"\nResultado: {'SUCESSO' if not failures else f'{len(failures)} falha(s)'}")
    if failures and not args.skip_http:
        print("Se o servidor não estiver ativo, inicie-o com: python3 -m http.server 8000")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
