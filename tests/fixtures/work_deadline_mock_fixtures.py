import datetime
from unittest.mock import AsyncMock, patch

import pytest


@pytest.fixture(scope="function", autouse=False)
def mock_work_deadline():
    base_path = "app.services.works.work_service.WorksService"

    async def get_deadline(*args, **kwargs):
        return datetime.datetime.now() - datetime.timedelta(days=1)

    patches = [patch(f"{base_path}._get_submission_deadline", new_callable=AsyncMock, side_effect=get_deadline)]

    for p in patches:
        p.start()

    yield

    for p in patches:
        p.stop()
