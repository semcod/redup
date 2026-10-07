---
{
  "schema": "wellmanifest.docs/document/v2",
  "id": "user-manual",
  "kind": "service",
  "version": 3,
  "title": "Podręcznik operatora semcod/redup",
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
    "repo://semcod/redup/src/redup/mcp/server.py",
    "repo://semcod/redup/README.md"
  ]
}
---

# Podręcznik operatora semcod/redup

<!-- docs:section summary -->
## Cel i rezultat

Udostępnia operatorowi źródła konfiguracji i odróżnia udokumentowany interfejs od nieweryfikowanych możliwości.

<!-- docs:section details -->
## Zakres i rozwiązanie

Repozytorium `semcod/redup`, obserwowana wersja `0.4.48`, baza `17ab187b37df23c66627b733c2b9c6f507138bf7`. Źródła: [pyproject.toml](../../pyproject.toml), [VERSION](../../VERSION), [src/redup/__main__.py](../../src/redup/__main__.py), [src/redup/mcp/server.py](../../src/redup/mcp/server.py).

Model roboczy: [usermanual-observation.json](../standards/usermanual-observation.json). Zawiera 0 odczytów zmiennych środowiska, 0 literalnych tras GET i 0 literalnych tras mutacji z ograniczonej próbki kodu Python.

Przeczytaj README i źródła przed uruchomieniem. Prefiksy routerów, autoryzacja, wymagane wartości konfiguracji i idempotencja potrzebują przeglądu. Nie ustalono DSL, mapy UI ani aktywnego cyfrowego bliźniaka; puste tablice oznaczają brak dowodu w próbce.

## Udokumentowana obsługa

CLI analizy duplikacji ma polecenia scan, compare, diff, check, config i info. README opisuje też serwer MCP uruchamiany jako `redup-mcp`; używa on stdio, a diagnostyka trafia na stderr. Pierwsze wywołanie agentowe: find_duplicates, następnie analiza grup i testy konsumentów przed refaktoryzacją.

Źródło: [README](../../README.md) w podanej bazie. Powyższe instrukcje sprawdzono w źródle; nie wykonano opisanych uruchomień ani zmian usług.

## Deklaracje wejść CLI

- `redup` — python-entrypoint, źródło `pyproject.toml`.
- `redup-mcp` — python-entrypoint, źródło `pyproject.toml`.

Deklaracje potwierdzono w obiektach Git, bez uruchamiania poleceń. Dostępność programu, argumenty i efekty wymagają osobnej kontroli; nie kopiowano treści skryptów npm ani poświadczeń.

<!-- docs:section validation -->
## Weryfikacja

Model przechodzi schemat wellmanifest.usermanual/v1. Zbadano najwyżej osiem modułów Python; pozostałe języki i działające API nie były testowane. Pełny podręcznik wymaga analizy wszystkich publicznych interfejsów oraz testu driftu CQRS.

<!-- docs:section risks -->
## Ryzyka i następny krok

To podręcznik roboczy, a nie potwierdzenie gotowości produkcyjnej. Po weryfikacji modelu przygotuj normatywną publikację doc/USER_MANUAL.md i doc/usermanual.json w osobnym przyjętym zakresie. Nie ponawiaj mutacji bez dowodu idempotencji.
