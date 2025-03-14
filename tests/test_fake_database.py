

from testai.src.interactors.database.gateways.user import FakeUserGateWay
from testai.src.interactors.database.repositories.user import UserRepo


async def test_get_by_tg():
    fakerepo = UserRepo(
        user_gateway=FakeUserGateWay()
    )

    await fakerepo.upsert_user(123)

    user = await fakerepo.get_user_by_tg_id(123)

    assert user.id == 123
    assert user.tg_id == 123


async def test_get_by_user():
    fakerepo = UserRepo(
        user_gateway=FakeUserGateWay()
    )

    await fakerepo.upsert_user(123)

    user = await fakerepo.get_user_by_id(123)

    assert user.id == 123
    assert user.tg_id == 123


async def test_add_assistant():
    fakerepo = UserRepo(
        user_gateway=FakeUserGateWay()
    )

    await fakerepo.upsert_user(123)

    await fakerepo.add_assistant(123, "123", "some")

    user = await fakerepo.get_user_by_id(123)
    assert user.assistants[0].openai_id == "123"
    assert user.assistants[0].name == "some"


async def test_add_two_assistant():
    fakerepo = UserRepo(
        user_gateway=FakeUserGateWay()
    )

    await fakerepo.upsert_user(123)

    await fakerepo.add_assistant(123, "123", "some")
    await fakerepo.add_assistant(123, "321", "some2")

    user = await fakerepo.get_user_by_id(123)
    assert user.assistants[0].openai_id == "123"
    assert user.assistants[0].name == "some"

    assert user.assistants[1].openai_id == "321"
    assert user.assistants[1].name == "some2"
