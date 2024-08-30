import pytest
import pytest_asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from motor.motor_asyncio import AsyncIOMotorClientSession
from app.main import app
from app.config import settings
from app.db import get_session
from app.tests.utils import get_superuser_token_headers, authentication_token_from_email


'''
Fixtures are created when first requested by a test, and are destroyed based on their scope:
    - function: the default scope, the fixture is destroyed at the end of the test.
    - class: the fixture is destroyed during teardown of the last test in the class.
    - module: the fixture is destroyed during teardown of the last test in the module.
    - package: the fixture is destroyed during teardown of the last test in the package.
    - session: the fixture is destroyed at the end of the test session.
'''


def pytest_collection_modifyitems(items):
    pytest_asyncio_tests = (item for item in items if pytest_asyncio.is_async_test(item))
    session_scope_marker = pytest.mark.asyncio(loop_scope="function")
    for async_test in pytest_asyncio_tests:
        async_test.add_marker(session_scope_marker, append=False)


@pytest_asyncio.fixture(loop_scope="function")
async def session() -> AsyncGenerator[AsyncIOMotorClientSession, None]:
    async for _session in get_session():
        yield _session


@pytest_asyncio.fixture(loop_scope="session")
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as _client:
        yield _client


@pytest_asyncio.fixture(loop_scope="function")
async def superuser_token_headers(client: AsyncClient) -> dict[str, str]:
    return await get_superuser_token_headers(client)


@pytest_asyncio.fixture(loop_scope="function")
async def normal_user_token_headers(client: AsyncClient, session: AsyncIOMotorClientSession) -> dict[str, str]:
    return await authentication_token_from_email(client=client, email=settings.EMAIL_TEST_USER, session=session)
