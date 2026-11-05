# Fredagsbarens event-system

Et lille system til fredagsbarens events: en **Flask-API**, der holder styr på events og
tilmeldinger, og en **Streamlit-frontend**, der taler med API'et over HTTP. Alt kan startes
med `docker compose up --build` – eller køres lokalt uden Docker.

## Struktur

```
fredagsbar/
├── api.py               # Del 1: Flask-API
├── swagger.json         # Del 1: OpenAPI-dokumentation af API'et
├── app.py               # Del 2: Streamlit-frontend
├── Dockerfile           # Del 3
├── docker-compose.yml   # Del 3
├── .dockerignore        # Del 3
├── pyproject.toml
├── uv.lock
└── README.md
```

## Forudsætninger

- Python 3.12 og [uv](https://docs.astral.sh/uv/) til lokal kørsel
- Docker og Docker Compose til Del 3

## Kør lokalt uden Docker

```bash
uv sync
```

Start API'et i terminal 1:

```bash
uv run api.py
```

Start frontenden i terminal 2:

```bash
uv run streamlit run app.py
```

- Frontend: <http://localhost:8501>
- API: <http://localhost:5000>

Frontenden bruger `API_URL` til at finde API'et. Uden den peger den på
`http://127.0.0.1:5000`, som er adressen, når begge dele kører lokalt.

## Kør med Docker

Fra roden af repoet:

```bash
docker compose up --build
```

- Frontend: <http://localhost:8501>
- API: <http://localhost:5000> – porten er koblet til værtsmaskinen, så API'et kan testes
  i Postman/Insomnia eller med `curl`.

`docker-compose.yml` har to services, `api` og `frontend`, som bygges fra samme
`Dockerfile`. Inde i Docker kan frontenden ikke bruge `127.0.0.1` (det er containeren selv),
så den får `API_URL=http://api:5000` og taler med API-containeren via servicenavnet.
Begge programmer lytter på `0.0.0.0` i containeren.

Stop og ryd op:

```bash
docker compose down
```

## API-endpoints

| Metode | URL                              | Body                          | Succes                        |
| ------ | -------------------------------- | ----------------------------- | ----------------------------- |
| GET    | `/events`                        | –                             | 200 + liste af events         |
| GET    | `/events/<id>`                   | –                             | 200 + ét event                |
| POST   | `/events`                        | `{"title", "date", "capacity"}` | 201 + det nye event         |
| POST   | `/events/<id>/signups`           | `{"name"}`                    | 201 + det opdaterede event    |
| DELETE | `/events/<id>/signups/<name>`    | –                             | 204                           |
| DELETE | `/events/<id>`                   | –                             | 204                           |

Fejl returneres som JSON på formen `{"error": "..."}` med statuskoden:

- **400** – `title`, `date` eller `capacity` mangler, `capacity` er ikke et positivt
  heltal, eller en tilmelding mangler `name`
- **404** – eventet findes ikke, eller tilmeldingen findes ikke ved afmelding
- **409** – eventet er fuldt, eller personen er allerede tilmeldt

Eksempel:

```bash
curl http://localhost:5000/events
curl -X POST http://localhost:5000/events \
  -H "Content-Type: application/json" \
  -d '{"title": "Quizaften", "date": "2026-12-04", "capacity": 20}'
```

## Dokumentation

`swagger.json` beskriver alle seks endpoints inklusive fejlkoder. Åbn filen i
[Swagger Editor](https://editor.swagger.io/) for at se og afprøve API'et.

## Data

Al data ligger i en liste i hukommelsen i `api.py` (ligesom `users` i `hello_api.py`).
Det betyder, at ændringer forsvinder, når API'et genstartes – der er ingen database.
