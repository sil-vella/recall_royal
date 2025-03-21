class JackSwap:
    ID = "jack_swap"

    def activate(self, game_state, player):
        """Allows the player to swap two cards."""
        return {"action": "swap", "count": 1}
