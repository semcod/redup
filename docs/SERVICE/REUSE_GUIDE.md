---
{
  "schema": "wellmanifest.docs/document/v2",
  "id": "reuse-guide",
  "kind": "service",
  "version": 1,
  "title": "Ponowne wykorzystanie kodu semcod/redup",
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

# Ponowne wykorzystanie kodu semcod/redup

<!-- docs:section summary -->
## Cel i rezultat

Określa kolejność odkrywania i oceny istniejących modułów przed nową implementacją.

<!-- docs:section details -->
## Zakres i rozwiązanie

Repozytorium `semcod/redup`, obserwowana wersja `0.4.48`, baza `17ab187b37df23c66627b733c2b9c6f507138bf7`. Źródła: [pyproject.toml](../../pyproject.toml), [VERSION](../../VERSION), [src/redup/__main__.py](../../src/redup/__main__.py), [src/redup/mcp/server.py](../../src/redup/mcp/server.py).

Obserwowano 0 istniejących artefaktów związanych z reuse. Wykorzystaj narzędzia `semcod/search`, `semcod/redup` oraz istniejące pakiety, zachowując ich kontrakty i licencje.

Sekwencja: DISCOVER → COMPARE → EXTRACT → CONSUME → VERIFY. Szukaj po dokładnym identyfikatorze `semcod/redup`, by uniknąć pomylenia projektów o tej samej nazwie. Nie uruchamiaj automatycznej ekstrakcji na podstawie samego podobieństwa.

<!-- docs:section validation -->
## Weryfikacja

Najpierw `subactor-search ask "semcod/redup" --json`, potem `redup scan .`. Zweryfikuj rzeczywiste wyniki oraz testy konsumentów. Szkic planu istnieje w zewnętrznym zestawie PLF-012; skanów tego repozytorium nie deklarujemy jako wykonanych.

<!-- docs:section risks -->
## Ryzyka i następny krok

Wspólny kod może mieć różnych właścicieli, semantykę i uprawnienia. Ekstrakcja wymaga osobnego ticketu i jawnej granicy API; dokumentacja nie przekazuje prawa do modyfikacji innych repozytoriów.
