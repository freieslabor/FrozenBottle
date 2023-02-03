import random

class GameController:
    commands = (
        1, 1, 1, 1, 1, 1, 1, 1, 1,
        5, 5, 5, 5, 5, 5, 5, 5,
        3, 3, 3, 3, 3, 3, 3, 3,
    )
    def __init__(self):
        self.command = None
        self.counter = 0

    def start(self):
        self.cmd_index = 0

    def getch(self):
        self.counter += 1
        if self.command is None or self.counter == 4:
            self.counter = 0
            self.command = random.randint(0, 5)
        return self.command

        if self.cmd_index == len(GameController.commands) - 1:
            self.cmd_index = 0

        cmd = GameController.commands[self.cmd_index]
        self.cmd_index = self.cmd_index + 1
        return cmd
