from plugins.game_plugin.modules.leaderboard_module.leaderboard_module import LeaderboardModule
from plugins.game_plugin.modules.player_module.player_manager import PlayerManager
from plugins.game_plugin.modules.cards_module.card_manager import CardManager
from plugins.game_plugin.modules.game_play_module.game_manager import GameManager


from tools.logger.custom_logging import custom_log


class GamePlugin:
    def initialize(self, app_manager):
        """
        Initialize the GamePlugin with AppManager.
        :param app_manager: AppManager - The main application manager.
        """
        custom_log("Initializing GamePlugin...")

        try:
            # Register modules
            app_manager.module_manager.register_module(
                "leaderboard_module", 
                LeaderboardModule, 
                app_manager=app_manager
            )
            app_manager.module_manager.register_module(
                "player_module",
                PlayerManager,
                app_manager=app_manager
            )
            app_manager.module_manager.register_module(
                "cards_module",
                CardManager,
                app_manager=app_manager
            )
            app_manager.module_manager.register_module(
                "game_play_module",
                GameManager,
                app_manager=app_manager
            )

        except Exception as e:
            custom_log(f"Error initializing GamePlugin: {e}")
            raise

    def setup_game(self, app_manager, user_id, username, game_id):
        """
        Sets up a new game with a single player.
        :param app_manager: AppManager instance
        :param user_id: Unique identifier for the player
        :param username: Display name for the player
        :param game_id: Unique identifier for the game session
        :return: Game session details or error message
        """
        try:
            custom_log(f"Setting up new game {game_id} for player {username} ({user_id})")

            # Get required modules
            player_manager = app_manager.module_manager.get_module("player_module")
            game_manager = app_manager.module_manager.get_module("game_play_module")

            # Create the player
            player = player_manager.create_player(user_id, username)
            if not player:
                return {"error": "Failed to create player"}

            # Create the game with the player
            game_state = game_manager.create_game(game_id, [user_id])
            if "error" in game_state:
                return game_state

            return {
                "game_id": game_id,
                "player": {
                    "id": user_id,
                    "username": username,
                    "cards": player.cards
                },
                "game_state": game_state
            }

        except Exception as e:
            custom_log(f"Error setting up game: {e}")
            return {"error": str(e)}

    def start_game(self, app_manager, player_ids):
        """
        Starts a new game session with the given players.
        :param player_ids: List of player IDs
        :return: Game session details
        """
        try:
            custom_log("Starting a new game session...")

            player_manager = app_manager.module_manager.get_module("player_module")
            card_manager = app_manager.module_manager.get_module("cards_module")

            # Create players
            players = {pid: player_manager.create_player(pid) for pid in player_ids}

            # Shuffle and distribute cards
            for player in players.values():
                for _ in range(4):  # Each player gets 4 cards
                    player.cards.append(card_manager.draw_card())

            game_state = {
                "players": {pid: player.cards for pid, player in players.items()},
                "deck_size": len(card_manager.deck)
            }

            custom_log(f"Game started with players: {list(players.keys())}")
            return game_state

        except Exception as e:
            custom_log(f"Error starting game: {e}")
            return {"error": str(e)}
