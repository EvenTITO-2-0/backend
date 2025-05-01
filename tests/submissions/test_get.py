from ..commontest import create_headers


async def test_get_latest_submission(
    client, create_user, create_event, create_work_from_user, create_submission_from_work
):
    event_id = create_event["id"]
    response = await client.get(
        f"/events/{event_id}/works/{create_work_from_user}/submissions/latest",
        headers=create_headers(create_user["id"]),
    )
    assert response.status_code == 200, f"response error: {response.json()}"
    assert response.json()["id"] == create_submission_from_work


async def test_get_all_submissions(
    client, create_user, create_event, create_work_from_user, create_submission_from_work
):
    event_id = create_event["id"]
    response = await client.get(
        f"/events/{event_id}/works/{create_work_from_user}/submissions", headers=create_headers(create_user["id"])
    )
    assert response.status_code == 200, f"response error: {response.json()}"
    submissions = response.json()
    assert len(submissions) == 1


async def test_get_latest_submission_no_submission_fails(client, create_user, create_event, create_work_from_user):
    event_id = create_event["id"]
    response = await client.get(
        f"/events/{event_id}/works/{create_work_from_user}/submissions/latest",
        headers=create_headers(create_user["id"]),
    )
    assert response.status_code == 404
