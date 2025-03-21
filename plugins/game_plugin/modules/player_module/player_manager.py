class PlayerManager:
    def __init__(self, app_manager):
        self.app_manager = app_manager
        self.players = {}

    def create_player(self, player_id, username, is_computer=False, difficulty="medium"):
        """Creates a new player (human or AI) and registers them."""
        if player_id not in self.players:
            self.players[player_id] = Player(player_id, username, is_computer, difficulty)
        return self.players[player_id]

    def get_player(self, player_id):
        """Retrieves a player object."""
        return self.players.get(player_id)


class Player:
    def __init__(self, player_id, username, is_computer=False, difficulty="medium"):
        self.id = player_id
        self.username = username
        self.is_computer = is_computer
        self.difficulty = difficulty  # "easy", "medium", "hard"
        self.cards = []  # Player's hand
        self.known_cards = []  # AI's memory of revealed cards
        self.unknown_cards = []  # AI's unknown hand cards
        self.known_from_others = []  # AI's knowledge of opponent cards

    def set_difficulty(self, difficulty):
        """Sets AI difficulty dynamically."""
        self.difficulty = difficulty

    def add_known_card(self, card_id, owner_id, position):
        """Stores an opponent's revealed card in AI knowledge."""
        if self.is_computer or self.id != owner_id:
            self.known_from_others.append({
                "card_id": card_id,
                "owner_id": owner_id,
                "position": position
            })