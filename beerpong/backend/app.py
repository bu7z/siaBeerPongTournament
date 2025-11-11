from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

teams = []
matches = []

@app.get("/teams")
def get_teams():
    return jsonify(teams)

@app.post("/teams")
def add_team():
    data = request.json
    # hier evtl. validieren auf max 16
    teams.append({
        "id": len(teams) + 1,
        "name": data["name"],
        "group": data.get("group")
    })
    return jsonify({"status": "ok"}), 201

@app.get("/matches")
def get_matches():
    return jsonify(matches)

@app.post("/generate-groups")
def generate_groups():
    # sehr simpel: teams round-robin in 4 Gruppen verteilen
    groups = ["A", "B", "C", "D"]
    for i, t in enumerate(teams):
        t["group"] = groups[i % 4]
    # hier könntest du auch gleich die Gruppenspiele erstellen
    return jsonify({"status": "groups-assigned"})
