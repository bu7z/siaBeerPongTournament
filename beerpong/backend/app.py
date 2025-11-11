from flask import Flask, request, jsonify, abort
from flask_cors import CORS
import os
import json

app = Flask(__name__)
CORS(app)

# persistenter Speicher (einfach JSON-file)
store_path = os.path.join(os.path.dirname(__file__), "store.json")
_default_store = {
    "teams": [],  # list of {id, name, group}
    "tournament": {"mode": "groups", "groupCount": 4},
    "group_matches": {}  # { "Gruppe A": [ {team1, team2, winner}, ... ] }
}

def load_store():
    if os.path.exists(store_path):
        try:
            with open(store_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return dict(_default_store)
    return dict(_default_store)

def save_store(s):
    with open(store_path, "w", encoding="utf-8") as f:
        json.dump(s, f, ensure_ascii=False, indent=2)

_store = load_store()

def next_team_id():
    if not _store["teams"]:
        return 1
    return max(t["id"] for t in _store["teams"]) + 1

@app.get("/teams")
def get_teams():
    return jsonify(_store["teams"])

@app.post("/teams")
def add_team():
    data = request.json or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "Name required"}), 400
    team = {"id": next_team_id(), "name": name, "group": data.get("group")}
    _store["teams"].append(team)
    save_store(_store)
    return jsonify(team), 201

@app.delete("/teams/<int:team_id>")
def delete_team(team_id):
    teams = _store["teams"]
    idx = next((i for i, t in enumerate(teams) if t["id"] == team_id), None)
    if idx is None:
        return jsonify({"error": "Team not found"}), 404
    teams.pop(idx)
    save_store(_store)
    return jsonify({"status": "deleted"})

@app.get("/tournament")
def get_tournament():
    return jsonify(_store["tournament"])

@app.post("/tournament")
def update_tournament():
    data = request.json or {}
    # einfache Validierung
    mode = data.get("mode", _store["tournament"].get("mode"))
    group_count = data.get("groupCount", _store["tournament"].get("groupCount"))
    _store["tournament"]["mode"] = mode
    _store["tournament"]["groupCount"] = int(group_count) if group_count is not None else None
    save_store(_store)
    return jsonify(_store["tournament"])

@app.get("/group-matches")
def get_group_matches():
    return jsonify(_store["group_matches"])

def generate_round_robin(teams_arr):
    matches = []
    for i in range(len(teams_arr)):
        for j in range(i + 1, len(teams_arr)):
            matches.append({"team1": teams_arr[i], "team2": teams_arr[j], "winner": None})
    return matches

@app.post("/generate-groups")
def generate_groups():
    # verteilt Teams auf Gruppen und erstellt Gruppenspiele (Round-Robin)
    groups = []
    count = _store["tournament"].get("groupCount") or 4
    group_letters = ["A","B","C","D","E","F","G","H"]
    groups_names = [f"Gruppe {group_letters[i] if i < len(group_letters) else i+1}" for i in range(count)]

    # clear previous groups and matches
    for t in _store["teams"]:
        t["group"] = None
    _store["group_matches"] = {}

    # round-robin assignment by index
    for idx, t in enumerate(_store["teams"]):
        group_idx = idx % count
        t["group"] = groups_names[group_idx]

    # build matches per group
    grouped = {}
    for g in groups_names:
        team_names = [t["name"] for t in _store["teams"] if t.get("group") == g]
        grouped[g] = generate_round_robin(team_names)
    _store["group_matches"] = grouped
    save_store(_store)
    return jsonify({"status": "groups-assigned", "groups": grouped})

@app.post("/group-matches/<group_name>/<int:match_index>/winner")
def set_match_winner(group_name, match_index):
    data = request.json or {}
    winner = data.get("winner")
    if group_name not in _store["group_matches"]:
        return jsonify({"error": "group not found"}), 404
    matches = _store["group_matches"][group_name]
    if match_index < 0 or match_index >= len(matches):
        return jsonify({"error": "match index out of range"}), 400
    matches[match_index]["winner"] = winner
    save_store(_store)
    return jsonify(matches[match_index])

@app.get("/matches")
def get_matches():
    # flattened list of all matches
    all_matches = []
    for g, ms in _store["group_matches"].items():
        for m in ms:
            m_copy = dict(m)
            m_copy["group"] = g
            all_matches.append(m_copy)
    return jsonify(all_matches)

# health
@app.get("/health")
def health():
    return jsonify({"ok": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
