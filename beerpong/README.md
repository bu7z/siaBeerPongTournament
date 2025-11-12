# SIA BeerPong Tournament

Kurzprojekt: Web‑App zur Organisation kleiner Beer‑Pong‑Turniere. Dieses Repository enthält ein einfaches Fullstack‑Setup mit einem Flask‑Backend (SQLite + Socket.IO) und einer Vue 3 / Vite‑Frontend‑App. Ziel ist, Teams zu verwalten, Gruppen zu generieren und Spielstände/Matches in Echtzeit zu verteilen.

## Schnellstart (lokal, Docker)

Voraussetzung: Docker und docker-compose installiert.

1. Im Projekt-Root (dort, wo `docker-compose.yml` liegt) ausführen:

```bash
docker-compose up --build
```

2. Frontend wird auf Port 5173, Backend auf Port 5000 verfügbar sein (Standard laut `docker-compose.yml`).

Alternativ lokal entwickeln (ohne Docker):

Backend:
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Frontend:
```bash
cd frontend
npm install
npm run dev
```

## Ordnerübersicht

`backend/`
- Zweck: Flask‑API, SQLite‑Datenbank (`tournament.db` im Backend‑Ordner), Socket.IO für Echtzeit‑Updates.
- Hauptdatei: `app.py` (Modelle, API‑Routen, Socket.IO Events).
- Wichtige Punkte:
  - Konfiguration derzeit in `app.py` (z.B. `SECRET_KEY`, DB‑Pfad). Für Produktion: Umziehen in Umgebungsvariablen und sichere Secrets verwenden.
  - Datenbank: SQLite (gut für Demo/Dev, limitiert bei parallelen Schreibzugriffen). Für produktive Nutzung DB migrieren (Postgres, MySQL) und Migrationstool (z. B. Alembic) einführen.

`frontend/`
- Zweck: Vue 3 + Vite App (UI, Socket.IO Client). Stellt die Turnierverwaltung, Gruppenansicht und K.O.-Bracket dar.
- Wichtige Dateien/Ordner:
  - `index.html`, `src/` (App.vue, main.js, style.css)
  - `src/components/`: UI‑Komponenten (z. B. `KnockoutBracket.vue`, `GroupsView.vue`, `TournamentWizard.vue`).
  - `public/`: statische Assets.
  - `package.json`: enthält Abhängigkeiten (Vue, bootstrap, socket.io-client).

`docker-compose.yml`
- Orchestriert Backend und Frontend als Services. Stellt Ports 5000 (Backend) und 5173 (Frontend) nach außen bereit. Nutzt Volumes für Live‑Code‑Änderungen.

Sonstiges
- `backend/Dockerfile` / `frontend/Dockerfile`: Docker‑Definitionen für beide Services.
- `backend/requirements.txt`: Python‑Abhängigkeiten.

## Hinweise für Entwickler

- API‑Basis: Backend bietet REST Endpunkte (z. B. `/teams`, `/tournament`, `/generate-groups`, `/group-matches`) und Socket.IO Broadcasts (`teams_updated`, `group_matches_updated`, `match_updated`).
- Bei Änderungen an DB‑Modellen: Backup der `tournament.db` anlegen oder Migration einführen.
- Sicherheit: CORS ist aktuell offen (`origins="*"`). Für Deployment auf eine Domain einschränken.

## Nächste sinnvolle Schritte

- Tests hinzufügen (Backend: pytest + Test‑DB; Frontend: vitest oder jest).
- Konfiguration via Umgebungsvariablen (z. B. `FLASK_ENV`, `SECRET_KEY`, `DATABASE_URL`).
- DB‑Migration (z. B. Alembic) und Entkopplung vom SQLite‑Dateipfad.
- Endpoint‑Dokumentation (kurz in README oder OpenAPI/Swagger).

---

Weitere Details zu einzelnen Komponenten und ein kurzer technischer Rundown des Backends folgen im nächsten Abschnitt.
