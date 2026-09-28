"""
Feature Flags System — Standard El-Joumla ERP
Enables/disables features dynamically without redeployment.
Supports: per-user, per-environment, percentage rollout, kill switches.

Usage:
    from src.core.feature_flags import FeatureFlags

    # Check if feature is enabled
    if FeatureFlags.is_enabled("new_dashboard"):
        show_new_dashboard()

    # Check with user context (for per-user rollout)
    if FeatureFlags.is_enabled("new_pricing", user_id=42):
        apply_new_pricing()
"""

import json
import logging
import os
import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class FlagState(Enum):
    """Feature flag states."""
    ON = "on"
    OFF = "off"
    PERCENTAGE = "percentage"   # Rollout to X% of users
    ENVIRONMENT = "environment"  # Only in specific environments
    USER_LIST = "user_list"     # Only for specific user IDs
    SCHEDULED = "scheduled"     # Enable after a specific date


@dataclass
class FeatureFlag:
    """A single feature flag definition."""
    name: str
    description: str = ""
    state: FlagState = FlagState.OFF
    percentage: float = 0.0          # 0-100
    environments: list = field(default_factory=list)  # e.g., ["staging", "production"]
    user_ids: list = field(default_factory=list)      # Specific user IDs
    enable_after: Optional[str] = None  # ISO datetime string
    kill_switch: bool = False         # If True, always OFF regardless of other settings
    metadata: dict = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "state": self.state.value,
            "percentage": self.percentage,
            "environments": self.environments,
            "user_ids": self.user_ids,
            "enable_after": self.enable_after,
            "kill_switch": self.kill_switch,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FeatureFlag":
        data = dict(data)  # copy
        if "state" in data and isinstance(data["state"], str):
            try:
                data["state"] = FlagState(data["state"])
            except ValueError:
                data["state"] = FlagState.OFF
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# ── Default Feature Flags ─────────────────────────────────────────────────
DEFAULT_FLAGS: list[dict] = [
    {
        "name": "new_dashboard",
        "description": "Redesigned dashboard with real-time charts",
        "state": "environment",
        "environments": ["staging", "development"],
    },
    {
        "name": "new_pricing_engine",
        "description": "Dynamic pricing engine v2 with ML recommendations",
        "state": "percentage",
        "percentage": 10.0,
        "environments": ["staging", "production"],
    },
    {
        "name": "ai_predictions",
        "description": "AI-powered sales predictions and inventory optimization",
        "state": "on",
        "environments": ["staging", "production", "development"],
    },
    {
        "name": "wholesale_mode",
        "description": "Wholesale pricing and bulk order management",
        "state": "on",
    },
    {
        "name": "multi_warehouse",
        "description": "Multi-warehouse support with transfer logistics",
        "state": "on",
    },
    {
        "name": "payment_plans",
        "description": "Installment payment plans for customers",
        "state": "on",
    },
    {
        "name": "advanced_analytics",
        "description": "Advanced BI analytics and reporting dashboards",
        "state": "environment",
        "environments": ["staging"],
    },
    {
        "name": "canary_api_v2",
        "description": "API v2 endpoints with new response format",
        "state": "percentage",
        "percentage": 5.0,
        "environments": ["production"],
    },
    {
        "name": "websocket_realtime",
        "description": "Real-time updates via WebSocket",
        "state": "on",
    },
    {
        "name": "experimental_rpa",
        "description": "Robotic Process Automation features",
        "state": "off",
    },
    {
        "name": "loyalty_program",
        "description": "Customer loyalty points and rewards",
        "state": "percentage",
        "percentage": 50.0,
    },
    {
        "name": "carbon_tracking",
        "description": "Carbon footprint tracking for products",
        "state": "off",
    },
]


class FeatureFlags:
    """
    Thread-safe feature flags manager.
    Reads from: 1) JSON config file, 2) environment variables, 3) defaults.
    Environment override: FEATURE_<NAME>=on/off
    """

    _instance: Optional["FeatureFlags"] = None
    _lock = threading.Lock()

    def __init__(self, config_path: Optional[str] = None):
        self._flags: dict[str, FeatureFlag] = {}
        self._config_path = config_path or os.environ.get(
            "FEATURE_FLAGS_PATH",
            str(Path(__file__).resolve().parent.parent.parent / "config" / "feature_flags.json")
        )
        self._current_env = os.environ.get("ENVIRONMENT", "development")
        self._load_flags()

    @classmethod
    def get_instance(cls, config_path: Optional[str] = None) -> "FeatureFlags":
        """Get or create the singleton instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(config_path)
        return cls._instance

    @classmethod
    def reset(cls):
        """Reset singleton (for testing)."""
        with cls._lock:
            cls._instance = None

    def _load_flags(self):
        """Load flags from config file and defaults."""
        # Start with defaults
        for flag_data in DEFAULT_FLAGS:
            flag = FeatureFlag.from_dict(flag_data)
            self._flags[flag.name] = flag

        # Override from config file
        try:
            config_path = Path(self._config_path)
            if config_path.exists():
                with open(config_path, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                if isinstance(saved, dict):
                    for name, flag_data in saved.items():
                        if isinstance(flag_data, dict):
                            flag_data["name"] = name
                            self._flags[name] = FeatureFlag.from_dict(flag_data)
                logger.info("Loaded %d feature flags from %s", len(self._flags), config_path)
        except Exception as e:
            logger.warning("Failed to load feature flags from %s: %s", self._config_path, e)

        # Override from environment variables (highest priority)
        for name, flag in self._flags.items():
            env_key = f"FEATURE_{name.upper()}"
            env_val = os.environ.get(env_key)
            if env_val is not None:
                if env_val.lower() in ("on", "true", "1", "yes"):
                    flag.state = FlagState.ON
                elif env_val.lower() in ("off", "false", "0", "no"):
                    flag.state = FlagState.OFF
                logger.debug("Feature flag '%s' overridden by env %s=%s", name, env_key, env_val)

    def save_flags(self):
        """Save current flags to config file."""
        try:
            config_path = Path(self._config_path)
            config_path.parent.mkdir(parents=True, exist_ok=True)
            data = {name: flag.to_dict() for name, flag in self._flags.items()}
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info("Saved %d feature flags to %s", len(self._flags), config_path)
        except Exception as e:
            logger.warning("Failed to save feature flags: %s", e)

    def is_enabled(
        self,
        name: str,
        user_id: Optional[int] = None,
        default: bool = False,
    ) -> bool:
        """
        Check if a feature flag is enabled.

        Args:
            name: Feature flag name
            user_id: Optional user ID for per-user rollout
            default: Default value if flag doesn't exist

        Returns:
            True if the feature should be active for this context
        """
        flag = self._flags.get(name)
        if flag is None:
            return default

        # Kill switch overrides everything
        if flag.kill_switch:
            return False

        if flag.state == FlagState.ON:
            return True

        if flag.state == FlagState.OFF:
            return False

        if flag.state == FlagState.ENVIRONMENT:
            return self._current_env in flag.environments

        if flag.state == FlagState.PERCENTAGE:
            if self._current_env == "development":
                return True  # Always on in dev
            if self._current_env not in flag.environments and flag.environments:
                return False
            # Deterministic rollout based on user_id or flag name hash
            if user_id is not None:
                bucket = (user_id * 31 + hash(name)) % 100
                return bucket < flag.percentage
            # No user context — use percentage as probability
            return flag.percentage >= 100.0

        if flag.state == FlagState.USER_LIST:
            return user_id is not None and user_id in flag.user_ids

        if flag.state == FlagState.SCHEDULED:
            if flag.enable_after:
                try:
                    enable_time = datetime.fromisoformat(flag.enable_after)
                    return datetime.utcnow() >= enable_time
                except (ValueError, TypeError):
                    return False
            return False

        return default

    def set_flag(
        self,
        name: str,
        state: Optional[FlagState] = None,
        percentage: Optional[float] = None,
        environments: Optional[list] = None,
        description: Optional[str] = None,
        kill_switch: Optional[bool] = None,
    ) -> FeatureFlag:
        """Update a feature flag."""
        flag = self._flags.get(name)
        if flag is None:
            flag = FeatureFlag(name=name, description=description or "")

        if state is not None:
            flag.state = state
        if percentage is not None:
            flag.percentage = percentage
        if environments is not None:
            flag.environments = environments
        if description is not None:
            flag.description = description
        if kill_switch is not None:
            flag.kill_switch = kill_switch

        flag.updated_at = datetime.utcnow().isoformat()
        self._flags[name] = flag
        return flag

    def kill(self, name: str) -> None:
        """Emergency disable a feature flag (kill switch)."""
        flag = self._flags.get(name)
        if flag:
            flag.kill_switch = True
            flag.updated_at = datetime.utcnow().isoformat()
            logger.warning("🚨 KILL SWITCH activated for feature: %s", name)

    def revive(self, name: str) -> None:
        """Remove kill switch from a feature flag."""
        flag = self._flags.get(name)
        if flag:
            flag.kill_switch = False
            flag.updated_at = datetime.utcnow().isoformat()

    def get_all_flags(self) -> dict[str, dict]:
        """Get all flag definitions as dicts."""
        return {name: flag.to_dict() for name, flag in self._flags.items()}

    def get_enabled_flags(self, user_id: Optional[int] = None) -> list[str]:
        """Get list of currently enabled flag names."""
        return [name for name in self._flags if self.is_enabled(name, user_id=user_id)]

    def reload(self) -> None:
        """Reload flags from config file."""
        with self._lock:
            self._flags.clear()
            self._load_flags()


# ── Convenience Functions ─────────────────────────────────────────────────

def is_enabled(name: str, user_id: Optional[int] = None, default: bool = False) -> bool:
    """Quick check if a feature flag is enabled."""
    return FeatureFlags.get_instance().is_enabled(name, user_id=user_id, default=default)


def set_flag(name: str, **kwargs) -> FeatureFlag:
    """Quick update a feature flag."""
    return FeatureFlags.get_instance().set_flag(name, **kwargs)


def kill(name: str) -> None:
    """Emergency disable a feature."""
    FeatureFlags.get_instance().kill(name)
