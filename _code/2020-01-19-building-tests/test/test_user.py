import unittest
from unittest.mock import Mock
from dateutil import parser
from src.user import User, UserRepository, UserService, age_at
from test.user_fixtures import Users


class TestUser(unittest.TestCase):
    def test_is_older_older(self):
        self.assertTrue(Users.jack.is_older(Users.jill))

    def test_is_older_younger(self):
        self.assertFalse(Users.jane.is_older(Users.jill))


class TestAgeAt(unittest.TestCase):
    def test_age_at_birth(self):
        self.assertEqual(age_at(Users.jack, Users.jack.date_of_birth), 0)

    def test_age_at_some_random_date_after_birth(self):
        self.assertEqual(age_at(Users.jill, parser.parse("2019-11-11")), 18)

    def test_age_at_16th_birthday(self):
        self.assertEqual(age_at(Users.jack, parser.parse("2015-01-01")), 16)

    def test_age_before_born(self):
        with self.assertRaises(AssertionError):
            age_at(Users.jack, parser.parse("1990-01-01"))


class UserServiceTest(unittest.TestCase):
    def setUp(self):
        self._repo = Mock(spec=UserRepository)
        self._service = UserService(self._repo)

    def test_get_user(self):
        self._repo.get.return_value = Users.jack
        returned = self._service.read_user(Users.jack.id)
        self._repo.get.assert_called_once_with(Users.jack.id)
        self.assertEqual(returned, Users.jack)

    def test_update_user_name(self):
        self._repo.get.return_value = Users.jack
        new_name = "Captain Jack Sparrow"

        self._service.update_user_name(Users.jack.id, new_name)

        expected_saved_user = User(Users.jack.id, new_name, Users.jack.date_of_birth)
        self._repo.save.assert_called_once()
        # call_args[0][0] is the first positional argument of the call
        updated_user = self._repo.save.call_args[0][0]
        # note: dataclass generates __eq__ that checks all fields
        self.assertEqual(updated_user, expected_saved_user)


if __name__ == '__main__':
    unittest.main()
