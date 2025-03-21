import importlib
import os
import time

class PowerManager:
    def __init__(self):
        self.powers = {}
        self.load_powers()

    def load_powers(self, power_folder="plugins/game_plugin/modules/cards_module/powers"):
        """Dynamically loads all power modules."""
        try:
            if not os.path.exists(power_folder):
                print(f"Warning: Power folder {power_folder} does not exist.")
                return

            for file in os.listdir(power_folder):
                if file.endswith(".py") and file != "__init__.py":
                    module_name = f"{power_folder}.{file[:-3]}"
                    module = importlib.import_module(module_name)
                    power_class = getattr(module, file[:-3].capitalize(), None)
                    if power_class:
                        self.powers[power_class.ID] = power_class  # Store class reference
        except Exception as e:
            print(f"Warning: Failed to load powers: {e}")

    def get_power(self, power_id, player):
        """Retrieves and initializes a power instance for a player, checking expiration."""
        if power_id in self.powers:
            power = self.powers[power_id](player)
            return self.check_expiration(power, player)
        return None

    def check_expiration(self, power, player):
        """
        Checks if a power is expired due to time, use limit, or gameplay events.
        """
        current_time = time.time()

        # Remove power if it has expired based on time
        if "expiration_time" in power and power["expiration_time"] and power["expiration_time"] < current_time:
            self.remove_power(player, power["power_id"])
            return None

        # Remove power if it has exceeded its allowed uses
        if "uses_left" in power and power["uses_left"] == 0:
            self.remove_power(player, power["power_id"])
            return None

        # Remove power based on gameplay events
        if self.check_gameplay_expiration(player, power):
            self.remove_power(player, power["power_id"])
            return None

        return power

    def check_gameplay_expiration(self, player, power):
        """
        Checks if a power should expire due to gameplay events (e.g., losing 3 games in a row).
        """
        if "loss_streak" in player and player["loss_streak"] >= 3:
            return True  # Remove power after 3 consecutive losses

        if "unused_games" in power and power["unused_games"] >= 5:
            return True  # Remove power if not used in 5 games

        return False

    def update_power_strength(self, power, successful_execution):
        """
        Strengthens or weakens a power based on success or failure.
        """
        if successful_execution:
            power["usage_history"]["successes"] += 1
            if power["strength"] < power["max_strength"]:
                power["strength"] += 1
        else:
            power["usage_history"]["failures"] += 1
            if power["strength"] > 1:
                power["strength"] -= 1

        # Decrease remaining uses
        if "uses_left" in power and power["uses_left"] > 0:
            power["uses_left"] -= 1

        # Track games where the power was unused
        if "unused_games" in power:
            power["unused_games"] += 1

        return power

    def remove_power(self, player, power_id):
        """Removes a power from a player's active powers."""
        if player:
            player.powers = [p for p in player.powers if p["power_id"] != power_id]
