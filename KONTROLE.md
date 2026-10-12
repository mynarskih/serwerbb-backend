# Rzeczywisty wynik kontroli — 2026-10-12

Python syntax PASS; Docker build serwerbb-backend:github-review PASS. Brak odrębnego zestawu testów w źródłach.

## Sekrety i dane

Gitleaks 8.30.1: przygotowany zestaw źródeł PASS. Wykluczono rzeczywiste .env, token DDNS, dane NAS, prywatne zasoby, bazy, kopie, zależności i wyniki buildów. Szablony .env.example zawierają nazwy oraz puste wartości/przykładową konfigurację. W Temp Mail sprawdzono także całą oryginalną historię --all, bez wykryć. Dokładny finalny zestaw wersjonowanych plików i SHA zapisuje projects-index/MANIFESTY.json po przygotowaniu commitów.

Sprawdzono pliki już śledzone; .gitignore nie był traktowany jako dowód braku sekretów. Kod obejmuje przykładowe dane testowe i publiczne treści stron, ale nie bazy klientów/użytkowników, sesje lub listy kontaktów. Skaner nie gwarantuje wykrycia każdego nietypowego sekretu ani wszystkich danych osobowych; przegląd obejmował źródła/config oraz wykluczenie danych lokalnych. Nie przepisywano historii.

## Zależności

Brak zależności npm/Python spoza biblioteki standardowej w źródłach tego projektu. Sprawdzono lokalne obrazy przez Trivy; wynik obrazu nie jest wynikiem npm audit.


## Obrazy Docker i ograniczenia

Lokalny Trivy 0.75.0 przeskanował obrazy bez wysyłania kodu. Obrazy działających aplikacji pochodzą z obecnego wdrożenia, nie z poprawionych kopii źródeł. Szczegółowe CVE i wersje: projects-index/AUDYT-DOCKER.json, podsumowanie: projects-index/RAPORT.md. Nie restartowano produkcji, nie zmieniano sekretów ani danych. Aktualizacja baz/obrazów i odtwarzanie wymagają osobnego planu wdrożenia. Lokalny build JS nie jest skanem nowego kompletnego obrazu produkcyjnego.

## GitHub

Repozytorium zdalne, prywatność, SHA i tag, CI oraz Release: jeszcze niewykonane. Nie ma potwierdzonego uwierzytelnienia CLI. Pliki workflow i Dependabot są przygotowane; nie oznacza to aktywacji zabezpieczeń na GitHub. Nie aktywowano płatnych dodatków ani próbnych subskrypcji.
