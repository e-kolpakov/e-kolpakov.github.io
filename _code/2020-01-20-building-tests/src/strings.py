def reverse_string(input: str) -> str:
    """
    This is a docstring  to illustrate doctests

    >>> reverse_string("Hello!")
    '!olleH'
    >>> reverse_string("")
    ''
    >>> reverse_string('Привет!')
    '!тевирП'
    """
    return input[::-1]


if __name__ == "__main__":
    import doctest
    doctest.testmod()
