import datetime

from app.database.models.event import EventType
from app.schemas.events.create_event import CreateEventSchema
from app.schemas.events.dates import DateSchema, MandatoryDates
from app.schemas.works.author import AuthorInformation
from app.schemas.works.work import CreateWorkSchema


async def get_user_method(client, user_id):
    response = await client.get(f"/users/{user_id}", headers=create_headers(user_id))

    return response.json()


def create_headers(user_id):
    return {"X-User-Id": user_id}


ONE_EVENT = [
    CreateEventSchema(
        title="Conferencia de química",
        dates=[
            DateSchema(
                name=MandatoryDates.START_DATE,
                label="Fecha de Comienzo",
                description="Fecha de comienzo del evento.",
                date=datetime.date.today() + datetime.timedelta(days=30),
                is_mandatory=True,
            ),
            DateSchema(
                name=MandatoryDates.END_DATE,
                label="Fecha de Finalización",
                description="Fecha de comienzo del evento.",
                is_mandatory=True,
                date=datetime.date.today() + datetime.timedelta(days=32),
            ),
            DateSchema(
                name=MandatoryDates.SUBMISSION_DEADLINE_DATE,
                label="Fecha de envío de trabajos",
                description="Fecha límite de envío de trabajos.",
                is_mandatory=True,
            ),
        ],
        description="""
        Conferencia donde se tratará el tema de hidrocarburos
        """,
        event_type=EventType.CONFERENCE,
        location="Paseo Colon 850",
        tracks=["math", "chemistry", "phisics"],
    )
]

EVENTS = [
    CreateEventSchema(
        title="Conferencia de química",
        dates=[
            DateSchema(
                name=MandatoryDates.START_DATE,
                label="Fecha de Comienzo",
                description="Fecha de comienzo del evento.",
                date=datetime.date.today() + datetime.timedelta(days=30),
                is_mandatory=True,
            ),
            DateSchema(
                name=MandatoryDates.END_DATE,
                label="Fecha de Finalización",
                description="Fecha de comienzo del evento.",
                is_mandatory=True,
                date=datetime.date.today() + datetime.timedelta(days=32),
            ),
            DateSchema(
                name=MandatoryDates.SUBMISSION_DEADLINE_DATE,
                label="Fecha de envío de trabajos",
                description="Fecha límite de envío de trabajos.",
                is_mandatory=True,
            ),
        ],
        description="""
        Conferencia donde se tratará el tema de hidrocarburos
        """,
        event_type=EventType.CONFERENCE,
        location="Paseo Colon 850",
        tracks=["math", "chemistry", "phisics"],
    ),
    CreateEventSchema(
        title="Maratón de proba",
        description="Abierta para todos los estudiantes" + "de la materia Probabilidad y Estadística",
        event_type=EventType.TALK,
        location="Paseo Colon 850",
        tracks=["math", "chemistry", "phisics"],
    ),
    CreateEventSchema(
        title="Conferencia JIAFES",
        description="Nueva edición de la conferencia",
        event_type=EventType.CONFERENCE,
        location="Paseo Colon 850",
        tracks=["math", "chemistry", "phisics"],
    ),
]


WORKS = [
    CreateWorkSchema(
        title=(
            "Comparación del Rendimiento de Curve25519, "
            "P-256 y Curvas de Edwards en Algoritmos "
            "de Criptografía Cuántica"
        ),
        track="chemistry",
        abstract="",
        keywords=["ciber", "security"],
        authors=[AuthorInformation(full_name="Mateo Perez", membership="fiuba", mail="mail@mail.com")],
    ),
    CreateWorkSchema(
        title=("Aplicaciones de los Toros de Clifford en " "la Teoría de Códigos Correctores de Errores"),
        track="math",
        abstract=(
            "Este trabajo explora los toros de Clifford y su aplicación en la "
            "teoría de códigos correctores de errores. Los toros de Clifford, "
            "con sus propiedades topológicas y geométricas únicas, permiten "
            "el diseño de códigos que mejoran la eficiencia y robustez en la "
            "detección y corrección de errores en sistemas de comunicación "
            "digital. Se presenta un marco teórico que aprovecha la simetría "
            "y periodicidad de estos toros para simplificar la codificación y "
            "decodificación, demostrando mejoras significativas en "
            "comparación con los métodos tradicionales."
        ),
        keywords=["math", "topology", "Clifford Torus", "Complex Spaces"],
        authors=[
            AuthorInformation(full_name="Juan Sanchez", membership="FIUBA", mail="juansanchez@mail.com"),
            AuthorInformation(full_name="Julian Altocapo", membership="Exactas", mail="julianaltocapo@mail.com"),
        ],
    ),
]
