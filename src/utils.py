from string import ascii_letters
from random import randint
import re
from typing import List


def encode_room(room_number: int) -> str:
    return f'secretsanta-{"".join([ascii_letters[randint(0, len(ascii_letters) - 1)] for i in range(12)])}-{room_number}'


def shufflePlayers(members: list):
# def shufflePlayers(members: List[List[str, bool, int]]):
    return members


def decode_room(invite_code: str) -> int:
    pattern = r'^secretsanta-(\w{12})-(\d+)$'

    match = re.match(pattern, invite_code)
    if match:
        return int(match.group(2))
    else:
        raise ValueError(f"{invite_code} is invalid")


import random

def split_couples(people):
    split_people = []
    for person in people:
        id = person[2]
        if person[1]:  # If the person is part of a couple
            names = person[0].split()
            for name in names:
                split_people.append((id, name, person[0]))
        else:
            split_people.append((id, person[0], None))
    return split_people

def create_pairings(people):
    people = split_couples(people)
    for i in range(100): # unable to connect people
        random.shuffle(people)
        pairings = []
        for i in range(len(people)):
            current = people[i]
            next_person = people[(i + 1) % len(people)]
            # Check if the current person is paired with their partner
            if current[2] is None or current[2] != next_person[2]:
                pairings.append([current[0], current[1], current[2] or current[1], next_person[1], next_person[2] or next_person[1]])
            else:
                break  # Reshuffle if a person is paired with their partner
        if len(pairings) == len(people):
            return pairings


if __name__ == '__main__':


    people = [
        ["Юра Неля", True, 123],
        ["Сер Діана", True, 124],
        ["Юля Діма", True, 125],
        ["Жора", False, 126]
    ]

    # split_people = split_couples(people)
    pairings = create_pairings(people)
    for pair in pairings:
        print(pair)

