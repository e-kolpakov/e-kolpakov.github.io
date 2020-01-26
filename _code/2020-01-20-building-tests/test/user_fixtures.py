from dateutil import parser
from src.user import User


class Users:
    jack = User(1, "jack", parser.parse("1999-01-01"))
    jill = User(2, "Jill", parser.parse("2001-06-14"))
    jane = User(3, "Jane", parser.parse("2003-01-01"))