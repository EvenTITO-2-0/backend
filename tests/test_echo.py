from .commontest import create_headers


async def test_echo(client, admin_data):
    response = await client.get("/users/echo", headers=create_headers(admin_data.id))
    assert response.status_code == 200
