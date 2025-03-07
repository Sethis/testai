

import random
from typing import Protocol
from datetime import datetime


class GetUniqueNameProtocol(Protocol):
    def __call__(self, postfix: str) -> str:
        raise NotImplementedError()


class SimpleGetUniqueName:
    __slots__ = ("_user_id", "_current_time", "_random_salt", "_used")

    def __init__(self, user_id: int):
        self._user_id = user_id
        self._current_time = f"{datetime.now().timestamp()}".replace(".", "_")
        self._random_salt = random.randint(1, 1000)
        self._used = 0

    def __call__(self, postfix: str):
        self._user_id += 1

        return (
            f"{self._user_id}_"
            f"{self._used}_"
            f"{self._current_time}_"
            f"{self._random_salt}"
            f"{postfix}"
        )
