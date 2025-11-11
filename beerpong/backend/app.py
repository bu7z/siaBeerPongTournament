from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit
import os
from datetime import datetime

app = Flask(__name__)
CORS(app, origins="*")

# ----------------------------
# Config
# ----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "tournament.db")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "change-me"  # für socketio sessions

db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# ----------------------------
# Models
# ----------------------------

class Tournament(db.Model):
    __tablename__ = "tournaments"
    id = db.Column(db.Integer, primary_key=True)
    mode = db.Column(db.String(20), default="groups")  # groups | quarter | round16
    group_count = db.Column(db.Integer, default=4)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Team(db.Model):
    __tablename__ = "teams"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    group_name = db.Column(db.String(50), nullable=True)  # z.B. "Gruppe A"

class GroupMatch(db.Model):
    __tablename__ = "group_matches"
    id = db.Column(db.Integer, primary_key=True)
    group_name = db.Column(db.String(50), nullable=False)
    team1 = db.Column(db.String(120), nullable=False)
    team2 = db.Column(db.String(120), nullable=False)
    winner = db.Column(db.String(120), nullable=True)
    order_index = db.Column(db.Integer, nullable=False, default=0)  # für Reihenfolge

# optional: Tiebreak extra speichern
class Tiebreak(db.Model):
    __tablename__ = "tiebreaks"
    id = db.Column(db.Integer, primary_key=True)
    group_name = db.Column(db.String(50), nullable=False)
    mode = db.Column(db.String(20), nullable=False)  # 'mini' | 'rage'
    payload = db.Column(db.Text, nullable=True)  # JSON als string
    resolved = db.Column(db.Boolean, default=False)

# einmalig anlegen
with app.app_context():
    db.create_all()
    # falls kein Turnier existiert → Default
    if not Tournament.query.first():
        db.session.add(Tournament(mode="groups", group_count=4))
        db.session.commit()

# ----------------------------
# Helper
# ----------------------------

def current_tournament():
    return Tournament.query.first()

def round_robin(team_names):
    matches = []
    order = 0
    for i in range(len(team_names)):
        for j in range(i + 1, len(team_names)):
            matches.append({
                "team1": team_names[i],
                "team2": team_names[j],
                "order_index": order
            })
            order += 1
    return matches

# ----------------------------
# API: Teams
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
    # broadcast neue Liste
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
# API: Tournament
# ----------------------------

@app.get("/tournament")
def get_tournament():
    t = current_tournament()
    return jsonify({"mode": t.mode, "groupCount": t.group_count, "id": t.id})

@app.post("/tournament")
def update_tournament():
    data = request.json or {}
    t = current_tournament()
    if "mode" in data:
        t.mode = data["mode"]
    if "groupCount" in data:
        t.group_count = int(data["groupCount"])
    db.session.commit()
    socketio.emit("tournament_updated", {"mode": t.mode, "groupCount": t.group_count}, broadcast=True)
    return jsonify({"mode": t.mode, "groupCount": t.group_count})

# ----------------------------
# API: Gruppen generieren
# ----------------------------

@app.post("/generate-groups")
def generate_groups():
    t = current_tournament()
    group_count = t.group_count or 4
    letters = ["A","B","C","D","E","F","G","H"]
    group_names = [f"Gruppe {letters[i] if i < len(letters) else i+1}" for i in range(group_count)]

    teams = Team.query.order_by(Team.id).all()

    # alte Matches löschen
    GroupMatch.query.delete()
    db.session.commit()

    # Teams auf Gruppen verteilen
    for idx, team in enumerate(teams):
        gname = group_names[idx % group_count]
        team.group_name = gname
    db.session.commit()

    # neue Matches erzeugen
    for gname in group_names:
      names = [t.name for t in teams if t.group_name == gname]
      rr = round_robin(names)
      for m in rr:
          gm = GroupMatch(
              group_name=gname,
              team1=m["team1"],
              team2=m["team2"],
              order_index=m["order_index"],
              winner=None
          )
          db.session.add(gm)
    db.session.commit()

    # broadcast
    socketio.emit("group_matches_updated", get_group_matches_payload(), broadcast=True)

    return jsonify({"status": "groups-assigned", "groups": get_group_matches_payload()})

def get_group_matches_payload():
    all_matches = GroupMatch.query.order_by(GroupMatch.group_name, GroupMatch.order_index).all()
    out = {}
    for m in all_matches:
        out.setdefault(m.group_name, []).append({
            "id": m.id,
            "team1": m.team1,
            "team2": m.team2,
            "winner": m.winner
        })
    return out

@app.get("/group-matches")
def get_group_matches():
    return jsonify(get_group_matches_payload())

# ----------------------------
# API: Sieger setzen
# ----------------------------

@app.post("/group-matches/<group_name>/<int:match_id>/winner")
def set_match_winner(group_name, match_id):
    data = request.json or {}
    winner = data.get("winner")
    match = GroupMatch.query.filter_by(id=match_id, group_name=group_name).first()
    if not match:
        return jsonify({"error": "match not found"}), 404

    match.winner = winner
    db.session.commit()

    # allen Clients mitteilen
    socketio.emit("match_updated", {
        "group": group_name,
        "match": {
            "id": match.id,
            "team1": match.team1,
            "team2": match.team2,
            "winner": match.winner
        }
    }, broadcast=True)

    return jsonify({"status": "ok"})

# ----------------------------
# Health
# ----------------------------

@app.get("/health")
def health():
    return jsonify({"ok": True})

# ----------------------------
# Socket.IO einfache Events
# ----------------------------

@socketio.on("connect")
def handle_connect():
    emit("hello", {"msg": "connected to tournament backend"})

# ----------------------------
# Start
# ----------------------------
if __name__ == "__main__":
    # wichtig für docker + socketio
    socketio.run(app, host="0.0.0.0", port=5000)
