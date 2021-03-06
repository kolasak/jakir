import json

import numpy as np

from character.items.BoostItem import BoostItem
from character.items.Key import Key
from character.items.HealingItem import HealingItem
from fields import *
# Returns map as array of objects.
# For these who dont know np.array is just array in C or Java, so you can get or set element by index/es.
from gameplay.Question import Question
from gameplay.QuestionContainer import QuestionContainer
from tokens.BossToken import BossToken
from tokens.ChestToken import ChestToken
from tokens.MonsterToken import MonsterToken
from tokens.NpcToken import NpcToken

MAX_QUESTION_ANSWERS = 5


def load_multi_room_map(json_path='config.json'):
    with open(json_path) as json_file:
        json_data = json.load(json_file)
        json_file.close()

    map_height = len(json_data)
    map_width = len(json_data[0])
    game_map = np.empty((map_height, map_width), dtype=object)
    passages_map = np.empty((map_height, map_width), dtype=object)

    for row_of_rooms in json_data:
        for room in row_of_rooms:
            room_map, passages = parse_map(room['map'])
            room_map = parse_monsters(room_map, room['monsters'])
            room_map = parse_npcs(room_map, room['npcs'])
            room_map = parse_items(room_map, room['items'])
            room_map = parse_chests(room_map, room['chests'])
            x, y = room["position"]
            passages_map[x][y] = passages
            game_map[x][y] = room_map
    bind_passages(game_map, passages_map, map_height, map_width,
                  json_data[0][0]['map']['height'], json_data[0][0]['map']['width'])
    return game_map


def bind_passages(game_map, passages_map, map_height, map_width, room_height, room_width):
    reverse_passage_type = {
        "N": "S",
        "S": "N",
        "W": "E",
        "E": "W"
    }
    passage_vector = {
        "N": (1, 0),
        "S": (-1, 0),
        "W": (0, -1),
        "E": (0, 1)
    }
    for current_room_position_x in range(map_height):
        for current_room_position_y in range(map_width):
            passages = passages_map[current_room_position_x][current_room_position_y]
            for passage in passages:
                passage_type = get_passage_type(passage, room_height, room_width)
                next_room_position_x, next_room_position_y = passage_vector[passage_type]
                next_room_position_x += current_room_position_x
                next_room_position_y += current_room_position_y
                for next_passage in passages_map[next_room_position_x][next_room_position_y]:
                    if get_passage_type(next_passage, room_height, room_width) == reverse_passage_type[passage_type]:
                        current_room_x, current_room_y = passage
                        next_room_x, next_room_y = next_passage
                        next_vector_x, next_vector_y = passage_vector[passage_type]
                        next_room_x += next_vector_x
                        next_room_y += next_vector_y
                        game_map[current_room_position_x][current_room_position_y][current_room_y][current_room_x]\
                            .bind(game_map[next_room_position_x][next_room_position_y], (next_room_y, next_room_x))


def get_passage_type(passage, room_height, room_width):
    x, y = passage
    if x == 0: return "S"
    if y == 0: return "W"
    if x == room_height - 1: return "N"
    if y == room_width - 1: return "E"
    return None


def load_map(json_path='config.json'):
    with open(json_path) as json_file:
        json_data = json.load(json_file)
        json_file.close()

    json_stages = json_data['stages']
    stages = []
    for json_stage in json_stages:  # we allow user to define as many stages as he want, and we load each one
        game_map, _ = parse_map(json_stage['map'])
        game_map = parse_monsters(game_map, json_stage['monsters'])
        game_map = parse_npcs(game_map, json_stage['npcs'])
        game_map = parse_items(game_map, json_stage['items'])
        game_map = parse_chests(game_map, json_stage['chests'])
        stages.append(game_map)
    return stages


def parse_questions(riddles):
    for riddle in riddles:
        question = Question(riddle['question'])
        for answer in riddle['answers']:
            Question.add_answer(question, answer)
            if answer == riddle['correct']:
                Question.add_correct(question, answer)
        QuestionContainer.getInstance().add_question(question)


def load_questions(json_path='riddles.json'):
    question_container = QuestionContainer.getInstance()
    with open(json_path) as json_file:
        json_data = json.load(json_file)
        json_file.close()
    parse_questions(json_data['riddles'])
    return question_container


def parse_map(json_map):
    width = json_map['width']
    height = json_map['height']
    game_map = np.empty((width, height), dtype=Field)

    row_counter = 0
    passages = []
    for json_row in json_map['map']:
        field_counter = 0
        for character in json_row:
            field_class = CHARACTER_TO_FIELD[character]
            game_map[field_counter][row_counter] = field_class()
            if character == 'P':
                passages.append((row_counter, field_counter))
            field_counter += 1
        row_counter += 1
    return game_map, passages


def parse_monsters(map, json_monsters):
    for monster in json_monsters['basic']:
        new_monster = MonsterToken(monster['hp'], monster['strength'], monster['image'], monster['xp'])
        new_monster.item = _get_item(map, monster['item'])
        map[monster['x']][monster['y']].put_token(new_monster)
    for boss in json_monsters['bosses']:
        new_boss = BossToken(boss['hp'], boss['strength'], boss['image'], boss['xp'])
        new_boss.item = _get_item(map, boss['item'])
        map[boss['x']][boss['y']].put_token(new_boss)
    return map


def parse_items(map, json_items):
    for key in json_items['keys']:
        key_obj = Key()
        map[key['x']][key['y']].put_item(key_obj)
        gate = map[key['gate_x']][key['gate_y']]
        if isinstance(gate, GateField):
            gate.set_key_id(key_obj.id)

    for item in json_items['boost']:
        item_obj = BoostItem(item['name'], item['strength'], item['image'])
        map[item['x']][item['y']].put_item(item_obj)

    for item in json_items['potions']:
        item_obj = HealingItem(item['name'], item['healing'], item['image'])
        map[item['x']][item['y']].put_item(item_obj)

    return map


def parse_chests(map, json_chests):
    for chest in json_chests:
        item = _get_item(map, chest['item'])
        new_chest = ChestToken(item, chest['difficulty'])
        map[chest['x']][chest['y']].put_token(new_chest)
    return map


def parse_npcs(map, json_npcs):
    for npc in json_npcs:
        quest_item = _get_item(map, npc['quest']['item'])
        new_npc = NpcToken(npc['name'], npc['image'], npc['attributes'], npc['quest'], quest_item, npc['dialog'])
        map[npc['x']][npc['y']].put_token(new_npc)
    return map


def _get_item(map, item):
    item_obj = None
    if item is not None:
        if item['type'] == 'boost':
            item_obj = BoostItem(item['name'], item['strength'], item['image'])
        elif item['type'] == 'key':
            item_obj = Key()
            gate = map[item['gate_x']][item['gate_y']]
            gate.set_key_id(item_obj.id)
        elif item['type'] == 'potion':
            item_obj = HealingItem(item['name'], item['healing'], item['image'])
    return item_obj
