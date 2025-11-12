from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit
import os
from datetime import datetime
import math
import random
from collections import defaultdict

app = Flask(__name__)
CORS(app, origins="*")

# ----------------------------
# Config
# ----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "tournament.db")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "change-me"

db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# ----------------------------
# Models
# ----------------------------

class Tournament(db.Model):
    __tablename__ = "tournaments"
    id = db.Column(db.Integer, primary_key=True)
    mode = db.Column(db.String(20), default="groups")
    participant_count = db.Column(db.Integer, default=8)
    cups_per_game = db.Column(db.Integer, default=6)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Team(db.Model):
    __tablename__ = "teams"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    group_name = db.Column(db.String(50), nullable=True)

class GroupMatch(db.Model):
    __tablename__ = "group_matches"
    id = db.Column(db.Integer, primary_key=True)
    group_name = db.Column(db.String(50), nullable=False)
    team1 = db.Column(db.String(120), nullable=False)
    team2 = db.Column(db.String(120), nullable=False)
    winner = db.Column(db.String(120), nullable=True)
    cups_team1 = db.Column(db.Integer, nullable=True)
    cups_team2 = db.Column(db.Integer, nullable=True)
    order_index = db.Column(db.Integer, nullable=False, default=0)

class Tiebreak(db.Model):
    __tablename__ = "tiebreaks"
    id = db.Column(db.Integer, primary_key=True)
    group_name = db.Column(db.String(50), nullable=False)
    mode = db.Column(db.String(20), nullable=False)
    payload = db.Column(db.Text, nullable=True)
    resolved = db.Column(db.Boolean, default=False)

# ----------------------------
# Init
# ----------------------------
with app.app_context():
    db.create_all()
    if not Tournament.query.first():
        db.session.add(Tournament(mode="groups", participant_count=8, cups_per_game=6))
        db.session.commit()

# ----------------------------
# Helper (allgemein)
# ----------------------------

def current_tournament():
    return Tournament.query.first()

def letters():
    return ["A","B","C","D","E","F","G","H","I","J","K","L","M","N","O","P"]

POW2_KO = [4, 8, 16, 32, 64, 128]

def choose_ko_size(qualified: int) -> int:
    for k in POW2_KO:
        if k >= qualified:
            return k
    return qualified

def balanced_sizes(n: int, groups: int) -> list:
    base = n // groups
    rem = n % groups
    return [base + (1 if i < rem else 0) for i in range(groups)]

def group_count_by_band(n: int) -> int:
    """
    Band-Logik:
      - ≤4  -> 1 Gruppe
      - ≤8  -> 2 Gruppen
      - ≤11 -> 3 Gruppen
      - ≤16 -> 4 Gruppen
      - ≥17 -> zielt auf 4–5 pro Gruppe
    """
    if n <= 4:  return 1
    if n <= 8:  return 2
    if n <= 11: return 3
    if n <= 16: return 4
    # 17+: 4–5 pro Gruppe anpeilen
    return max(4, round(n / 4.5))

# ----------------------------
# Ranking/Seeding Hilfen
# ----------------------------

def cups_diff(row):
    # falls cupsDiff schon mitkommt, nutze ihn; sonst berechne aus B+ - B-
    if row.get("cupsDiff") is not None:
        return int(row.get("cupsDiff"))
    return int(row.get("cupsFor", 0)) - int(row.get("cupsAgainst", 0))

def build_h2h_lookup(group_matches):
    h2h = {}
    for m in group_matches or []:
        g = m.get("group") or m.get("group_name")
        t1, t2, w = m.get("team1"), m.get("team2"), m.get("winner")
        if g and t1 and t2:
            h2h[(g, t1, t2)] = w
            h2h[(g, t2, t1)] = w
    return h2h

def h2h_winner(h2h, group, a_name, b_name):
    return h2h.get((group, a_name, b_name))

def rank_group_rows(rows, group_name, h2h):
    """
    Gruppenintern für 1./2./3./4.:
    points desc -> cupsDiff desc -> H2H -> cupsFor desc -> name
    """
    def key_func(r):
        return (
            -int(r.get("points", 0)),
            -int(cups_diff(r)),
            -int(r.get("cupsFor", 0)),
            r.get("name", "")
        )
    sorted_rows = sorted(rows, key=key_func)

    # H2H nur bei exaktem Gleichstand points & diff & cupsFor
    i = 0
    while i < len(sorted_rows) - 1:
        a, b = sorted_rows[i], sorted_rows[i+1]
        if (int(a.get("points", 0)) == int(b.get("points", 0)) and
            cups_diff(a) == cups_diff(b) and
            int(a.get("cupsFor", 0)) == int(b.get("cupsFor", 0))):
            w = h2h_winner(h2h, group_name, a.get("name"), b.get("name"))
            if w == b.get("name"):
                sorted_rows[i], sorted_rows[i+1] = b, a
        i += 1
    return sorted_rows

# >>> Play-In Ranking (deine Policy)
def playin_key(c):
    """
    Globales Ranking NUR für Play-In-Kandidaten (3./4. Plätze):
    1) Becher-Differenz (cupsDiff) DESC
    2) Becher+ (cupsFor) DESC
    3) Punkte DESC
    """
    return (-int(c["cupsDiff"]), -int(c["cupsFor"]), -int(c["points"]))

def same_playin_strength(a, b):
    return (a["cupsDiff"] == b["cupsDiff"] and
            a["cupsFor"] == b["cupsFor"] and
            a["points"] == b["points"])

def prefer_inter_group_pairs(cands_sorted):
    """
    Paare strongest vs weakest mit inter-group-Prio.
    Input: cands_sorted (strongest first)
    """
    pairs = []
    i, j = 0, len(cands_sorted) - 1
    while i < j:
        a = cands_sorted[i]
        # suche von hinten Partner aus anderer Gruppe
        k = j
        partner_idx = None
        while k > i:
            if cands_sorted[k]["group"] != a["group"]:
                partner_idx = k
                break
            k -= 1
        if partner_idx is None:
            partner_idx = j
        b = cands_sorted[partner_idx]
        pairs.append((a, b))
        i += 1
        j = partner_idx - 1
    return pairs

# ----------------------------
# „Klassischer“ Planer (Band-basiert)
# ----------------------------

def compute_optimal_groups_and_ko(n: int) -> dict:
    if n <= 0:
        return {"error": "Ungültige Teilnehmerzahl"}

    g = group_count_by_band(n)
    sizes = balanced_sizes(n, g)

    # EXPLIZITE Sonderbehandlung: genau 12 Teilnehmer -> 4 Gruppen à 3 Teams
    if n == 12:
        g = 4
        sizes = [3, 3, 3, 3]

    # Für 17+ sicherstellen: max. 5 pro Gruppe
    if n >= 17:
        while max(sizes) > 5:
            g += 1
            sizes = balanced_sizes(n, g)

    group_names = [f"Gruppe {letters()[i]}" for i in range(g)]
    groups = [{"name": name, "size": size} for name, size in zip(group_names, sizes)]

    qualified = sum(2 if s >= 2 else 0 for s in sizes)  # Top-2 je Gruppe
    # Ziel-KO Größen: 4/8/16/32/...
    ko_size = choose_ko_size(qualified)
    slots_needed = max(0, ko_size - qualified)

    # Kandidatenlabels (3./4.) – generisch
    thirds, fourths = [], []
    for name, size in zip(group_names, sizes):
        if size >= 3:
            thirds.append({"group": name, "position": 3, "label": f"3. {name}"})
        if size >= 4:
            fourths.append({"group": name, "position": 4, "label": f"4. {name}"})
    candidates = thirds + fourths

    return {
        "groups": groups,
        "ko_size": ko_size,
        "qualified_per_group": 2,
        "playin_needed": slots_needed > 0,
        "playin_slots_needed": slots_needed,
        "playin_candidates": candidates
    }

def generate_ko_bracket(ko_size, qualified_teams):
    bracket = {"size": ko_size, "rounds": [], "matches": []}
    if ko_size == 4:
        bracket["rounds"] = [{"name": "Halbfinale", "matches": 2}, {"name": "Finale", "matches": 1}]
        bracket["matches"] = [
            {"round": 0, "match": 1, "team1": "Sieger Gruppe A", "team2": "Zweiter Gruppe B"},
            {"round": 0, "match": 2, "team1": "Sieger Gruppe B", "team2": "Zweiter Gruppe A"},
            {"round": 1, "match": 1, "team1": "Sieger HF 1", "team2": "Sieger HF 2"}
        ]
    elif ko_size == 8:
        bracket["rounds"] = [
            {"name": "Viertelfinale", "matches": 4},
            {"name": "Halbfinale", "matches": 2},
            {"name": "Finale", "matches": 1}
        ]
        bracket["matches"] = [
            {"round": 0, "match": 1, "team1": "Sieger Gruppe A", "team2": "Zweiter Gruppe B"},
            {"round": 0, "match": 2, "team1": "Sieger Gruppe C", "team2": "Zweiter Gruppe D"},
            {"round": 0, "match": 3, "team1": "Sieger Gruppe B", "team2": "Zweiter Gruppe A"},
            {"round": 0, "match": 4, "team1": "Sieger Gruppe D", "team2": "Zweiter Gruppe C"},
            {"round": 1, "match": 1, "team1": "Sieger VF 1", "team2": "Sieger VF 2"},
            {"round": 1, "match": 2, "team1": "Sieger VF 3", "team2": "Sieger VF 4"},
            {"round": 2, "match": 1, "team1": "Sieger HF 1", "team2": "Sieger HF 2"}
        ]
    return bracket

# ----------------------------
# API: Turnierplan (klassisch)
# ----------------------------

@app.post("/compute-tournament-plan")
def compute_plan_endpoint():
    data = request.json or {}
    n = int(data.get("participantCount") or 0)
    if n <= 0:
        t = current_tournament()
        n = t.participant_count
    plan = compute_optimal_groups_and_ko(n)
    plan["ko_bracket"] = generate_ko_bracket(plan["ko_size"], [])
    plan["playin_needed"] = bool(plan.get("playin_slots_needed", 0) > 0)
    return jsonify(plan)

# ----------------------------
# API: Play-In aus echten Tabellen (deine Policy)
# ----------------------------

@app.post("/compute-playin-from-tables")
def compute_playin_from_tables():
    """
    Erwartet:
    {
      "groups": {
        "Gruppe A": [ { "name": "...", "points": 6, "wins": 3, "losses": 0,
                        "cupsFor": 18, "cupsAgainst": 10, "cupsDiff": 8 }, ... ],
        "Gruppe B": [ ... ],
        ...
      }
    }
    """
    data = request.json or {}
    group_tables = data.get("groups", {})

    # Slots bestimmen (aus Struktur)
    t = current_tournament()
    base_plan = compute_optimal_groups_and_ko(t.participant_count)
    slots_needed = int(base_plan.get("playin_slots_needed", 0))

    # Kein Play-In nötig? → leer zurück
    if slots_needed <= 0:
        return jsonify({
            "playin_needed": False,
            "direct_qualified": [],
            "tie_cluster": [],
            "playin_matches": [],
            "rage_cage_groups": [],
            "policy_notes": ["Kein Play-In erforderlich (SlotsNeeded=0)."]
        })

    # Kandidaten sammeln: 3. + 4. jeder Gruppe
    # Vorher Gruppen intern ranken (points → diff → H2H → cupsFor)
    ranked = {}
    h2h = {}
    for gname, rows in group_tables.items():
        ranked[gname] = rank_group_rows(rows, gname, h2h)

    candidates = []
    for gname, rows in ranked.items():
        if len(rows) >= 3:
            r3 = rows[2]
            candidates.append({
                "group": gname,
                "position": 3,
                "team": r3["name"],
                "points": int(r3.get("points", 0)),
                "cupsFor": int(r3.get("cupsFor", 0)),
                "cupsAgainst": int(r3.get("cupsAgainst", 0)),
                "cupsDiff": cups_diff(r3)
            })
        if len(rows) >= 4:
            r4 = rows[3]
            candidates.append({
                "group": gname,
                "position": 4,
                "team": r4["name"],
                "points": int(r4.get("points", 0)),
                "cupsFor": int(r4.get("cupsFor", 0)),
                "cupsAgainst": int(r4.get("cupsAgainst", 0)),
                "cupsDiff": cups_diff(r4)
            })

    # Sortierung nach Policy: diff ↓, B+ ↓, points ↓
    candidates.sort(key=playin_key)

    C = len(candidates)
    if C == 0:
        return jsonify({
            "playin_needed": False,
            "direct_qualified": [],
            "tie_cluster": [],
            "playin_matches": [],
            "rage_cage_groups": [],
            "policy_notes": ["Keine Play-In-Kandidaten vorhanden."]
        })

    if C <= slots_needed:
        return jsonify({
            "playin_needed": False,
            "direct_qualified": [f"{c['team']} ({c['position']}. {c['group']})" for c in candidates],
            "tie_cluster": [],
            "playin_matches": [],
            "rage_cage_groups": [],
            "policy_notes": ["Kandidaten ≤ benötigte Plätze → alle qualifiziert, kein Play-In notwendig."]
        })

    # Cut-Off ermitteln
    boundary_idx = slots_needed - 1  # 0-basiert
    boundary = candidates[boundary_idx]

    def better(a, b):
        return playin_key(a) < playin_key(b)

    strict_better = [c for c in candidates if better(c, boundary)]
    direct = strict_better[:]

    eq_key = playin_key(boundary)
    tie_cluster = [c for c in candidates if playin_key(c) == eq_key]
    remaining_slots = slots_needed - len(strict_better)

    policy_notes = [
        "Play-In Ranking: Becher-Differenz → Becher+ → Punkte (alle absteigend).",
        "Nur Gleichstand am Cut-Off erzeugt Play-In; klare Rankings qualifizieren direkt."
    ]

    in_top = sum(1 for c in candidates if playin_key(c) == eq_key and candidates.index(c) <= boundary_idx)
    if in_top == len(tie_cluster):
        direct += [c for c in tie_cluster if c not in direct]
        return jsonify({
            "playin_needed": False,
            "direct_qualified": [f"{c['team']} ({c['position']}. {c['group']})" for c in direct],
            "tie_cluster": [],
            "playin_matches": [],
            "rage_cage_groups": [],
            "policy_notes": policy_notes + ["Tie-Cluster liegt vollständig innerhalb der Top-Plätze → kein Play-In."]
        })

    out_top = sum(1 for c in candidates if playin_key(c) == eq_key and candidates.index(c) > boundary_idx)
    if out_top == len(tie_cluster):
        return jsonify({
            "playin_needed": False,
            "direct_qualified": [f"{c['team']} ({c['position']}. {c['group']})" for c in direct],
            "tie_cluster": [],
            "playin_matches": [],
            "rage_cage_groups": [],
            "policy_notes": policy_notes + ["Tie-Cluster liegt vollständig unterhalb des Cut-Off → kein Play-In."]
        })

    cluster_size = len(tie_cluster)
    eliminations = cluster_size - remaining_slots

    if cluster_size == 3 and eliminations == 1:
        return jsonify({
            "playin_needed": True,
            "direct_qualified": [f"{c['team']} ({c['position']}. {c['group']})" for c in direct],
            "tie_cluster": [f"{c['team']} ({c['position']}. {c['group']})" for c in tie_cluster],
            "playin_matches": [],
            "rage_cage_groups": [{
                "teams": [f"{c['team']} ({c['position']}. {c['group']})" for c in tie_cluster],
                "note": "Exakter 3er-Gleichstand am Cut-Off → Rage-Cage bestimmt den einen Verlierer."
            }],
            "policy_notes": policy_notes + ["3er-Tie am Cut-Off → Rage-Cage."]
        })

    cluster_sorted = sorted(tie_cluster, key=playin_key)  # strongest first
    matches = []
    pairs = prefer_inter_group_pairs(cluster_sorted)
    pairs = pairs[:eliminations]

    mid = 1
    for a, b in pairs:
        matches.append({
            "match_id": mid,
            "team1": f"{a['team']} ({a['position']}. {a['group']})",
            "team2": f"{b['team']} ({b['position']}. {b['group']})",
            "type": "playin_elimination"
        })
        mid += 1

    if len(matches) < eliminations:
        policy_notes.append("Cluster-Edge-Case: zusätzliche Mini-Runde erforderlich (Front-End kann nachfassen).")

    return jsonify({
        "playin_needed": True,
        "direct_qualified": [f"{c['team']} ({c['position']}. {c['group']})" for c in direct],
        "tie_cluster": [f"{c['team']} ({c['position']}. {c['group']})" for c in tie_cluster],
        "playin_matches": matches,
        "rage_cage_groups": [],
        "policy_notes": policy_notes
    })

# ----------------------------
# Teams API
# ----------------------------

@app.get("/teams")
def get_teams():
    teams = Team.query.order_by(Team.id).all()
    return jsonify([{"id": t.id, "name": t.name, "group": t.group_name} for t in teams])

@app.post("/teams")
def add_team():
    data = request.json or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "Name required"}), 400
    team = Team(name=name, group_name=data.get("group"))
    db.session.add(team)
    db.session.commit()
    socketio.emit("teams_updated", {"teams": [{"id": team.id, "name": team.name, "group": team.group_name}]}, broadcast=True)
    return jsonify({"id": team.id, "name": team.name, "group": team.group_name}), 201

@app.delete("/teams/<int:team_id>")
def delete_team(team_id):
    t = Team.query.get(team_id)
    if not t:
        return jsonify({"error": "not found"}), 404
    db.session.delete(t)
    db.session.commit()
    socketio.emit("teams_deleted", {"id": team_id}, broadcast=True)
    return jsonify({"status": "deleted"})

# ----------------------------
# Tournament API
# ----------------------------

@app.get("/tournament")
def get_tournament():
    t = current_tournament()
    return jsonify({
        "mode": t.mode,
        "participantCount": t.participant_count,
        "cupsPerGame": t.cups_per_game,
        "id": t.id
    })

@app.post("/tournament")
def update_tournament():
    data = request.json or {}
    t = current_tournament()
    if "mode" in data:
        t.mode = data["mode"]
    if "participantCount" in data:
        t.participant_count = int(data["participantCount"])
    if "cupsPerGame" in data:
        t.cups_per_game = int(data["cupsPerGame"])
    db.session.commit()
    socketio.emit("tournament_updated", {
        "mode": t.mode,
        "participantCount": t.participant_count,
        "cupsPerGame": t.cups_per_game
    }, broadcast=True)
    return jsonify({
        "mode": t.mode,
        "participantCount": t.participant_count,
        "cupsPerGame": t.cups_per_game
    })

# ----------------------------
# Gruppen generieren
# ----------------------------

def round_robin(team_names):
    matches = []
    order = 0
    for i in range(len(team_names)):
        for j in range(i + 1, len(team_names)):
            matches.append({"team1": team_names[i], "team2": team_names[j], "order_index": order})
            order += 1
    return matches

@app.post("/generate-groups")
def generate_groups():
    t = current_tournament()
    plan = compute_optimal_groups_and_ko(t.participant_count)
    group_names = [g["name"] for g in plan["groups"]]
    group_sizes = [g["size"] for g in plan["groups"]]

    teams = Team.query.order_by(Team.id).all()

    GroupMatch.query.delete()
    db.session.commit()

    shuffled = teams.copy()
    random.shuffle(shuffled)

    idx = 0
    for gname, gsize in zip(group_names, group_sizes):
        for _ in range(gsize):
            if idx < len(shuffled):
                shuffled[idx].group_name = gname
                idx += 1
    db.session.commit()

    for gname in group_names:
        names = [t.name for t in teams if t.group_name == gname]
        if len(names) >= 2:
            rr = round_robin(names)
            for m in rr:
                db.session.add(GroupMatch(
                    group_name=gname,
                    team1=m["team1"],
                    team2=m["team2"],
                    order_index=m["order_index"],
                    winner=None,
                    cups_team1=None,
                    cups_team2=None
                ))
    db.session.commit()

    socketio.emit("group_matches_updated", get_group_matches_payload(), broadcast=True)

    return jsonify({
        "status": "groups-assigned",
        "groups": get_group_matches_payload(),
        "groupCount": len(group_names),
        "groupSizes": group_sizes,
        "groupNames": group_names,
        "tournament_plan": plan
    })

def get_group_matches_payload():
    all_matches = GroupMatch.query.order_by(GroupMatch.group_name, GroupMatch.order_index).all()
    out = {}
    for m in all_matches:
        out.setdefault(m.group_name, []).append({
            "id": m.id,
            "team1": m.team1,
            "team2": m.team2,
            "winner": m.winner,
            "cups_team1": m.cups_team1,
            "cups_team2": m.cups_team2
        })
    return out

@app.get("/group-matches")
def get_group_matches():
    return jsonify(get_group_matches_payload())

# ----------------------------
# Match Ergebnis
# ----------------------------

@app.post("/group-matches/<group_name>/<int:match_id>/result")
def set_match_result(group_name, match_id):
    data = request.json or {}
    winner = data.get("winner")
    cups_team1 = data.get("cups_team1")
    cups_team2 = data.get("cups_team2")

    match = GroupMatch.query.filter_by(id=match_id, group_name=group_name).first()
    if not match:
        return jsonify({"error": "match not found"}), 404

    match.winner = winner
    match.cups_team1 = cups_team1
    match.cups_team2 = cups_team2
    db.session.commit()

    socketio.emit("match_updated", {
        "group": group_name,
        "match": {
            "id": match.id,
            "team1": match.team1,
            "team2": match.team2,
            "winner": match.winner,
            "cups_team1": match.cups_team1,
            "cups_team2": match.cups_team2
        }
    }, broadcast=True)

    return jsonify({"status": "ok"})

# ----------------------------
# Health & Socket.IO
# ----------------------------

@app.get("/health")
def health():
    return jsonify({"ok": True})

@socketio.on("connect")
def handle_connect():
    emit("hello", {"msg": "connected to tournament backend"})

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
