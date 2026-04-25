# RaceControl Pro – Entwickler-Handbuch

**Für Entwickler, die das System erweitern oder warten**  
Stand: April 2026 · Version 0.4.1

---

## Inhaltsverzeichnis

1. [Entwicklungsumgebung einrichten](#1-entwicklungsumgebung-einrichten)
2. [Projektstruktur](#2-projektstruktur)
3. [Backend-Architektur (FastAPI)](#3-backend-architektur-fastapi)
4. [Frontend-Architektur (Vue 3)](#4-frontend-architektur-vue-3)
5. [Authentifizierung & Rollen](#5-authentifizierung--rollen)
6. [WebSocket-System](#6-websocket-system)
7. [Datenbank & Migrationen](#7-datenbank--migrationen)
8. [Tests schreiben](#8-tests-schreiben)
9. [Neues Feature implementieren – Schritt für Schritt](#9-neues-feature-implementieren--schritt-für-schritt)
10. [CI/CD Pipeline](#10-cicd-pipeline)
11. [Coding-Konventionen](#11-coding-konventionen)

---

## 1. Entwicklungsumgebung einrichten

### Voraussetzungen

- Python 3.9+ (getestet mit 3.11 in CI)
- Node.js 18+ / npm
- Git

### Backend starten

```bash
cd RaceControl/backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Die SQLite-Datenbank `racecontrol.db` wird beim ersten Start automatisch aus `schema.sql` angelegt.  
Interaktive API-Dokumentation: `http://localhost:8000/docs`

### Frontend starten (Dev-Modus)

```bash
cd RaceControl/frontend
npm install
npm run dev
```

Läuft auf `http://localhost:5173`. Alle `/api/` und `/ws`-Aufrufe werden automatisch an Port 8000 proxyt (konfiguriert in `vite.config.js`).

### Beide zusammen (Empfehlung)

```bash
# Terminal 1
cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2
cd frontend && npm run dev
```

### Erster Login nach Neustart

Standardbenutzer `admin` wird beim ersten Start über `schema.sql` oder `seed.py` angelegt.  
Passwort über `http://localhost:8000/docs` → `POST /api/auth/login` testen oder `seed.py` ausführen.

---

## 2. Projektstruktur

```
RaceControl/
├── backend/
│   ├── main.py              # FastAPI-App, CORS, WebSocket-Endpoints, Static-Files
│   ├── database.py          # DB-Verbindung, init_db(), Migrations-Funktionen
│   ├── schema.sql           # SQLite-Schema (Single Source of Truth)
│   ├── schemas.py           # Pydantic-Modelle (Request/Response)
│   ├── deps.py              # Auth-Abhängigkeiten, require_roles()
│   ├── auth.py              # JWT (HS256), bcrypt-Passwortverwaltung
│   ├── broadcast.py         # BroadcastManager: WebSocket-Verbindungspool
│   ├── seed.py              # Testdaten-Seeder (Dev/Demo)
│   ├── routers/
│   │   ├── auth.py          # POST /api/auth/login
│   │   ├── events.py        # CRUD Events, Classes, Nennungsschluss, Announce
│   │   ├── participants.py  # CRUD Teilnehmer, suggest-class
│   │   ├── results.py       # Ergebnisse, Strafen, Standings, Views
│   │   ├── reglements.py    # CRUD Reglements + PenaltyDefinitions
│   │   ├── users.py         # CRUD Benutzer (admin only)
│   │   ├── clubs.py         # CRUD Vereine
│   │   ├── sponsors.py      # CRUD Sponsoren
│   │   ├── settings.py      # Druckvorlagen-Einstellungen
│   │   ├── public.py        # Öffentliche Endpunkte (kein Login)
│   │   ├── notifications.py
│   ├── marshal.py       # Streckenposten – Fehlerpunkt-Meldungen # POST /api/notifications (Push-Nachrichten)
│   │   └── import_router.py # CSV-Import Teilnehmer
│   └── tests/
│       ├── conftest.py      # Fixtures: db, client, admin_headers, class_id, …
│       ├── test_auth.py
│       ├── test_events.py
│       ├── test_participants.py
│       └── test_results.py
├── frontend/
│   ├── src/
│   │   ├── main.js          # Vue-App initialisieren, Pinia, Router
│   │   ├── App.vue          # Root-Komponente: Header, RouterView, StatusBar, Notifications
│   │   ├── api/client.js    # Axios-Instanz mit JWT-Header
│   │   ├── stores/
│   │   │   ├── auth.js      # Login/Logout, JWT-Persistenz, Rolle
│   │   │   └── event.js     # Aktive Veranstaltung, Klassen, Vereine
│   │   ├── router/index.js  # Routen-Definition + Rollen-Guard
│   │   ├── composables/
│   │   │   ├── useRealtimeUpdate.js  # WebSocket-Verbindung + Auto-Reconnect
│   │   │   └── useNetworkStatus.js  # Online/Offline-Erkennung
│   │   ├── components/
│   │   │   ├── AppHeader.vue   # Navigation, Live-Uhr, Logout
│   │   │   └── StatusBar.vue   # Verbindungsstatus, Versionsnummer
│   │   └── views/           # Eine Datei pro Seite/Rolle
│   ├── vite.config.js       # Vite + PWA + Dev-Proxy-Konfiguration
│   └── package.json
├── RaPi_lichtschranke/      # Raspberry Pi GPIO-Clients
├── tools/                   # ELV LSU200 USB-Client
├── schema.sql               # SQLite-Schema (direkt im Root — Backend und Tests lesen hier)
├── db_design.md             # Datenbankschema-Dokumentation
└── .github/workflows/ci.yml # GitHub Actions CI
```

---

## 3. Backend-Architektur (FastAPI)

### Routing-Prinzip

Alle API-Endpunkte haben das Präfix `/api`. Jeder Router wird in `main.py` registriert:

```python
app.include_router(events.router,    prefix="/api")
app.include_router(results.router,   prefix="/api")
app.include_router(notifications.router, prefix="/api")
# ...
```

Jeder Router definiert seinen eigenen Präfix:
```python
# events.py
router = APIRouter(prefix="/events", tags=["events"])
# → /api/events, /api/events/{id}/classes, …

# results.py
router = APIRouter(prefix="/events/{event_id}", tags=["results"])
# → /api/events/{id}/results, /api/events/{id}/standings, …
```

### Dependency Injection

Das Backend nutzt FastAPI-Abhängigkeiten (`Depends`) konsequent für:

**Datenbankverbindung:**
```python
# In jedem Endpoint-Handler:
db: Annotated[sqlite3.Connection, Depends(get_db)]
```
`get_db()` öffnet pro Request eine SQLite-Verbindung, setzt WAL-Modus und Foreign Keys, schließt sie am Ende.

**Authentifizierung:**
```python
# deps.py
CurrentUser = Annotated[sqlite3.Row, Depends(get_current_user)]

# Rollenprüfung:
AdminOnly = Annotated[sqlite3.Row, Depends(require_roles("admin"))]
ZeitnahmeOrAbove = Annotated[sqlite3.Row, Depends(require_roles("admin", "schiedsrichter", "zeitnahme"))]
```

### Pydantic-Schemas (`schemas.py`)

Jede Ressource hat drei Varianten:
- `XxxCreate` — eingehende Daten (POST/PATCH). **Path-Parameter** müssen als `Optional[int] = None` definiert sein, da sie erst nach Pydantic-Validierung gesetzt werden.
- `XxxUpdate` — Teilaktualisierung (alle Felder optional)
- `XxxResponse` — ausgehende Daten inkl. generierter Felder (id, created_at, ...)

```python
class ParticipantCreate(BaseModel):
    event_id:  Optional[int] = None  # wird vom Router gesetzt, nicht vom Client
    class_id:  Optional[int] = None
    first_name: str
    last_name:  str
    # ...
```

### Fehlerbehandlung

HTTP-Fehlercodes werden einheitlich verwendet:
- `404` — Ressource nicht gefunden
- `409` — Konflikt (z.B. UNIQUE-Verletzung, Klasse nicht in korrektem Status)
- `422` — Validierungsfehler (Pydantic)
- `403` — Keine Berechtigung (falsche Rolle)
- `401` — Nicht authentifiziert

```python
raise HTTPException(404, "Klasse nicht gefunden")
raise HTTPException(409, "Klasse läuft nicht – Zeiteingabe erst nach Klassenstart möglich")
```

---

## 4. Frontend-Architektur (Vue 3)

### State Management (Pinia)

Es gibt zwei globale Stores:

**`auth.js`** — Authentifizierung
```js
const auth = useAuthStore()
auth.isLoggedIn   // bool
auth.role         // "admin" | "zeitnahme" | ...
auth.user         // { id, username, role }
auth.login(token) // speichert JWT in localStorage
auth.logout()     // löscht Token, leitet auf / weiter
```

**`event.js`** — Veranstaltungsdaten
```js
const store = useEventStore()
store.activeEvent   // { id, name, date, location, … }
store.classes       // Array aller Klassen der aktiven Veranstaltung
store.clubs         // Array aller Vereine
store.loadEvents()  // lädt Events + setzt aktive Veranstaltung
store.selectEvent(event)
```

### API-Client (`api/client.js`)

Zentraler Axios-Wrapper mit automatischem JWT-Header:
```js
import api from '../api/client'

// Alle Requests gehen gegen /api/...
const { data } = await api.get(`/events/${id}/participants`)
await api.post(`/events/${id}/results`, { ... })
await api.patch(`/events/${id}/participants/${pid}`, { status: 'checked_in' })
```

Bei 401-Antwort wird automatisch ausgeloggt (Response-Interceptor).

### Routing & Rollenschutz (`router/index.js`)

Routen ohne `meta.roles` sind öffentlich. Mit `meta.roles` wird vor Navigation geprüft:
```js
{ path: '/zeitnahme', component: ZeitnahmeView, meta: { roles: ['admin', 'zeitnahme'] } }
{ path: '/nachrichten', component: NachrichtenView, meta: { roles: ['admin', 'zeitnahme', 'nennung', 'schiedsrichter'] } }
{ path: '/livetiming', component: LivetimingView, meta: { public: true } }
```

### Echtzeit-Updates (`useRealtimeUpdate`)

Composable für WebSocket-Verbindung mit Auto-Reconnect:
```js
import { useRealtimeUpdate } from '../composables/useRealtimeUpdate'

useRealtimeUpdate((msg) => {
  if (msg.type === 'results')      loadResults()
  if (msg.type === 'notification') showBanner(msg)
  if (msg.type === 'timing_result') setTimeField(msg.raw_time)
})
```

Reconnect nach 2,5 Sekunden bei Verbindungsabbruch — Views müssen nichts selbst implementieren.

### View-Struktur (typisches Muster)

```vue
<script setup>
import { ref, onMounted } from 'vue'
import api from '../api/client'
import { useEventStore } from '../stores/event'
import { useRealtimeUpdate } from '../composables/useRealtimeUpdate'

const store = useEventStore()
const data  = ref([])

async function load() {
  if (!store.activeEvent) return
  const { data: d } = await api.get(`/events/${store.activeEvent.id}/...`)
  data.value = d
}

// Echtzeit-Refresh bei relevanten WS-Ereignissen
useRealtimeUpdate((msg) => {
  if (msg.type === 'results') load()
})

onMounted(load)
</script>
```

---

## 5. Authentifizierung & Rollen

### JWT-Flow

```
Client                     Backend
  │  POST /api/auth/login     │
  │  { username, password }   │
  │ ─────────────────────────►│  bcrypt.verify(password, hash)
  │                           │  jwt.encode({ sub: user_id, role }, SECRET, HS256)
  │◄───────────────────────── │  { access_token: "eyJ…" }
  │                           │
  │  GET /api/events          │
  │  Authorization: Bearer …  │
  │ ─────────────────────────►│  jwt.decode(token)
  │                           │  SELECT * FROM Users WHERE id = sub AND is_active = 1
  │◄───────────────────────── │  200 OK
```

JWT-Secret: Umgebungsvariable `SECRET_KEY` (Fallback in `auth.py` für lokale Entwicklung).

### Neue Rolle anlegen

1. `schema.sql`: CHECK-Constraint in `Users.role` erweitern
2. `deps.py`: Neue `Annotated`-Typen für die Rolle ergänzen
3. `router/index.js`: Route mit der neuen Rolle in `meta.roles` + `roleHome` hinzufügen
4. `AppHeader.vue`: Eintrag in `allNav` mit `primary: true/false` und `roles`

**Verfügbare Rollen:** `admin` · `zeitnahme` · `nennung` · `schiedsrichter` · `marshal` · `viewer`

---

## 6. WebSocket-System

### Architektur

```
Browser-Clients (Zeitnahme, Livetiming, …)
    │  ws://host/ws
    │
    ├──► BroadcastManager._connections (set of WebSocket)
    │
Raspberry Pi / ELV LSU200
    │  ws://host/ws/timing
    │
    └──► main.py → timing_device_endpoint()
               → manager.broadcast(data)  → alle Browser-Clients
```

**`broadcast.py`** enthält den `BroadcastManager` als Singleton:
```python
from broadcast import manager
await manager.broadcast({"type": "results", "event_id": 1, "class_id": 3})
```

### Nachrichten-Typen

| `type` | Ausgelöst durch | Empfänger |
|---|---|---|
| `results` | Neues Ergebnis / Korrektur / Strafe | Zeitnahme, Livetiming, Sprecher |
| `notification` | Nennungsschluss-Announce, `/nachrichten` | Alle Browser-Clients |
| `timing_result` | Lichtschranke (RaPi oder ELV) | Zeitnahme (→ Zeitfeld) |
| `timing_device_heartbeat` | Lichtschranke | Zeitnahme (→ Status-Indikator) |
| `timing_device_status` | Connect/Disconnect eines Messgeräts | Zeitnahme |
| `marshal_penalty` | Streckenposten (`POST /api/marshal/report`) | Zeitnahme (→ Übernahme-Panel), Sprecher |

### Push-Benachrichtigung aus einem Router senden

```python
# In einem beliebigen Router-Endpoint:
from broadcast import manager

@router.post("/something", status_code=204)
async def do_something(background_tasks: BackgroundTasks, ...):
    # Wichtig: background_tasks — blockiert den Response nicht
    background_tasks.add_task(manager.broadcast, {
        "type": "notification",
        "message": "Etwas ist passiert",
        "level": "info",
    })
```

---

## 7. Datenbank & Migrationen

### Schema verwalten

Das Schema liegt in `schema.sql` (Projektroot). Es ist die **einzige Quelle der Wahrheit**.  
Beim Start von `init_db()` wird es vollständig angewendet:
- `CREATE TABLE IF NOT EXISTS` — sicher für bestehende DBs
- Views werden mit `DROP VIEW IF EXISTS` + `CREATE VIEW` neu erzeugt

### Neue Spalte hinzufügen

**Schritt 1:** `schema.sql` anpassen — Spalte im `CREATE TABLE` ergänzen:
```sql
CREATE TABLE IF NOT EXISTS Participants (
    ...
    new_column TEXT,   -- neu hinzugefügt
    ...
)
```

**Schritt 2:** Migration in `database.py` schreiben:
```python
def _migrate(conn):
    _migrate_participants(conn)
    _migrate_classes(conn)
    # ...
    _migrate_participants_new_column(conn)   # NEU

def _migrate_participants_new_column(conn):
    existing = {row[1] for row in conn.execute("PRAGMA table_info(Participants)")}
    if not existing or "new_column" in existing:
        return
    conn.execute("ALTER TABLE Participants ADD COLUMN new_column TEXT")
```

> SQLite kann mit `ALTER TABLE ADD COLUMN` nur am Ende anfügen.  
> Für UNIQUE-Constraint-Änderungen oder Umstrukturierungen: Tabelle via `_v2`-Copy recreaten (siehe `_migrate_participants_unique_per_class` in `database.py` als Vorlage).

### Neuen View hinzufügen

In `schema.sql`:
```sql
DROP VIEW IF EXISTS v_my_view;
CREATE VIEW v_my_view AS
    SELECT ...;
```

Views werden bei jedem Backend-Start neu erzeugt — kein Migrations-Code nötig.

---

## 8. Tests schreiben

### Setup

```bash
cd backend
pip install -r requirements-test.txt
pytest tests/ -v
```

### Test-Infrastruktur (`conftest.py`)

Jeder Test bekommt eine **eigene In-Memory-SQLite-DB** — keine gemeinsamen Daten zwischen Tests.

Verfügbare Fixtures:

| Fixture | Was es bereitstellt |
|---|---|
| `db` | SQLite-In-Memory-Verbindung, frisch initialisiert aus `schema.sql` |
| `client` | `TestClient` mit `get_db`-Override auf `db`, StaticFiles entfernt, `init_db` gemockt |
| `admin_headers` | JWT-Bearer-Header für Benutzer mit Rolle `admin` |
| `schiri_headers` | JWT-Bearer-Header für `schiedsrichter` |
| `zeitnahme_headers` | JWT-Bearer-Header für `zeitnahme` |
| `nennung_headers` | JWT-Bearer-Header für `nennung` |
| `event_id` | ID einer angelegten Veranstaltung |
| `class_id` | ID einer Klasse mit `run_status: "running"` (wichtig: laufend, damit Ergebnisse eingetragen werden dürfen) |
| `participant_id` | ID eines angelegten Teilnehmers |

### Typischer Backend-Test

```python
def test_create_result(client, event_id, participant_id, class_id, zeitnahme_headers):
    r = client.post(f"/api/events/{event_id}/results", json={
        "participant_id": participant_id,
        "class_id": class_id,
        "run_number": 1,
        "raw_time": 45.3,
        "status": "valid",
    }, headers=zeitnahme_headers)
    assert r.status_code == 201
    assert r.json()["raw_time"] == pytest.approx(45.3)
```

### Rollentest (403 prüfen)

```python
def test_create_result_forbidden_for_viewer(client, event_id, class_id, db):
    viewer_token = _make_user(db, "t_viewer", "viewer")
    headers = {"Authorization": f"Bearer {viewer_token}"}
    r = client.post(f"/api/events/{event_id}/results", json={...}, headers=headers)
    assert r.status_code == 403
```

### Direkte DB-Manipulation in Tests

```python
def test_suggest_class(client, event_id, class_id, db):
    # DB direkt beschreiben, ohne über die API zu gehen:
    db.execute("UPDATE Classes SET min_birth_year = 2010 WHERE id = ?", (class_id,))
    db.commit()
    r = client.get(f"/api/events/{event_id}/participants/suggest-class/2012")
    assert r.json()["class_id"] == class_id
```

### Frontend-Tests (Vitest)

```bash
cd frontend
npm test
```

Tests liegen in `src/__tests__/`. Aktuell getestet: `useNetworkStatus` und `useRealtimeUpdate`.  
Neue Composable-Tests analog aufbauen — jsdom + `@vue/test-utils` sind verfügbar.

---

## 9. Neues Feature implementieren – Schritt für Schritt

### Beispiel: Neue Ressource „Streckenposten"

#### Backend

**1. Schema erweitern** (`schema.sql`):
```sql
CREATE TABLE IF NOT EXISTS Marshals (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id    INTEGER NOT NULL REFERENCES Events(id) ON DELETE CASCADE,
    name        TEXT    NOT NULL,
    post        TEXT,
    created_at  TEXT    DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
```

**2. Pydantic-Schemas** (`schemas.py`):
```python
class MarshalCreate(BaseModel):
    event_id: Optional[int] = None  # gesetzt vom Router
    name: str
    post: Optional[str] = None

class MarshalResponse(MarshalCreate):
    id: int
    created_at: str
    model_config = {"from_attributes": True}
```

**3. Router** (`routers/marshals.py`):
```python
from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated
import sqlite3
from database import get_db
from deps import require_roles
from schemas import MarshalCreate, MarshalResponse

router = APIRouter(prefix="/events/{event_id}/marshals", tags=["marshals"])
AdminOnly = Annotated[sqlite3.Row, Depends(require_roles("admin"))]

@router.get("", response_model=list[MarshalResponse])
def list_marshals(event_id: int, db: Annotated[sqlite3.Connection, Depends(get_db)]):
    return [dict(r) for r in db.execute(
        "SELECT * FROM Marshals WHERE event_id = ?", (event_id,)
    ).fetchall()]

@router.post("", response_model=MarshalResponse, status_code=201)
def create_marshal(event_id: int, body: MarshalCreate,
                   db: Annotated[sqlite3.Connection, Depends(get_db)], _: AdminOnly):
    body.event_id = event_id
    cur = db.execute(
        "INSERT INTO Marshals (event_id, name, post) VALUES (?,?,?)",
        (event_id, body.name, body.post)
    )
    db.commit()
    return dict(db.execute("SELECT * FROM Marshals WHERE id = ?", (cur.lastrowid,)).fetchone())
```

**4. In `main.py` registrieren:**
```python
from routers import marshals
app.include_router(marshals.router, prefix="/api")
```

#### Frontend

**5. Neue View** (`src/views/MarshalsView.vue`):
```vue
<script setup>
import { ref, onMounted } from 'vue'
import api from '../api/client'
import { useEventStore } from '../stores/event'

const store = useEventStore()
const marshals = ref([])

async function load() {
  const { data } = await api.get(`/events/${store.activeEvent.id}/marshals`)
  marshals.value = data
}
onMounted(load)
</script>
```

**6. Route registrieren** (`router/index.js`):
```js
{ path: '/streckenposten', component: () => import('../views/MarshalsView.vue'),
  meta: { roles: ['admin'] } }
```

**7. Nav-Eintrag** (`AppHeader.vue`):
```js
{ to: '/streckenposten', label: 'Streckenposten', roles: ['admin'] },
```

---

## 10. CI/CD Pipeline

### GitHub Actions (`.github/workflows/ci.yml`)

Drei Jobs laufen bei jedem Push/PR auf `main`:

| Job | Was wird geprüft | Runtime |
|---|---|---|
| `backend-tests` | `pytest backend/tests/ -v` auf Python 3.11 | ~30 s |
| `frontend-tests` | `npm ci && npm test` (Vitest) auf Node 20 | ~20 s |
| `frontend-build` | `npm run build` (nach frontend-tests) | ~30 s |

### Voraussetzungen für grüne CI

- `backend/requirements.txt` und `backend/requirements-test.txt` aktuell halten
- `frontend/package-lock.json` muss synchron mit `package.json` sein (`npm install` lokal ausführen wenn neue Pakete hinzugefügt werden)
- Alle neuen Backend-Tests müssen mit In-Memory-SQLite (`db`-Fixture aus `conftest.py`) funktionieren — keine Abhängigkeit von `racecontrol.db`

### Häufige CI-Fehler und Ursachen

| Fehler | Ursache | Fix |
|---|---|---|
| `409 Conflict` bei Ergebnis-Test | `class_id`-Fixture hat `run_status: "planned"` statt `"running"` | `conftest.py` prüfen |
| `UNIQUE constraint failed: Users.username` | `init_db()` läuft in Tests und berührt `racecontrol.db` | `patch("main.init_db")` im `client`-Fixture |
| `405 Method Not Allowed` bei POST | StaticFiles-Route interceptiert Request | StaticFiles-Route im `client`-Fixture entfernen |
| `npm ci` schlägt fehl | `package-lock.json` out of sync | `npm install` lokal ausführen, Lock-File committen |
| `no such column: xyz` | Spalte in `schema.sql` ergänzt aber Migration vergessen | Migration in `database.py` hinzufügen |

---

## 11. Coding-Konventionen

### Backend

- Alle Routen haben explizite `response_model`-Typen
- Path-Parameter in Pydantic-Schemas immer `Optional[int] = None` (werden nach Validierung gesetzt)
- Fehler immer als `raise HTTPException(status_code, "Nachricht auf Deutsch")`
- Broadcasts immer über `background_tasks.add_task(manager.broadcast, {...})` — nie `await` im Handler (blockiert Response)
- Keine direkten SQL-Strings in `main.py` — nur in Routers und `database.py`
- SQLite-Rows mit `dict(row)` in dicts umwandeln bevor sie zurückgegeben werden

### Frontend

- Composition API (`<script setup>`) durchgehend — keine Options API
- Reactive State: `ref()` für einzelne Werte, `reactive()` für Objekte mit vielen Keys
- API-Calls immer über `api` (Axios-Client) — kein nacktes `fetch`
- Kein globaler State außerhalb von Pinia (`auth.js` und `event.js`)
- Tailwind-Klassen direkt im Template — kein separates CSS außer für `scoped`-Ausnahmen
- Einheitliche Button-Klassen: `btn-primary`, `btn-secondary` aus `main.css`/Tailwind-Konfiguration
- WebSocket-Listener immer über `useRealtimeUpdate` — nie manuell `new WebSocket()`

### Versionierung

- Semantic Versioning: `MAJOR.MINOR.PATCH`
- Changelog: `changelog.txt` (UTF-8) — normales Lesen/Schreiben:
  ```python
  import pathlib
  p = pathlib.Path("changelog.txt")
  text = p.read_text(encoding="utf-8")
  idx = text.find("[0.")
  p.write_text(text[:idx] + new_entry + text[idx:], encoding="utf-8")
  ```
- `README.md` ist UTF-16 LE (mit BOM `ÿþ`) — per Python mit `raw.decode('utf-16')` lesen,
  `b'ÿþ' + text.encode('utf-16-le')` schreiben

### Datenbankzugriff

- Alle Queries parametrisiert: `db.execute("... WHERE id = ?", (id,))` — niemals f-Strings mit User-Input
- `db.commit()` nach jedem schreibenden Zugriff
- Views nie direkt schreiben — nur lesen
- `is_exhibition`-Flag in `Classes`: Exhibition-Klassen umgehen den `_require_class_running`-Check

---

## Schnellreferenz: Wichtige Dateien

| Datei | Wofür |
|---|---|
| `schema.sql` | Datenbankstruktur ändern |
| `backend/database.py` | Migration für bestehende DBs hinzufügen |
| `backend/schemas.py` | Request/Response-Typen definieren |
| `backend/deps.py` | Neue Rollenprüfung definieren |
| `backend/broadcast.py` | WebSocket-Broadcast-Logik |
| `backend/tests/conftest.py` | Test-Fixtures ändern oder ergänzen |
| `frontend/src/router/index.js` | Neue Route + Rollenschutz |
| `frontend/src/components/AppHeader.vue` | Nav-Eintrag für neue Seite |
| `frontend/src/stores/auth.js` | Auth-State, Rolle, Login/Logout |
| `frontend/src/stores/event.js` | Globale Veranstaltungsdaten |
| `frontend/src/api/client.js` | Axios-Basis-URL, JWT-Header, 401-Handler |
| `frontend/vite.config.js` | Dev-Proxy, PWA-Manifest, Build-Konfiguration |
| `.github/workflows/ci.yml` | CI/CD anpassen |
