import pytest

from ...commontest import create_headers


@pytest.fixture(scope="function")
async def create_submission_from_work(client, create_user, create_event, create_work_from_user) -> str:
    event_id = create_event["id"]
    response = await client.put(
        f"/events/{event_id}/works/{create_work_from_user}/submissions/submit",
        headers=create_headers(create_user["id"]),
    )
    assert response.status_code == 201, f"error: {response.json()}"
    return response.json()["id"]
