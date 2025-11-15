"""Configuration management for DAGLinter."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


@dataclass
class Config:
    """Application configuration."""

    # Rule configurations
    rules: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # File/directory exclusions
    exclude: List[str] = field(default_factory=list)

    # File/directory inclusions
    include: List[str] = field(default_factory=list)

    # Output settings
    output_format: str = "terminal"
    output_file: Optional[Path] = None
    color: str = "auto"  # auto, always, never
    verbose: bool = False
    quiet: bool = False

    # Performance settings
    max_workers: int = 1  # Single-threaded for MVP
    timeout_per_file: int = 30

    @classmethod
    def from_file(cls, config_path: Path) -> "Config":
        """
        Load configuration from YAML file.

        Args:
            config_path: Path to .daglinter.yml

        Returns:
            Config instance
        """
        try:
            with open(config_path, "r") as f:
                data = yaml.safe_load(f) or {}
        except Exception as e:
            raise ValueError(f"Failed to load config from {config_path}: {e}")

        return cls(
            rules=data.get("rules", {}),
            exclude=data.get("exclude", []),
            include=data.get("include", []),
            output_format=data.get("output", {}).get("format", "terminal"),
            color=data.get("output", {}).get("color", "auto"),
            verbose=data.get("output", {}).get("verbose", False),
            quiet=data.get("output", {}).get("quiet", False),
            max_workers=data.get("performance", {}).get("max_workers", 1),
            timeout_per_file=data.get("performance", {}).get("timeout_per_file", 30),
        )

    @classmethod
    def default(cls) -> "Config":
        """Create default configuration."""
        return cls(
            exclude=["**/tests/**", "**/__pycache__/**", "*.pyc"],
            rules={
                "heavy-imports": {
                    "enabled": True,
                    "severity": "error",
                    "libraries": [
                        "pandas",
                        "numpy",
                        "sklearn",
                        "tensorflow",
                        "torch",
                        "matplotlib",
                        "seaborn",
                        "plotly",
                    ],
                },
                "db-connections": {"enabled": True, "severity": "error"},
                "missing-docs": {
                    "enabled": True,
                    "severity": "warning",
                    "min_length": 20,
                },
                "complex-dependencies": {
                    "enabled": True,
                    "severity": "warning",
                    "max_fan_out": 10,
                    "max_fan_in": 10,
                },
            },
        )

    def merge_cli_args(self, **kwargs: Any) -> "Config":
        """
        Merge CLI arguments into config (CLI takes precedence).

        Args:
            **kwargs: CLI arguments

        Returns:
            New Config with merged values
        """
        # Create a copy and override with CLI args
        config_dict = {
            "rules": self.rules.copy(),
            "exclude": self.exclude.copy(),
            "include": self.include.copy(),
            "output_format": self.output_format,
            "output_file": self.output_file,
            "color": self.color,
            "verbose": self.verbose,
            "quiet": self.quiet,
            "max_workers": self.max_workers,
            "timeout_per_file": self.timeout_per_file,
        }

        for key, value in kwargs.items():
            if value is not None:
                config_dict[key] = value

        return Config(**config_dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "rules": self.rules,
            "exclude": self.exclude,
            "include": self.include,
            "output": {
                "format": self.output_format,
                "color": self.color,
                "verbose": self.verbose,
                "quiet": self.quiet,
            },
            "performance": {
                "max_workers": self.max_workers,
                "timeout_per_file": self.timeout_per_file,
            },
        }


class ConfigLoader:
    """Discovers and loads configuration files."""

    CONFIG_FILENAMES = [".daglinter.yml", ".daglinter.yaml"]

    @staticmethod
    def discover_config(start_path: Path) -> Optional[Path]:
        """
        Search for config file from start_path up to root.

        Args:
            start_path: Directory to start search

        Returns:
            Path to config file or None
        """
        current = start_path.resolve()

        while True:
            for filename in ConfigLoader.CONFIG_FILENAMES:
                config_path = current / filename
                if config_path.exists():
                    return config_path

            # Move up one directory
            parent = current.parent
            if parent == current:  # Reached root
                break
            current = parent

        return None

    @staticmethod
    def load(config_path: Optional[Path] = None) -> Config:
        """
        Load configuration, with fallback to defaults.

        Args:
            config_path: Explicit config path or None to discover

        Returns:
            Config instance
        """
        if config_path and config_path.exists():
            return Config.from_file(config_path)

        # Auto-discover
        discovered = ConfigLoader.discover_config(Path.cwd())
        if discovered:
            return Config.from_file(discovered)

        # Fall back to defaults
        return Config.default()
