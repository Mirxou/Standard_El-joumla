import logging
import json
import os
from datetime import datetime


class GamificationService:
    """
    The 'Game Engine' & 'Adaptive Intelligence' Service.
    Manages User XP and Tracks Behavior for Personalization.
    """

    def __init__(self, db_manager):
        self.db = db_manager
        self.tracking_file = "data/user_behavior.json"
        self._load_behavior_data()

    def _load_behavior_data(self):
        """Load behavior data from JSON"""
        self.behavior_data = {"actions": {}, "history": []}
        try:
            if os.path.exists(self.tracking_file):
                with open(self.tracking_file, "r", encoding="utf-8") as f:
                    self.behavior_data = json.load(f)
        except Exception:
            pass  # Fail silently

    def _save_behavior_data(self):
        """Save behavior data to JSON"""
        try:
            os.makedirs("data", exist_ok=True)
            with open(self.tracking_file, "w", encoding="utf-8") as f:
                json.dump(self.behavior_data, f, ensure_ascii=False, indent=2)
        except Exception:
            logging.getLogger(__name__).warning("Ignored exception in gamification_service.py")

    def track_action(self, action_name: str):
        """
        Track a user action for adaptive suggestions.
        """
        # 1. Update frequency count
        current_count = self.behavior_data["actions"].get(action_name, 0)
        self.behavior_data["actions"][action_name] = current_count + 1

        # 2. Add to history (keep last 100)
        entry = {"action": action_name, "timestamp": datetime.now().isoformat()}
        self.behavior_data["history"].append(entry)
        if len(self.behavior_data["history"]) > 100:
            self.behavior_data["history"].pop(0)

        self._save_behavior_data()

        # 3. Award XP (Gamification)
        return self.award_xp(None, action_name)

    def get_top_actions(self, limit=3):
        """Return the most frequently used actions"""
        # Sort actions by count descending
        sorted_actions = sorted(
            self.behavior_data["actions"].items(),
            key=lambda item: item[1],
            reverse=True,
        )
        return [action[0] for action in sorted_actions[:limit]]

    def get_user_progress(self, user_id):
        # Mocking data for now
        return {
            "level": 5,
            "xp": 450,
            "next_level_xp": 1000,
            "badges": ["Early Bird", "Fast Typer", "Closer"],
        }

    def award_xp(self, user_id, action):
        """
        Awards XP based on action type.
        """
        xp_map = {
            "login": 10,
            "create_invoice": 20,
            "close_deal": 50,
            "error_fix": 30,
            "view_report": 5,
            "check_stock": 5,
        }
        amount = xp_map.get(action, 5)
        return amount, f" gained {amount} XP!"

    def check_new_badges(self, user_id):
        return []

    def get_level_title(self, level):
        if level < 5:
            return "Novice"
        if level < 10:
            return "Apprentice"
        if level < 20:
            return "Expert"
        return "Master"
