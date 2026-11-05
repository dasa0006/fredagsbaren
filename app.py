import os
from datetime import date
from urllib.parse import quote

import httpx
import streamlit as st

# API'ets adresse er forskellig lokalt og i Docker. I docker-compose.yml sættes
# API_URL til http://api:5000, lokalt bruges standardværdien.
API_URL = os.environ.get("API_URL", "http://127.0.0.1:5000").rstrip("/")
TIMEOUT = 2.0

st.set_page_config(page_title="Fredagsbaren", page_icon="🍻", layout="wide")


class ApiError(Exception):
    """En fejl, der skal vises som en pæn besked i stedet for en stack trace."""


def api_request(method, path, **kwargs):
    """Kald API'et og oversæt HTTP-fejl til ApiError med en læsbar besked."""
    try:
        response = httpx.request(method, f"{API_URL}{path}", timeout=TIMEOUT, **kwargs)
        response.raise_for_status()
        return response
    except httpx.ConnectError as exc:
        raise ApiError(
            f"Kan ikke få forbindelse til API'et på {API_URL}. Er API'et startet?"
        ) from exc
    except httpx.TimeoutException as exc:
        raise ApiError("API'et svarede ikke i tide. Prøv igen om lidt.") from exc
    except httpx.HTTPStatusError as exc:
        try:
            body = exc.response.json()
        except ValueError:
            body = None
        message = body.get("error") if isinstance(body, dict) else None
        if not message:
            message = f"API'et svarede med HTTP {exc.response.status_code}."
        raise ApiError(message) from exc
    except httpx.HTTPError as exc:
        raise ApiError("Der skete en ukendt fejl i kommunikationen med API'et.") from exc


def flash(kind, message):
    """Gem en besked, der vises efter det næste rerun."""
    st.session_state["flash"] = (kind, message)


def show_flash():
    item = st.session_state.pop("flash", None)
    if item is None:
        return
    kind, message = item
    if kind == "success":
        st.success(message)
    else:
        st.error(message)


st.title("🍻 Fredagsbaren")
st.caption("Hold styr på events og tilmeldinger – eller opret et nyt event.")
show_flash()

if "name" not in st.session_state:
    st.session_state.name = ""

with st.sidebar:
    st.header("Mit navn")
    st.text_input("Dit navn", key="name", placeholder="Fx Anna")
    st.caption("Navnet bruges, når du tilmelder eller afmelder dig et event.")
    name = st.session_state.name.strip()

try:
    events = api_request("GET", "/events").json()
except ApiError as exc:
    st.error(str(exc))
    st.stop()
except ValueError:
    st.error("API'et returnerede et svar, der ikke er gyldig JSON.")
    st.stop()

st.subheader("Oversigt")
if events:
    rows = [
        {
            "Titel": event["title"],
            "Dato": event["date"],
            "Antal tilmeldte": len(event["participants"]),
            "Ledige pladser": max(event["capacity"] - len(event["participants"]), 0),
        }
        for event in events
    ]
    st.dataframe(rows, hide_index=True)
else:
    st.info("Der er ingen events endnu. Opret det første nedenfor.")

st.subheader("Tilmeld og afmeld")
if events:
    events_by_id = {event["id"]: event for event in events}
    selected_id = st.selectbox(
        "Vælg event",
        options=list(events_by_id),
        format_func=lambda event_id: (
            f"{events_by_id[event_id]['title']} ({events_by_id[event_id]['date']})"
        ),
        key="selected_event",
    )
    selected_event = events_by_id[selected_id]
    participants = selected_event["participants"]
    free_places = max(selected_event["capacity"] - len(participants), 0)

    st.markdown(f"**{selected_event['title']}** · {selected_event['date']}")
    st.write(
        f"{len(participants)} af {selected_event['capacity']} pladser er optaget "
        f"({free_places} ledige)."
    )
    if participants:
        st.write("Tilmeldte: " + ", ".join(participants))
    else:
        st.write("Der er endnu ingen tilmeldte.")

    signup_column, unsubscribe_column = st.columns(2)
    with signup_column:
        if st.button(
            "Tilmeld mig",
            key="signup",
            type="primary",
            disabled=not name or free_places <= 0,
        ):
            try:
                api_request(
                    "POST",
                    f"/events/{selected_event['id']}/signups",
                    json={"name": name},
                )
            except ApiError as exc:
                st.error(str(exc))
            else:
                flash("success", f"Du er tilmeldt {selected_event['title']}.")
                st.rerun()

    with unsubscribe_column:
        if st.button("Afmeld mig", key="unsubscribe", disabled=not name):
            try:
                api_request(
                    "DELETE",
                    f"/events/{selected_event['id']}/signups/"
                    f"{quote(name, safe='')}",
                )
            except ApiError as exc:
                st.error(str(exc))
            else:
                flash("success", f"Du er afmeldt {selected_event['title']}.")
                st.rerun()

    if not name:
        st.info("Skriv dit navn i sidebaren for at kunne tilmelde og afmelde dig.")
else:
    st.info("Opret et event nedenfor, før der kan tilmeldes deltagere.")

st.subheader("Opret event")
with st.form("create_event", clear_on_submit=True):
    new_title = st.text_input("Titel", key="new_title", placeholder="Fx Quizaften")
    new_date = st.date_input("Dato", key="new_date", value=date.today())
    new_capacity = st.number_input(
        "Antal pladser", key="new_capacity", min_value=1, value=10, step=1
    )
    submitted = st.form_submit_button("Opret event", type="primary")

if submitted:
    if not new_title.strip():
        st.error("Titel må ikke være tom.")
    else:
        try:
            response = api_request(
                "POST",
                "/events",
                json={
                    "title": new_title.strip(),
                    "date": new_date.isoformat(),
                    "capacity": int(new_capacity),
                },
            )
        except ApiError as exc:
            st.error(str(exc))
        else:
            created = response.json()
            flash("success", f"Eventet “{created['title']}” blev oprettet.")
            st.rerun()
