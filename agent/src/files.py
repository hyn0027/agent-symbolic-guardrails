import random
import string
import os


def generate_random_file_path(base_path: str, extension: str):
    if not os.path.exists(base_path):
        os.makedirs(base_path)
    random_string = "".join(random.choices(string.ascii_letters + string.digits, k=8))
    filename = f"{random_string}.{extension}"
    file_path = os.path.join(base_path, filename)
    return file_path


def delete_file_if_exists(file_path: str):
    if os.path.exists(file_path):
        os.remove(file_path)
