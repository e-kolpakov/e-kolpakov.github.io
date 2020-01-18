from dataclasses import dataclass
from datetime import date
from dateutil.relativedelta import relativedelta


@dataclass
class User:
    id: int
    name: str
    date_of_birth: date

    def is_older(self, other) -> bool:
        assert(isinstance(other, User))
        return self.date_of_birth < other.date_of_birth


def age_at(user: User, date: date) -> int:
    assert(user.date_of_birth <= date)
    return relativedelta(date, user.date_of_birth).years


class UserRepository:
    def get(self, id: int) -> User: pass
    def save(self, user: User) -> None: pass


class InMemoryUserRepository(UserRepository):
    def __init__(self):
        self._store = dict()

    def get(self, id: int) -> User:
        return self._store.get(id)

    def save(self, user: User) -> None:
        # if len(self._store) > 2:  # some non-trivial buggy code to trigger the error
        #     return
        self._store[user.id] = user

class UserService:
    def __init__(self, user_repo: UserRepository):
        self._repo = user_repo

    def read_user(self, id: int) -> User:
        return self._repo.get(id)

    def update_user_name(self, id: int, new_name: str):
        old_record = self._repo.get(id)
        old_record.name = new_name
        self._repo.save(old_record)
