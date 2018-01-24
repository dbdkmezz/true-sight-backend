import random
import string


def random_string(length=10, characters=string.ascii_letters):
    return u''.join(random.choice(characters) for x in range(length))


def random_bool():
    return random.choice([True, False])
