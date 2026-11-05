import os

from flask import Flask, jsonify, request

app = Flask(__name__)
app.json.ensure_ascii = False

# Alt data ligger i hukommelsen og forsvinder, når API'et genstartes.
events = [
    {
        "id": 1,
        "title": "Quizaften",
        "date": "2026-11-13",
        "capacity": 3,
        "participants": ["Anna", "Bo"],
    },
    {
        "id": 2,
        "title": "Karaoké",
        "date": "2026-11-20",
        "capacity": 4,
        "participants": ["Gustav", "Philip"],
    },
    {
        "id": 3,
        "title": "BeerPong Tourney",
        "date": "2026-11-27",
        "capacity": 6,
        "participants": ["Ulrik", "Anders", "Markus"],
    },
]


def find_event(event_id):
    """Returnér eventet med det givne id, eller None hvis det ikke findes."""
    for event in events:
        if event["id"] == event_id:
            return event
    return None


def error(message, status_code):
    return jsonify({"error": message}), status_code


@app.get("/events")
def get_events():
    return jsonify(events), 200


@app.get("/events/<int:event_id>")
def get_event(event_id):
    event = find_event(event_id)
    if event is None:
        return error("Eventet findes ikke", 404)
    return jsonify(event), 200


@app.post("/events")
def create_event():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return error("Body skal være JSON med title, date og capacity", 400)

    missing = [
        field
        for field in ("title", "date", "capacity")
        if field not in data or data[field] is None or data[field] == ""
    ]
    if missing:
        return error("Følgende felter mangler: " + ", ".join(missing), 400)

    title = data["title"]
    event_date = data["date"]
    capacity = data["capacity"]

    if not isinstance(title, str) or not title.strip():
        return error("title skal være en tekst", 400)
    if not isinstance(event_date, str) or not event_date.strip():
        return error("date skal være en tekst på formen YYYY-MM-DD", 400)
    # bool er en underklasse af int, så den skal tjekkes særskilt.
    if isinstance(capacity, bool) or not isinstance(capacity, int) or capacity <= 0:
        return error("capacity skal være et positivt heltal", 400)

    event = {
        "id": max((event["id"] for event in events), default=0) + 1,
        "title": title.strip(),
        "date": event_date.strip(),
        "capacity": capacity,
        "participants": [],
    }
    events.append(event)
    return jsonify(event), 201


@app.delete("/events/<int:event_id>")
def delete_event(event_id):
    event = find_event(event_id)
    if event is None:
        return error("Eventet findes ikke", 404)
    events.remove(event)
    return "", 204


@app.post("/events/<int:event_id>/signups")
def create_signup(event_id):
    event = find_event(event_id)
    if event is None:
        return error("Eventet findes ikke", 404)

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return error("Body skal være JSON med name", 400)

    name = data.get("name")
    if not isinstance(name, str) or not name.strip():
        return error("name mangler", 400)
    name = name.strip()

    if len(event["participants"]) >= event["capacity"]:
        return error("Eventet er fuldt", 409)
    if name in event["participants"]:
        return error("Personen er allerede tilmeldt", 409)

    event["participants"].append(name)
    return jsonify(event), 201


@app.delete("/events/<int:event_id>/signups/<name>")
def delete_signup(event_id, name):
    event = find_event(event_id)
    if event is None:
        return error("Eventet findes ikke", 404)

    if name not in event["participants"]:
        return error("Tilmeldningen findes ikke", 404)

    event["participants"].remove(name)
    return "", 204


@app.errorhandler(404)
def handle_not_found(_error):
    return error("Ressourcen findes ikke", 404)


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "5000")),
        debug=os.environ.get("FLASK_DEBUG") == "1",
    )
