from controllers.ChestController import ChestController
from tokens.Token import Token
import random


class ChestToken(Token):
    def __init__(self, item, difficulty):
        self.item = item
        self.image = 'images/items/chest.png'
        self.shortened = False
        self.already_interacted = False
        self.code = [random.choice(['a', 'd']) for _ in range(difficulty)]

    def interact(self, character_info=None):
        controller = ChestController(self)
        result = controller.start_chest_view()
        if result:
            character_info.exp += 5
        self.already_interacted = True
        return result
