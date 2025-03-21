class DoublePeek:
    ID = "double_peek"

    def __init__(self, player):
        self.player = player

    def activate(self, game_state):
        """Allows the player to peek at two cards instead of one."""
        return {"action": "peek", "count": 2}
