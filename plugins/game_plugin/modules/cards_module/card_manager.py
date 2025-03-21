import random
from plugins.game_plugin.modules.cards_module.power_manager import PowerManager
from plugins.game_plugin.modules.game_play_module.game_manager import GameManager

class CardManager:
    def __init__(self, app_manager):
        self.app_manager = app_manager
        self.power_manager = PowerManager()
        self.deck = self.create_deck()

    def create_deck(self):
        """Creates a structured deck of cards with unique IDs but no initial powers."""
        suits = ['hearts', 'diamonds', 'clubs', 'spades']
        deck = []

        # Add numbered cards
        for rank in range(1, 11):
            for suit in suits:
                deck.append({
                    "card_id": f"{rank}_{suit}_{random.randint(1000, 9999)}",
                    "name": f"{rank} of {suit.capitalize()}",
                    "rank": rank,
                    "suit": suit,
                    "type": "regular",
                    "powers": [],  # No powers initially
                    "history": {"wins": 0, "uses": 0}
                })

        # Add special cards (Queens, Jacks, Kings, Jokers) with no initial powers
        special_cards = ["Joker", "Red King", "King", "Queen", "Jack"]
        for special in special_cards:
            for suit in suits:
                deck.append({
                    "card_id": f"{special.lower()}_{suit}_{random.randint(1000, 9999)}",
                    "name": f"{special} of {suit.capitalize()}",
                    "rank": 10,
                    "suit": suit,
                    "type": "special",
                    "powers": [],  # No powers initially
                    "history": {"wins": 0, "uses": 0}
                })

        random.shuffle(deck)
        return deck

    def draw_card(self):
        """Draws a card from the deck."""
        return self.deck.pop() if self.deck else None

    def play_card(self, player, card, game_state):
        """
        Handles when a player plays a card.
        If the card has a power, triggers it and updates power strength.
        Otherwise, moves the card to the discard pile.
        """
        if card["powers"]:
            for power in card["powers"]:
                power_instance = self.power_manager.get_power(power["power_id"], player)
                if power_instance:
                    success = power_instance.activate(game_state, player)
                    self.power_manager.update_power_strength(power, success)
                    return success

        # Move the played card to the discard pile
        game_manager.discard_card(player, card)

        return {"action": "play", "card": card["name"]}

    def reveal_card(self, player, target_player, position):
        """Reveals a card and stores it in AI knowledge if needed."""
        revealed_card = target_player.cards[position - 1]  # Position starts from 1
        player.add_known_card(revealed_card["card_id"], target_player.id, position)
        return {"action": "reveal", "revealed_card": revealed_card}
