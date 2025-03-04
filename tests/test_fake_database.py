

import pytest

from testai.src.interactors.database.gateways.user import FakeUserGateWay
from testai.src.interactors.database.repositories.user import UserRepo


async def test_get_by_tg():
    fakerepo = UserRepo(
        user_gateway=FakeUserGateWay()
    )

    user = await fakerepo.get_user_by_tg_id(123)

    assert user.id == 123
    assert user.tg_id == 123
