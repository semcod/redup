---
{
  "schema": "wellmanifest.docs/document/v2",
  "id": "documentation-guide",
  "kind": "service",
  "version": 1,
  "title": "Dokumentacja operacyjna semcod/redup",
  "status": "proposed",
  "owner": "semcod/redup",
  "scope": "repository",
  "updated": "2026-10-07",
  "source_revision": "17ab187b37df23c66627b733c2b9c6f507138bf7",
  "priority": "P2",
  "evidence": [
    "repo://semcod/redup/pyproject.toml",
    "repo://semcod/redup/VERSION",
    "repo://semcod/redup/src/redup/__main__.py",
    "repo://semcod/redup/src/redup/mcp/server.py"
  ]
}
---

# Dokumentacja operacyjna semcod/redup

<!-- docs:section summary -->
## Cel i rezultat

Porządkuje cztery przewodniki i zakres ich odbioru w repozytorium właściciela.

<!-- docs:section details -->
## Zakres i rozwiązanie

Repozytorium `semcod/redup`, obserwowana wersja `0.4.48`, baza `17ab187b37df23c66627b733c2b9c6f507138bf7`. Źródła: [pyproject.toml](../../pyproject.toml), [VERSION](../../VERSION), [src/redup/__main__.py](../../src/redup/__main__.py), [src/redup/mcp/server.py](../../src/redup/mcp/server.py).

Używany pin docs: `0714f71462202788e6b775ed145e9e61a7d5c366`. Indeksem jest [docs/README.md](../README.md). Nowe dokumenty mają profil kompaktowy v2, cztery sekcje i najwyżej 120 linii oraz 600 słów. Aktualizuj temat i wersję istniejącego dokumentu zamiast tworzyć kopię.

[Logi](LOGGING_GUIDE.md), [reuse](REUSE_GUIDE.md), [podręcznik](USER_MANUAL.md).

<!-- docs:section validation -->
## Weryfikacja

Kontrola przygotowania wybiera właściciela i ścieżkę. Po zapisaniu i dodaniu dokumentu do Git kontrola `--complete` wymaga osobnego receiptu przygotowania, jawnego rezultatu i zaufanej bazy. Wyniki są rejestrowane poza Git.

<!-- docs:section risks -->
## Ryzyka i następny krok

Walidacja formatu nie potwierdza prawdziwości opisu ani publikacji. Zachowaj dotychczasowy pin; jego zmiana wymaga przyjęcia nowej rewizji, a merge niezależnego Validatora.
