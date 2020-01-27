from datetime import timedelta
from dateutil.relativedelta import relativedelta
from src.user import User, UserRepository, UserService, age_at

from hypothesis import given, assume
import hypothesis.strategies as st
from test.user_generators import user_id_gen, user_gen
import unittest
from unittest.mock import Mock


class TestUser(unittest.TestCase):
    @given(st.datetimes(), st.datetimes())
    def test_is_older(self, earlier_date, later_date):
        assume(earlier_date < later_date)  # test invariant - we want date1 < date2
        younger_user = User(1, "irrelevant", earlier_date)
        older_user = User(2, "irrelevant too", later_date)
        self.assertTrue(younger_user.is_older(older_user))  # property

    # This could have been written as below, but it fails "health check" - i.e. `assume` discards too many examples
    # @given(user_gen, user_gen)
    # def test_is_older(self, younger_user, older_user):
    #     assume(younger_user.date_of_birth < older_user.date_of_birth)  # test invariant - we want date1 < date2
    #     self.assertTrue(younger_user.is_older(older_user))  # property


class TestAgeAt(unittest.TestCase):
    @given(user_gen, st.datetimes())
    def test_age_at_tautological(self, user, date):
        # FIXME: this is an example of tautological test - DO NOT DO THIS
        assume(user.date_of_birth <= date)
        expected_age = relativedelta(date, user.date_of_birth).years
        self.assertEqual(age_at(user, date), expected_age)  # property

    @given(user_gen, st.integers(min_value=0, max_value=1000), st.data())
    def test_age_at_backward(self, user, age, data):
        assume(user.date_of_birth.year + age <= 10000)  # relativedelta doesn't like year 10000 and above
        # one of the techniques to define a property - work backwards from the output to the input that will produce it
        check_age_at = data.draw(st.datetimes(
            min_value=user.date_of_birth + relativedelta(dt1=user.date_of_birth, years=age),
            max_value=user.date_of_birth + relativedelta(dt1=user.date_of_birth, years=age+1) - timedelta(microseconds=1),
        ))
        self.assertEqual(age_at(user, check_age_at), age)  # property

    @given(user_gen, st.datetimes())
    def test_age_before_born(self, user, datetime):
        assume(user.date_of_birth > datetime)
        with self.assertRaises(AssertionError):  # property
            age_at(user, datetime)


class UserServiceTest(unittest.TestCase):
    @given(user_gen, st.text())
    def test_update_user_name(self, old_user, new_name):
        # caveat: need to create a mock for each test
        # to avoid multiple executions of the property against same instance of the mock
        mock_repo = Mock(spec=UserRepository)
        service = UserService(mock_repo)

        mock_repo.get.return_value = old_user
        service.update_user_name(old_user.id, new_name)

        mock_repo.save.assert_called_once()
        # call_args[0][0] is the first positional argument of the call
        updated_user = mock_repo.save.call_args[0][0]
        self.assertEqual(updated_user.name, new_name)  # property


if __name__ == "__main__":
    unittest.main()
