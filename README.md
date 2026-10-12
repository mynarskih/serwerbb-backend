
## Przygotowanie prywatnego repozytorium — 2026-10-12

Backend serwera domowego: Python 3.13, biblioteka standardowa, HTTP i SQLite. Dane kontaktów, użytkowników i sesji pozostają poza repozytorium.

Źródło bieżącego wdrożenia: `C:\Users\hmpow\Documents\Codex\2026-09-23\chc-skonfigurowa-m-j-domowy-serwer\server-infra\backend`. Ten katalog jest oddzielną kopią przygotowaną do wersjonowania; działające kontenery nadal używają oryginału. Nie przeniesiono baz danych ani wolumenów. Nie dodano licencji open source.

### Wymagania i instalacja

Windows/PowerShell, Git, Docker Desktop z kontenerami Linux i Compose obsługującym `!override` (2.24.4 lub nowszy). Aplikacje JS wymagają Node.js 22.13+; projekty z pnpm używają pnpm 11.19.0. Backend wymaga Python 3.13 przy uruchomieniu poza Dockerem. Klonuj dopiero po utworzeniu potwierdzonego prywatnego repozytorium.

### Konfiguracja, uruchomienie i testy

```powershell
python -m py_compile app.py
docker build -t serwerbb-backend:dev .
# Izolowane uruchomienie bez produkcyjnego wolumenu i zewnętrznych sieci:
docker run --rm -p 127.0.0.1:18081:8080 --tmpfs /data:uid=65534,gid=65534,mode=0700 serwerbb-backend:dev
```

Wartości `.env.example` są szablonem, nie konfiguracją produkcyjną. Wypełnij lokalny `.env` niezależnymi losowymi sekretami; nie zastępuj działających kluczy bez planu rotacji. Porty i sieci produkcyjne są zajęte: używaj osobnego projektu Compose i wolnych portów. Temp Mail w wariancie domowym współdzieli bramę; pełne odizolowanie wymaga dodatkowej konfiguracji sieci i routingu. Nie wykonuj `down -v` na produkcji.

### Faktyczny stan kontroli i ograniczenia

Backend Python stdlib i SQLite. Brak testów jednostkowych w tym katalogu; kontrola składni oraz izolowany build są planowane.

Wyniki końcowe i audyt po poprawkach opisuje `KONTROLE.md`. Workflow ma uprawnienie `contents: read`, brak sekretów, przypięte Actions i osobny skan Gitleaks przed instalacją zależności. Obecność workflow nie oznacza, że CI na GitHub zostało uruchomione. Zabezpieczenia konta, prywatność zdalnego repo i zgodność SHA wymagają sprawdzenia po wysłaniu. Pierwsze wydanie 0.1.0 należy oznaczyć jako prerelease.
