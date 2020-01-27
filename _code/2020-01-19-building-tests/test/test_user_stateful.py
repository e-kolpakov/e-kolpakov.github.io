import unittest
from hypothesis.stateful import RuleBasedStateMachine, rule, Bundle
from src.user import User, InMemoryUserRepository
from test.user_generators import user_id_gen, user_gen


class InMemoryUserRepositoryFSM(RuleBasedStateMachine):
    def __init__(self):
        super(InMemoryUserRepositoryFSM, self).__init__()
        self.repository = InMemoryUserRepository()
        self.model = dict()

    users = Bundle('users')

    @rule(target=users, user=user_gen)
    def add_user(self, user):
        return user

    @rule(user=users)
    def save(self, user: User):
        self.model[user.id] = user
        self.repository.save(user)

    @rule(user=users)
    def get(self, user):
        assert self.repository.get(user.id) == self.model.get(user.id)


InMemoryUserRepositoryTest = InMemoryUserRepositoryFSM.TestCase

if __name__ == "__main__":
    unittest.main()
