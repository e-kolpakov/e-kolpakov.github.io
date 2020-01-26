import hypothesis.strategies as st
from src.user import User

user_id_gen = st.integers(min_value=1)  # not really required, just to demonstrate composeability
user_gen = st.builds(User, user_id_gen, st.text(), st.datetimes())