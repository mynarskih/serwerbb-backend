# Rzeczywisty wynik kontroli — 2026-10-12

Python syntax PASS; Docker build serwerbb-backend:github-review PASS. Brak odrębnego zestawu testów w źródłach.

## Sekrety i dane

Gitleaks 8.30.1: przygotowany zestaw źródeł PASS. Wykluczono rzeczywiste .env, token DDNS, dane NAS, prywatne zasoby, bazy, kopie, zależności i wyniki buildów. Szablony .env.example zawierają nazwy oraz puste wartości/przykładową konfigurację. W Temp Mail sprawdzono także całą oryginalną historię --all, bez wykryć. Dokładny finalny zestaw wersjonowanych plików i SHA zapisuje projects-index/MANIFESTY.json po przygotowaniu commitów.

Sprawdzono pliki już śledzone; .gitignore nie był traktowany jako dowód braku sekretów. Kod obejmuje przykładowe dane testowe i publiczne treści stron, ale nie bazy klientów/użytkowników, sesje lub listy kontaktów. Skaner nie gwarantuje wykrycia każdego nietypowego sekretu ani wszystkich danych osobowych; przegląd obejmował źródła/config oraz wykluczenie danych lokalnych. Nie przepisywano historii.

## Zależności

Brak zależności npm/Python spoza biblioteki standardowej w źródłach tego projektu. Sprawdzono lokalne obrazy przez Trivy; wynik obrazu nie jest wynikiem npm audit.


## Obrazy Docker i ograniczenia

Lokalny Trivy 0.75.0 przeskanował obrazy bez wysyłania kodu. Obrazy działających aplikacji pochodzą z obecnego wdrożenia, nie z poprawionych kopii źródeł. Szczegółowe CVE i wersje: projects-index/AUDYT-DOCKER.json, podsumowanie: projects-index/RAPORT.md. Nie restartowano produkcji, nie zmieniano sekretów ani danych. Aktualizacja baz/obrazów i odtwarzanie wymagają osobnego planu wdrożenia. Lokalny build JS nie jest skanem nowego kompletnego obrazu produkcyjnego.

## GitHub — stan po publikacji

- Repozytorium: https://github.com/HMpower1/serwerbb-backend — prywatność potwierdzona przez API.
- Gałąź: main; opublikowany commit wydania: 20d855f31f94191d16a4edc67d266a7d5c704c7f.
- Tag v0.1.0 wskazuje commit 20d855f31f94191d16a4edc67d266a7d5c704c7f; zgodność lokalnego i zdalnego tagu potwierdzona.
- Wydanie: https://github.com/HMpower1/serwerbb-backend/releases/tag/v0.1.0 — prerelease.
- CI commita wydania: success, https://github.com/HMpower1/serwerbb-backend/actions/runs/38307014568.
- Włączone: Dependabot alerts, security updates oraz read-only workflow permissions; odczytane przez API. Secret Scanning/push protection niedostępne: Secret scanning is not available for this repository.
- Wyniki ochrony gałęzi i CI kolejnych commitów dokumentacji: aktualny RAPORT.md oraz STATUS-GITHUB.json w projects-index.

Commity dokumentacji po publikacji nie przepisują historii i nie zmieniają taga wydania. Oryginalne wdrożenie oraz dane nie były zmieniane.
