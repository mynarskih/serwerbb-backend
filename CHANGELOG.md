# Historia zmian

## 0.1.0 — przygotowanie pierwszego wydania, 2026-10-12

- Zapis aktualnego kodu i zasobów projektu: Backend serwera domowego: Python 3.13, biblioteka standardowa, HTTP i SQLite. Dane kontaktów, użytkowników i sesji pozostają poza repozytorium.
- Dodanie reguł wykluczania sekretów, danych, zależności i wyników buildów.
- Dokumentacja uruchomienia, konfiguracji, kontroli i ograniczeń.
- Workflow CI z minimalnymi uprawnieniami i lokalnym skanowaniem Gitleaks.
- Backend Python stdlib i SQLite. Brak testów jednostkowych w tym katalogu; kontrola składni oraz izolowany build są planowane.

Wydanie przygotowywane jako prerelease. Nie tworzono historii wcześniejszych wydań. Istniejące numery w package.json pozostają zachowane. Szczegóły poprawionych zależności i wykonanych kontroli: KONTROLE.md. GitHub Release jeszcze nie utworzony.

### Końcowa kontrola przygotowanej kopii

Python syntax PASS; Docker build serwerbb-backend:github-review PASS. Brak odrębnego zestawu testów w źródłach.

Brak zależności npm/Python spoza biblioteki standardowej w źródłach tego projektu. Sprawdzono lokalne obrazy przez Trivy; wynik obrazu nie jest wynikiem npm audit.

