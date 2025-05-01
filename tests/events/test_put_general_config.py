from fastapi.encoders import jsonable_encoder

from app.schemas.events.schemas import DynamicTracksEventSchema

from ..commontest import create_headers


async def test_put_event(client, admin_data, create_event):
    update_create_event = create_event.copy()
    update_create_event["title"] = "new event"
    update_create_event["end_date"] = "2024-09-05T00:00:00"
    update_create_event["notification_mails"] = []
    event_id = update_create_event.pop("id")

    response = await client.put(
        f"/events/{event_id}/configuration/general",
        json=jsonable_encoder(update_create_event),
        headers=create_headers(admin_data.id),
    )

    assert response.status_code == 204


async def test_put_event_different_notif_mails(client, admin_data, create_event):
    update_create_event = create_event.copy()
    update_create_event["title"] = "new event"
    update_create_event["end_date"] = "2024-09-05T00:00:00"
    added_mail = "mateo@mail.com"
    update_create_event["notification_mails"] = [added_mail, "someother@mail.com"]
    event_id = update_create_event.pop("id")

    _ = await client.put(
        f"/events/{event_id}/configuration/general",
        json=jsonable_encoder(update_create_event),
        headers=create_headers(admin_data.id),
    )
    response = await client.get(f"/events/{event_id}/configuration", headers=create_headers(admin_data.id))

    assert response.status_code == 200
    assert response.json()["notification_mails"][0] == added_mail


async def test_put_event_change_tracks(client, admin_data, create_event):
    update_create_event = create_event.copy()
    update_create_event["title"] = "new event"
    new_tracks = ["first_track", "second_track"]
    update_create_event["tracks"] = new_tracks
    update_create_event["notification_mails"] = []
    event_id = update_create_event.pop("id")

    _ = await client.put(
        f"/events/{event_id}/configuration/general",
        json=jsonable_encoder(update_create_event),
        headers=create_headers(admin_data.id),
    )
    response = await client.get(f"/events/{event_id}/configuration", headers=create_headers(admin_data.id))

    assert response.status_code == 200
    assert response.json()["tracks"][0] == new_tracks[0]
    assert response.json()["tracks"][1] == new_tracks[1]


async def test_put_many_changes(client, admin_data, create_event):
    update_create_event = create_event.copy()
    update_create_event["title"] = "new event"
    new_tracks = ["first_track", "second_track"]
    update_create_event["tracks"] = new_tracks
    update_create_event["title"] = "New Event Title"
    update_create_event["description"] = "New Event Description"
    update_create_event["location"] = "New Event Location"
    update_create_event["contact"] = "New Event Contact Info"
    update_create_event["notification_mails"] = []
    event_id = update_create_event.pop("id")

    _ = await client.put(
        f"/events/{event_id}/configuration/general",
        json=jsonable_encoder(update_create_event),
        headers=create_headers(admin_data.id),
    )
    response = await client.get(f"/events/{event_id}/configuration", headers=create_headers(admin_data.id))

    assert response.status_code == 200
    assert response.json()["tracks"][0] == new_tracks[0]
    assert response.json()["tracks"][1] == new_tracks[1]

    # the title and description do not change.
    assert response.json()["title"] == create_event["title"]
    assert response.json()["description"] == create_event["description"]

    assert response.json()["location"] == update_create_event["location"]
    assert response.json()["contact"] == update_create_event["contact"]


async def test_update_tracks_ok(client, admin_data, create_event):
    new_tracks = ["futbol", "tenis", "golf"]
    tracks_to_add = DynamicTracksEventSchema(tracks=new_tracks)
    response = await client.put(
        f"/events/{create_event['id']}/configuration/general/tracks",
        json=jsonable_encoder(tracks_to_add),
        headers=create_headers(admin_data.id),
    )

    assert response.status_code == 204

    response = await client.get(f"/events/{create_event['id']}/configuration", headers=create_headers(admin_data.id))

    assert response.status_code == 200
    assert response.json()["tracks"][0] == new_tracks[0]
    assert response.json()["tracks"][1] == new_tracks[1]
    assert response.json()["tracks"][2] == new_tracks[2]

    # the title and description do not change.
    assert response.json()["title"] == create_event["title"]
    assert response.json()["description"] == create_event["description"]
    assert response.json()["location"] == create_event["location"]
    assert response.json()["contact"] == create_event["contact"]


async def test_update_tracks_fails_if_event_started(client, admin_data, create_event_started):
    tracks_to_add = DynamicTracksEventSchema(tracks=["futbol", "tenis", "golf"])
    response = await client.put(
        f"/events/{create_event_started}/configuration/general/tracks",
        json=jsonable_encoder(tracks_to_add),
        headers=create_headers(admin_data.id),
    )

    assert response.status_code == 409


async def test_update_event_metadata(client, admin_data, create_event):
    update_create_event = create_event.copy()

    metadata_json = {"test": "test"}
    update_create_event["mdata"] = metadata_json

    event_id = update_create_event.pop("id")

    _ = await client.put(
        f"/events/{event_id}/configuration/general",
        json=jsonable_encoder(update_create_event),
        headers=create_headers(admin_data.id),
    )
    response = await client.get(f"/events/{event_id}/configuration", headers=create_headers(admin_data.id))
    assert response.status_code == 200
    assert response.json()["mdata"] == metadata_json
