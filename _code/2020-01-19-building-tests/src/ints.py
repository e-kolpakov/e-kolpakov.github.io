def multiply(i1: int, i2: int) -> int:
    return i1 * i2


def self_test():
    assert(multiply(1, 2) == 2)
    assert(multiply(3, 4) == 12)
    print("Tests passed")