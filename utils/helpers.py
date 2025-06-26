import random
import string


def generate_random_code(length=8):
    """
    Helper function that generates a random code of 8 characters + numbers.
    """
    characters = string.ascii_uppercase + string.digits
    return "".join(random.choice(characters) for i in range(length))
