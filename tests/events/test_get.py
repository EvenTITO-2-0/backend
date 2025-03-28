import uuid

import pytest
from fastapi.encoders import jsonable_encoder

from app.database.models.event import EventStatus
from app.exceptions.events_exceptions import EventNotFound
from app.schemas.events.event_status import EventStatusSchema
from app.schemas.events.roles import EventRole

from ..commontest import EVENTS, create_headers


async def test_get_event(client, create_event, create_user):
    response = await client.get(f"/events/{create_event['id']}/public", headers=create_headers(create_user["id"]))

    assert response.status_code == 200
    event = response.json()
    assert event["title"] == create_event["title"]
    assert event["status"] == EventStatus.CREATED  # The admin created it.
    assert event["review_skeleton"]["questions"] is not None
    assert event["review_skeleton"]["recommendation"] is not None
    assert event["review_skeleton"]["recommendation"]["question"] == "Recomendación"
    assert event["review_skeleton"]["recommendation"]["type_question"] == "multiple_choice"
    assert event["review_skeleton"]["recommendation"]["more_than_one_answer_allowed"] is False
    assert len(event["review_skeleton"]["recommendation"]["options"]) == 3
    assert len(response.json()["roles"]) == 0


async def test_get_event_not_exists_fails(client, create_user):
    this_id_does_not_exist = uuid.uuid4()
    response = await client.get(
        f"/events/{str(this_id_does_not_exist)}/public", headers=create_headers(create_user["id"])
    )

    assert response.status_code == 404
    assert response.json()["detail"] == EventNotFound(str(this_id_does_not_exist)).detail


async def test_get_event_not_exists_fails_with_422_if_not_uuid(client, create_user):
    this_id_does_not_exist = "this-id-is-not-uuid"
    response = await client.get(f"/events/{this_id_does_not_exist}/public", headers=create_headers(create_user["id"]))

    assert response.status_code == 422


async def test_get_all_events_not_admin_error(client, create_many_events, create_user):
    response = await client.get("/events/", headers=create_headers(create_user["id"]))
    assert response.status_code == 409
    assert response.json()["detail"]["errorcode"] == "INVALID_QUERY_EVENT_NOT_CREATED_NOT_ADMIN"


async def test_get_all_events_admin_gets_all(client, create_many_events, admin_data):
    response = await client.get("/events/", headers=create_headers(admin_data.id))
    assert response.status_code == 200
    events = response.json()
    assert len(events) == 3
    assert events[0]["creator"]["fullname"] == "Jorge Benitez"
    assert events[0]["creator"]["email"] == "jbenitez@email.com"
    assert events[0]["creator"]["id"] is not None
    assert events[1]["creator"]["fullname"] == "Jorge Benitez"
    assert events[1]["creator"]["email"] == "jbenitez@email.com"
    assert events[1]["creator"]["id"] is not None
    assert events[2]["creator"]["fullname"] == "Jorge Benitez"
    assert events[2]["creator"]["email"] == "jbenitez@email.com"
    assert events[2]["creator"]["id"] is not None


async def test_get_all_events_admin_status_waiting_approval_is_zero(client, create_many_events, admin_data):
    status_update = EventStatusSchema(status=EventStatus.CREATED)
    response = await client.patch(
        f"/events/{create_many_events[0]}/status",
        json=jsonable_encoder(status_update),
        headers=create_headers(admin_data.id),
    )

    response = await client.get(
        "/events/", headers=create_headers(admin_data.id), params={"status": EventStatus.WAITING_APPROVAL.value}
    )
    assert response.status_code == 200
    assert len(response.json()) == 0


async def test_get_all_events_non_admin_can_query_started(
    client, create_many_events, create_event_started, admin_data, create_user
):
    response = await client.get(
        "/events/", headers=create_headers(create_user["id"]), params={"status": EventStatus.STARTED.value}
    )
    assert response.status_code == 200
    assert len(response.json()) == 1
    events = response.json()
    assert events[0]["creator"] is None


async def test_get_all_events_non_admin_can_not_query_created(client, create_many_events, admin_data, create_user):
    status_update = EventStatusSchema(status=EventStatus.STARTED)
    response = await client.patch(
        f"/events/{create_many_events[0]}/status",
        json=jsonable_encoder(status_update),
        headers=create_headers(admin_data.id),
    )

    response = await client.get(
        "/events/", headers=create_headers(create_user["id"]), params={"status": EventStatus.CREATED.value}
    )
    assert response.status_code == 409


async def test_get_all_events_query_by_title_same_title(client, create_many_events, admin_data):
    response = await client.get("/events/", headers=create_headers(admin_data.id), params={"search": EVENTS[0].title})
    assert response.status_code == 200
    assert len(response.json()) == 1


async def test_get_all_events_query_by_title_contains(client, create_many_events, admin_data):
    response = await client.get("/events/", headers=create_headers(admin_data.id), params={"search": "de"})
    assert response.status_code == 200
    assert len(response.json()) == 2


async def test_get_all_events_public_is_status_created(client, create_event_started, admin_data):
    response = await client.get(
        "/events/", params={"status": EventStatus.STARTED.value}, headers=create_headers(admin_data.id)
    )
    assert response.status_code == 200
    assert len(response.json()) == 1


async def test_get_all_events_public_is_status_created2(client, create_many_events_started, admin_data):
    n_events = len(create_many_events_started)

    response = await client.get(
        "/events/", params={"status": EventStatus.STARTED.value}, headers=create_headers(admin_data.id)
    )
    assert response.status_code == 200
    assert len(response.json()) == n_events


@pytest.mark.skip(reason="TODO: Write this code. Which date should we take? Or add a param for ordering?")
async def test_get_all_events_should_be_ordered_by_something():
    raise AssertionError("Test not implemented yet")


async def test_get_event_with_organizer_role(client, create_event_from_event_creator, create_event_creator):
    response = await client.get(
        f"/events/{create_event_from_event_creator}/public", headers=create_headers(create_event_creator["id"])
    )

    assert response.status_code == 200
    assert EventRole.ORGANIZER in response.json()["roles"]
    assert len(response.json()["roles"]) == 1


async def test_get_event_with_chair_role(client, create_event_chair, create_event_from_event_creator):
    response = await client.get(
        f"/events/{create_event_from_event_creator}/public", headers=create_headers(create_event_chair)
    )

    assert response.status_code == 200
    assert EventRole.CHAIR in response.json()["roles"]
    assert len(response.json()["roles"]) == 1


async def test_get_event_with_attendee_role(client, create_inscription):
    response = await client.get(
        f"/events/{create_inscription['event_id']}/public", headers=create_headers(create_inscription["user_id"])
    )

    assert response.status_code == 200
    assert EventRole.ATTENDEE in response.json()["roles"]
    assert len(response.json()["roles"]) == 1
