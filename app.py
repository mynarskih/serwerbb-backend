import hashlib
import hmac
import html
import json
import os
import re
import secrets
import socket
import sqlite3
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from http import cookies
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse


STARTED_AT = datetime.now(timezone.utc)
DB_PATH = os.getenv("DB_PATH", "/data/serwerbb.db")
SERVICES = {
    "website": ("strona-web", 80),
    "portfolio": ("portfolio-web", 80),
    "files": ("voidnas-api-1", 3000),
}
SESSIONS = {}
CONTACT_LIMITS = {}
LOGIN_LIMITS = {}
ANALYTICS_LIMITS = {}
STATE_LOCK = threading.Lock()


def utc_now():
    return datetime.now(timezone.utc)


def db():
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA foreign_keys=ON")
    return connection


def initialize_database():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with db() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                subject TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TEXT NOT NULL,
                is_read INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                summary TEXT NOT NULL,
                body TEXT NOT NULL,
                created_at TEXT NOT NULL,
                published INTEGER NOT NULL DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                summary TEXT NOT NULL,
                body TEXT NOT NULL,
                category TEXT NOT NULL,
                url TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                published INTEGER NOT NULL DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS status_samples (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                checked_at TEXT NOT NULL,
                service TEXT NOT NULL,
                status TEXT NOT NULL,
                latency_ms INTEGER NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_status_time ON status_samples(checked_at);
            CREATE TABLE IF NOT EXISTS analytics (
                day TEXT NOT NULL,
                path TEXT NOT NULL,
                device TEXT NOT NULL,
                views INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY(day, path, device)
            );
            """
        )
        if connection.execute("SELECT COUNT(*) FROM posts").fetchone()[0] == 0:
            connection.executemany(
                "INSERT INTO posts(slug,title,summary,body,created_at) VALUES(?,?,?,?,?)",
                [
                    (
                        "jak-powstal-serwerbb-win",
                        "Jak powstał serwerbb.win",
                        "Od domowego komputera do usług dostępnych przez własną domenę.",
                        "Projekt rozpoczął się od uporządkowania usług działających na jednym komputerze.\n\nDocker oddziela aplikacje, Caddy kieruje ruch do właściwego kontenera i automatycznie obsługuje HTTPS. Cloudflare DNS wraz z DDNS pilnuje, aby domena wskazywała aktualny adres publiczny.\n\nNajważniejszym założeniem było zachowanie prostoty: publicznie dostępne są wyłącznie potrzebne usługi WWW, a panele techniczne pozostają niewystawione.",
                        "2026-09-24T12:00:00+00:00",
                    ),
                    (
                        "nextcloud-jako-prywatna-chmura",
                        "Nextcloud jako prywatna chmura",
                        "Pliki, synchronizacja i edycja dokumentów na własnym serwerze.",
                        "Nextcloud pełni rolę prywatnej przestrzeni na dokumenty i inne materiały. Działa w przeglądarce oraz przez aplikacje na komputer i telefon.\n\nInstalacja została ograniczona do funkcji związanych z plikami. Maksymalny rozmiar pojedynczego przesyłanego pliku wynosi 20 GB, a połączenie jest chronione automatycznym HTTPS.\n\nDane pozostają na własnym serwerze, natomiast dostęp do nich wymaga zalogowania.",
                        "2026-09-24T12:10:00+00:00",
                    ),
                ],
            )
        if connection.execute("SELECT COUNT(*) FROM projects").fetchone()[0] == 0:
            now = "2026-09-24T12:20:00+00:00"
            connection.executemany(
                "INSERT INTO projects(slug,title,summary,body,category,url,created_at) VALUES(?,?,?,?,?,?,?)",
                [
                    ("serwerbb-win", "serwerbb.win", "Centrum usług i informacji o serwerze.", "Responsywna witryna łącząca prywatną chmurę, portfolio, przewodniki i informacje o bezpieczeństwie.", "web", "https://strona.serwerbb.win", now),
                    ("nextcloud", "Prywatna chmura", "Nextcloud do plików i dokumentów.", "Prywatna przestrzeń do przechowywania, synchronizacji, udostępniania oraz edycji plików.", "cloud", "https://nas.serwerbb.win", now),
                    ("portfolio", "Portfolio", "Prezentacja projektów i umiejętności.", "Szybkie, dostępne i responsywne portfolio z opisami realizacji oraz domowego laboratorium.", "web", "https://portfolio.serwerbb.win", now),
                    ("homelab", "Domowy serwer", "Docker, Caddy, DDNS i HTTPS.", "Infrastruktura łącząca kontenery, automatyczny DNS, reverse proxy, monitoring i prywatną chmurę.", "infra", "https://portfolio.serwerbb.win/homelab/", now),
                ],
            )


def check_service(item):
    service_id, (host, port) = item
    started = time.perf_counter()
    try:
        with socket.create_connection((host, port), timeout=0.8):
            latency = max(1, round((time.perf_counter() - started) * 1000))
            return service_id, "online", latency
    except OSError:
        return service_id, "offline", 0


def live_statuses():
    with ThreadPoolExecutor(max_workers=len(SERVICES)) as pool:
        results = list(pool.map(check_service, SERVICES.items()))
    return {service: {"status": status, "latencyMs": latency} for service, status, latency in results}


def record_statuses():
    checked_at = utc_now().isoformat(timespec="seconds")
    statuses = live_statuses()
    with db() as connection:
        connection.executemany(
            "INSERT INTO status_samples(checked_at,service,status,latency_ms) VALUES(?,?,?,?)",
            [(checked_at, service, value["status"], value["latencyMs"]) for service, value in statuses.items()],
        )
        cutoff = (utc_now() - timedelta(days=30)).isoformat(timespec="seconds")
        connection.execute("DELETE FROM status_samples WHERE checked_at < ?", (cutoff,))
    return statuses


def monitor_loop():
    while True:
        try:
            record_statuses()
        except Exception:
            pass
        time.sleep(60)


def password_hash(password, salt=None):
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 310000)
    return salt.hex(), digest.hex()


def password_configured():
    with db() as connection:
        return connection.execute("SELECT 1 FROM settings WHERE key='admin_hash'").fetchone() is not None


def set_password(password):
    salt, digest = password_hash(password)
    with db() as connection:
        connection.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('admin_salt',?)", (salt,))
        connection.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('admin_hash',?)", (digest,))


def verify_password(password):
    with db() as connection:
        salt_row = connection.execute("SELECT value FROM settings WHERE key='admin_salt'").fetchone()
        hash_row = connection.execute("SELECT value FROM settings WHERE key='admin_hash'").fetchone()
    if not salt_row or not hash_row:
        return False
    _, candidate = password_hash(password, bytes.fromhex(salt_row[0]))
    return hmac.compare_digest(candidate, hash_row[0])


def slugify(value):
    value = value.lower().strip()
    replacements = str.maketrans("ąćęłńóśźż", "acelnoszz")
    value = value.translate(replacements)
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value[:80] or f"wpis-{int(time.time())}"


class Handler(BaseHTTPRequestHandler):
    server_version = "SerwerBB"
    sys_version = ""

    def _security_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        self.send_header("X-Frame-Options", "DENY")

    def send_json(self, status, payload, extra_headers=None):
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("X-Robots-Tag", "noindex, nofollow")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self._security_headers()
        for name, value in (extra_headers or {}).items():
            self.send_header(name, value)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def send_html(self, status, content):
        body = content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self._security_headers()
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def read_body(self, limit=65536):
        length = int(self.headers.get("Content-Length", "0"))
        if length < 0 or length > limit:
            raise ValueError("request_too_large")
        return self.rfile.read(length)

    def read_json(self, limit=65536):
        try:
            return json.loads(self.read_body(limit).decode("utf-8"))
        except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
            raise ValueError("invalid_json")

    def client_key(self):
        forwarded = self.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        return forwarded or self.client_address[0]

    def session(self):
        cookie = cookies.SimpleCookie(self.headers.get("Cookie", ""))
        token = cookie.get("admin_session")
        if not token:
            return None
        with STATE_LOCK:
            session = SESSIONS.get(token.value)
            if not session or session["expires"] < time.time():
                SESSIONS.pop(token.value, None)
                return None
            return session

    def require_admin(self, csrf=False):
        session = self.session()
        if not session:
            self.send_json(401, {"error": "unauthorized", "setupRequired": not password_configured()})
            return None
        if csrf and not hmac.compare_digest(self.headers.get("X-CSRF-Token", ""), session["csrf"]):
            self.send_json(403, {"error": "invalid_csrf"})
            return None
        return session

    def local_setup_allowed(self):
        host = self.headers.get("Host", "").split(":")[0].lower()
        return host in {"127.0.0.1", "localhost", "[::1]"}

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        if path == "/health":
            self.send_json(200, {"status": "ok"})
            return
        if path == "/local-setup":
            if not self.local_setup_allowed():
                self.send_json(403, {"error": "local_only"})
                return
            configured = password_configured()
            form = "<p>Hasło administratora jest już ustawione.</p>" if configured else """
                <form method="post" action="/local-setup">
                  <label>Nowe hasło administratora<input name="password" type="password" minlength="12" required autocomplete="new-password"></label>
                  <label>Powtórz hasło<input name="confirm" type="password" minlength="12" required autocomplete="new-password"></label>
                  <button type="submit">Ustaw hasło</button>
                </form>
            """
            self.send_html(200, f"""<!doctype html><html lang="pl"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Konfiguracja administratora</title><style>body{{max-width:560px;margin:5rem auto;padding:1rem;background:#091222;color:#edf7ff;font:16px system-ui}}form,label{{display:grid;gap:.6rem}}form{{gap:1rem}}input,button{{min-height:48px;padding:.7rem;border-radius:.7rem;border:1px solid #50657d;font:inherit}}button{{background:#62dce5;color:#071525;font-weight:800;cursor:pointer}}</style><h1>Panel administratora</h1><p>Ta strona działa wyłącznie lokalnie na serwerze.</p>{form}</html>""")
            return
        if path == "/api/status":
            statuses = live_statuses()
            simple = {key: value["status"] for key, value in statuses.items()}
            self.send_json(200, {"status": "online" if all(v == "online" for v in simple.values()) else "degraded", "service": "serwerbb.win", "services": simple, "details": statuses, "checkedAt": utc_now().isoformat(timespec="seconds"), "uptimeSeconds": int((utc_now() - STARTED_AT).total_seconds())})
            return
        if path == "/api/status/history":
            hours = max(1, min(720, int(query.get("hours", ["24"])[0])))
            cutoff = (utc_now() - timedelta(hours=hours)).isoformat(timespec="seconds")
            with db() as connection:
                rows = connection.execute("SELECT checked_at,service,status,latency_ms FROM status_samples WHERE checked_at>=? ORDER BY checked_at", (cutoff,)).fetchall()
            self.send_json(200, {"hours": hours, "samples": [dict(row) for row in rows]})
            return
        if path == "/api/content/posts":
            with db() as connection:
                rows = connection.execute("SELECT id,slug,title,summary,created_at FROM posts WHERE published=1 ORDER BY created_at DESC").fetchall()
            self.send_json(200, {"posts": [dict(row) for row in rows]})
            return
        if path == "/api/content/post":
            slug = query.get("slug", [""])[0][:80]
            with db() as connection:
                row = connection.execute("SELECT id,slug,title,summary,body,created_at FROM posts WHERE slug=? AND published=1", (slug,)).fetchone()
            self.send_json(200, {"post": dict(row) if row else None})
            return
        if path == "/api/content/projects":
            with db() as connection:
                rows = connection.execute("SELECT id,slug,title,summary,body,category,url,created_at FROM projects WHERE published=1 ORDER BY id").fetchall()
            self.send_json(200, {"projects": [dict(row) for row in rows]})
            return
        if path == "/api/search":
            term = query.get("q", [""])[0].strip()[:80]
            like = f"%{term}%"
            results = []
            if len(term) >= 2:
                with db() as connection:
                    for row in connection.execute("SELECT slug,title,summary FROM posts WHERE published=1 AND (title LIKE ? OR summary LIKE ? OR body LIKE ?) LIMIT 12", (like, like, like)):
                        results.append({"type": "Artykuł", "title": row["title"], "summary": row["summary"], "url": f"https://portfolio.serwerbb.win/blog/wpis/?slug={row['slug']}"})
                    for row in connection.execute("SELECT slug,title,summary,url FROM projects WHERE published=1 AND (title LIKE ? OR summary LIKE ? OR body LIKE ?) LIMIT 12", (like, like, like)):
                        results.append({"type": "Projekt", "title": row["title"], "summary": row["summary"], "url": row["url"] or f"https://portfolio.serwerbb.win/projekty/{row['slug']}/"})
            self.send_json(200, {"query": term, "results": results[:20]})
            return
        if path == "/api/admin/dashboard":
            session = self.require_admin()
            if not session:
                return
            with db() as connection:
                contacts = [dict(row) for row in connection.execute("SELECT id,name,email,subject,message,created_at,is_read FROM contacts ORDER BY created_at DESC LIMIT 100")]
                analytics = [dict(row) for row in connection.execute("SELECT day,path,device,views FROM analytics WHERE day>=date('now','-30 day') ORDER BY day DESC,views DESC")]
                posts = [dict(row) for row in connection.execute("SELECT id,slug,title,summary,created_at,published FROM posts ORDER BY created_at DESC")]
                projects = [dict(row) for row in connection.execute("SELECT id,slug,title,summary,category,url,created_at,published FROM projects ORDER BY id")]
                unread = connection.execute("SELECT COUNT(*) FROM contacts WHERE is_read=0").fetchone()[0]
                views = connection.execute("SELECT COALESCE(SUM(views),0) FROM analytics WHERE day>=date('now','-30 day')").fetchone()[0]
            self.send_json(200, {"csrf": session["csrf"], "summary": {"unreadMessages": unread, "views30d": views, "posts": len(posts), "projects": len(projects)}, "contacts": contacts, "analytics": analytics, "posts": posts, "projects": projects})
            return
        self.send_json(404, {"error": "not_found"})

    do_HEAD = do_GET

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/local-setup":
            if not self.local_setup_allowed() or password_configured():
                self.send_json(403, {"error": "setup_unavailable"})
                return
            form = parse_qs(self.read_body(8192).decode("utf-8"))
            password = form.get("password", [""])[0]
            confirm = form.get("confirm", [""])[0]
            if len(password) < 12 or password != confirm:
                self.send_html(400, "<h1>Hasła nie są identyczne lub mają mniej niż 12 znaków.</h1><a href='/local-setup'>Wróć</a>")
                return
            set_password(password)
            self.send_html(200, "<h1>Hasło ustawione.</h1><p>Możesz zamknąć tę stronę i zalogować się na https://strona.serwerbb.win/admin/</p>")
            return
        if path == "/api/contact":
            try:
                data = self.read_json(32768)
            except ValueError:
                self.send_json(400, {"error": "invalid_request"})
                return
            if data.get("company"):
                self.send_json(200, {"ok": True})
                return
            name = str(data.get("name", "")).strip()[:100]
            email_address = str(data.get("email", "")).strip()[:180]
            subject = str(data.get("subject", "")).strip()[:140]
            message = str(data.get("message", "")).strip()[:5000]
            if len(name) < 2 or not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email_address) or len(subject) < 3 or len(message) < 10 or not data.get("privacy"):
                self.send_json(400, {"error": "validation"})
                return
            key = self.client_key()
            now = time.time()
            with STATE_LOCK:
                recent = [stamp for stamp in CONTACT_LIMITS.get(key, []) if stamp > now - 3600]
                if len(recent) >= 3:
                    self.send_json(429, {"error": "rate_limited"})
                    return
                recent.append(now)
                CONTACT_LIMITS[key] = recent
            with db() as connection:
                connection.execute("INSERT INTO contacts(name,email,subject,message,created_at) VALUES(?,?,?,?,?)", (name, email_address, subject, message, utc_now().isoformat(timespec="seconds")))
            self.send_json(201, {"ok": True})
            return
        if path == "/api/analytics":
            try:
                data = self.read_json(4096)
            except ValueError:
                self.send_json(400, {"error": "invalid_request"})
                return
            page_path = str(data.get("path", "/"))[:180]
            if not page_path.startswith("/") or page_path.startswith("/admin"):
                self.send_json(202, {"ok": True})
                return
            key = self.client_key()
            now = time.time()
            with STATE_LOCK:
                recent = [stamp for stamp in ANALYTICS_LIMITS.get(key, []) if stamp > now - 3600]
                if len(recent) >= 120:
                    self.send_json(202, {"ok": True})
                    return
                recent.append(now)
                ANALYTICS_LIMITS[key] = recent
            device = data.get("device") if data.get("device") in {"mobile", "desktop", "tablet"} else "other"
            day = utc_now().date().isoformat()
            with db() as connection:
                connection.execute("INSERT INTO analytics(day,path,device,views) VALUES(?,?,?,1) ON CONFLICT(day,path,device) DO UPDATE SET views=views+1", (day, page_path, device))
            self.send_json(202, {"ok": True})
            return
        if path == "/api/admin/login":
            if not password_configured():
                self.send_json(428, {"error": "setup_required"})
                return
            try:
                data = self.read_json(8192)
            except ValueError:
                self.send_json(400, {"error": "invalid_request"})
                return
            key = self.client_key()
            now = time.time()
            with STATE_LOCK:
                recent = [stamp for stamp in LOGIN_LIMITS.get(key, []) if stamp > now - 900]
                if len(recent) >= 5:
                    self.send_json(429, {"error": "rate_limited"})
                    return
            if not verify_password(str(data.get("password", ""))):
                with STATE_LOCK:
                    recent.append(now)
                    LOGIN_LIMITS[key] = recent
                time.sleep(0.5)
                self.send_json(401, {"error": "invalid_credentials"})
                return
            with STATE_LOCK:
                LOGIN_LIMITS.pop(key, None)
            token = secrets.token_urlsafe(32)
            csrf = secrets.token_urlsafe(24)
            with STATE_LOCK:
                SESSIONS[token] = {"csrf": csrf, "expires": time.time() + 28800}
            self.send_json(200, {"ok": True, "csrf": csrf}, {"Set-Cookie": f"admin_session={token}; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age=28800"})
            return
        if path == "/api/admin/logout":
            session = self.require_admin(csrf=True)
            if not session:
                return
            cookie = cookies.SimpleCookie(self.headers.get("Cookie", ""))
            token = cookie.get("admin_session")
            if token:
                with STATE_LOCK:
                    SESSIONS.pop(token.value, None)
            self.send_json(200, {"ok": True}, {"Set-Cookie": "admin_session=; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age=0"})
            return
        if path in {"/api/admin/posts", "/api/admin/projects"}:
            session = self.require_admin(csrf=True)
            if not session:
                return
            try:
                data = self.read_json(65536)
            except ValueError:
                self.send_json(400, {"error": "invalid_request"})
                return
            title = str(data.get("title", "")).strip()[:160]
            summary = str(data.get("summary", "")).strip()[:500]
            body = str(data.get("body", "")).strip()[:20000]
            if len(title) < 3 or len(summary) < 10 or len(body) < 20:
                self.send_json(400, {"error": "validation"})
                return
            slug = slugify(str(data.get("slug") or title))
            try:
                with db() as connection:
                    if path.endswith("posts"):
                        connection.execute("INSERT INTO posts(slug,title,summary,body,created_at) VALUES(?,?,?,?,?)", (slug, title, summary, body, utc_now().isoformat(timespec="seconds")))
                    else:
                        category = str(data.get("category", "inne"))[:40]
                        url = str(data.get("url", ""))[:500]
                        if category not in {"web", "cloud", "infra", "inne"} or (url and not re.match(r"^https?://", url, re.I)):
                            self.send_json(400, {"error": "validation"})
                            return
                        connection.execute("INSERT INTO projects(slug,title,summary,body,category,url,created_at) VALUES(?,?,?,?,?,?,?)", (slug, title, summary, body, category, url, utc_now().isoformat(timespec="seconds")))
            except sqlite3.IntegrityError:
                self.send_json(409, {"error": "slug_exists"})
                return
            self.send_json(201, {"ok": True, "slug": slug})
            return
        match = re.match(r"^/api/admin/messages/(\d+)/read$", path)
        if match:
            session = self.require_admin(csrf=True)
            if not session:
                return
            with db() as connection:
                connection.execute("UPDATE contacts SET is_read=1 WHERE id=?", (int(match.group(1)),))
            self.send_json(200, {"ok": True})
            return
        self.send_json(404, {"error": "not_found"})

    def do_DELETE(self):
        path = urlparse(self.path).path
        match = re.match(r"^/api/admin/(messages|posts|projects)/(\d+)$", path)
        if not match:
            self.send_json(404, {"error": "not_found"})
            return
        session = self.require_admin(csrf=True)
        if not session:
            return
        table = {"messages": "contacts", "posts": "posts", "projects": "projects"}[match.group(1)]
        with db() as connection:
            connection.execute(f"DELETE FROM {table} WHERE id=?", (int(match.group(2)),))
        self.send_json(200, {"ok": True})

    def log_message(self, _format, *_args):
        return


def main():
    initialize_database()
    threading.Thread(target=monitor_loop, daemon=True).start()
    server = ThreadingHTTPServer(("0.0.0.0", int(os.getenv("PORT", "8080"))), Handler)
    server.daemon_threads = True
    server.serve_forever()


if __name__ == "__main__":
    main()
