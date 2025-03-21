import random

class GameManager:
    def __init__(self, app_manager):
        self.app_manager = app_manager
        self.card_manager = app_manager.module_manager.get_module("cards_module")
        self.power_manager = app_manager.module_manager.get_module("power_module")
        self.active_games = {}  # Store active game instances by game_id

    def create_game(self, game_id, player_ids):
        """Creates a new game session and stores it in active_games."""
        if game_id in self.active_games:
            return {"error": "Game ID already exists!"}

        # Create players
        player_manager = self.app_manager.module_manager.get_module("player_module")
        players = {pid: player_manager.create_player(pid) for pid in player_ids}

        # Shuffle and distribute cards
        for player in players.values():
            for _ in range(4):  # Each player gets 4 cards
                player.cards.append(self.card_manager.draw_card())

        # Store game state
        self.active_games[game_id] = {
            "game_id": game_id,
            "players": players,
            "deck_size": len(self.card_manager.deck),
            "discard_pile": []
        }

        return self.active_games[game_id]

    def get_game_instance(self, game_id):
        """Retrieves an active game instance by game_id."""
        return self.active_games.get(game_id, {"error": "Game not found!"})


    def discard_card(self, player, card):
        """
        Places a card in the discard pile.
        """
        print(f"{player.username} discards {card['card_id']}")
        self.discard_pile.append(card)

    def draw_from_discard_pile(self, player):
        """
        Allows a player to draw from the discard pile.
        If they do, all other players will know this card.
        """
        if not self.discard_pile:
            return {"error": "Discard pile is empty"}

        drawn_card = self.discard_pile.pop()
        player.cards.append(drawn_card)
        print(f"{player.username} draws {drawn_card['card_id']} from discard pile.")

        # Add this card to the "known_from_others" list for all players
        for other_player in self.players.values():
            if other_player.id != player.id:
                other_player.add_known_card(drawn_card["card_id"], player.id, len(player.cards))

        return {"action": "draw_discard", "card": drawn_card["card_id"]}

    def process_computer_turn(self, ai_player):
        """Handles the AI player's turn based on difficulty level."""
        print(f"AI {ai_player.username} ({ai_player.difficulty} mode) is taking a turn...")

        # EASY MODE - Plays randomly
        if ai_player.difficulty == "easy":
            return self.easy_ai_turn(ai_player)

        # MEDIUM MODE - Uses some strategy
        if ai_player.difficulty == "medium":
            return self.medium_ai_turn(ai_player)

        # HARD MODE - Fully strategic play
        if ai_player.difficulty == "hard":
            return self.hard_ai_turn(ai_player)

    def easy_ai_turn(self, ai_player):
        """AI makes random moves with little strategy."""
        if random.random() < 0.5:
            new_card = self.card_manager.draw_card()
            print(f"AI {ai_player.username} draws a new card: {new_card['card_id']}")
            return {"action": "draw", "card": new_card["card_id"]}

        random_card = random.choice(ai_player.cards)
        print(f"AI {ai_player.username} randomly plays {random_card['card_id']}")
        return self.play_card(ai_player, random_card)

    def medium_ai_turn(self, ai_player):
        """AI makes moves with basic strategy (tracks known cards, avoids high-value cards)."""
        best_card = self.get_best_card_to_play(ai_player, prefer_low=True)

        if best_card:
            print(f"AI {ai_player.username} plays {best_card['card_id']} (Strategic)")
            return self.play_card(ai_player, best_card)

        return self.easy_ai_turn(ai_player)  # Fallback to random play if no strategy available

    def hard_ai_turn(self, ai_player):
        """AI makes moves with advanced strategy (fully tracks opponents, optimizes plays)."""
        best_card = self.get_best_card_to_play(ai_player, prefer_low=True, track_opponents=True)

        if best_card:
            print(f"AI {ai_player.username} plays {best_card['card_id']} (Optimized Strategy)")
            return self.play_card(ai_player, best_card)

        return self.medium_ai_turn(ai_player)  # Fallback to medium strategy if no perfect move

    def get_best_card_to_play(self, ai_player):
        """AI picks the best card based on known strategy."""
        # Prioritize playing a known low-value card
        for known_card in ai_player.known_from_others:
            if known_card["card_id"] in [card["card_id"] for card in ai_player.cards]:
                return known_card  # Play a known safe card first

        # If no known card, pick the lowest card in hand
        sorted_cards = sorted(ai_player.cards, key=lambda c: int(c["card_id"].split("_")[0]) if c["card_id"][0].isdigit() else 10)
        return sorted_cards[0] if sorted_cards else None


    def play_card(self, ai_player, card):
        """Executes AI playing a card."""
        print(f"AI {ai_player.username} plays {card['card_id']}")

        # If the card has a power, activate it
        power_instance = self.power_manager.get_power(card["card_id"], ai_player)
        if power_instance:
            print(f"AI {ai_player.username} activates power {power_instance.ID}")
            return {"action": "power", "result": power_instance.activate({}, ai_player)}

        ai_player.cards.remove(card)
        return {"action": "play", "card": card["card_id"]}
