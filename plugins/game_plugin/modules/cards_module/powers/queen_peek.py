class QueenPeek:
    ID = "queen_peek"

    def activate(self, game_state, player):
        """Allows a player to peek at one card from any player."""
        return {"action": "peek", "count": 1}
