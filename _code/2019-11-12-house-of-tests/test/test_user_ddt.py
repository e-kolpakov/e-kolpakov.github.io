import unittest
import ddt
from unittest.mock import Mock
from datetime import timedelta
from dateutil import parser
from src.user import User, UserRepository, UserService, age_at
from test.user_fixtures import Users


@ddt.ddt
class TestUser(unittest.TestCase):
    @ddt.data(
        (Users.jack, Users.jill, True),
        (Users.jack, Users.jack, False),
        (Users.jane, Users.jill, False),
    )
    @ddt.unpack
    def test_is_older_older(self, user1, user2, expected_is_older):
        actual = user1.is_older(user2)
        self.assertEqual(actual, expected_is_older, f"{user1.name} is_older {user2.name} was not {expected_is_older}")


@ddt.ddt
class TestAgeAt(unittest.TestCase):
    @ddt.unpack
    @ddt.data(
        (Users.jack, Users.jack.date_of_birth, 0),
        (Users.jill, parser.parse("2019-11-11"), 18),
        (Users.jack, parser.parse("2015-01-01"), 16),
        (Users.jane, parser.parse("2203-01-01"), 200),
    )
    def test_age_at(self, user, date, expected_age):
        self.assertEqual(age_at(user, date), expected_age)

    @ddt.unpack
    @ddt.data(
        (Users.jack, parser.parse("1990-01-01")),
        (Users.jane, Users.jane.date_of_birth - timedelta(seconds=1)),
    )
    def test_age_before_born(self, user, date):
        with self.assertRaises(AssertionError):
            age_at(user, date)


@ddt.ddt
class UserServiceTest(unittest.TestCase):
    def setUp(self):
        self._repo = Mock(spec=UserRepository)
        self._service = UserService(self._repo)

    # ddt and non-ddt tests can peacefully coexist
    def test_get_user(self):
        self._repo.get.return_value = Users.jack
        returned = self._service.read_user(Users.jack.id)
        self._repo.get.assert_called_once_with(Users.jack.id)
        self.assertEqual(returned, Users.jack)

    @ddt.unpack
    @ddt.data(
        (1, "Jack Sparrow", "CAPTAIN Jack Sparrow"),
        (2, "Bond", "James Bond"),
        (3, "Pooh", "Winnie the Pooh")
    )
    def test_update_user_name(self, id, old_name, new_name):
        old_user = User(id, old_name, parser.parse("1970-01-01"))
        self._repo.get.return_value = old_user
        self._service.update_user_name(id, new_name)

        expected_saved_user = User(id, new_name, old_user.date_of_birth)
        self._repo.save.assert_called_once()
        # call_args[0][0] is the first positional argument of the call
        updated_user = self._repo.save.call_args[0][0]
        # note: dataclass generates __eq__ that checks all fields
        self.assertEqual(updated_user, expected_saved_user)


if __name__ == '__main__':
    unittest.main()
