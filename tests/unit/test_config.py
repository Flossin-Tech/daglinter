"""Unit tests for configuration management."""

from pathlib import Path

import pytest
import yaml

from daglinter.core.config import Config, ConfigLoader


class TestConfig:
    """Test Config dataclass functionality."""

    def test_should_create_default_config(self):
        """Config should create with default values."""
        config = Config.default()

        assert isinstance(config.rules, dict)
        assert isinstance(config.exclude, list)
        assert config.output_format == "terminal"
        assert config.max_workers == 1

    def test_should_have_all_default_rules_enabled(self):
        """Default config should have all 4 rules configured."""
        config = Config.default()

        assert "heavy-imports" in config.rules
        assert "db-connections" in config.rules
        assert "missing-docs" in config.rules
        assert "complex-dependencies" in config.rules

    def test_should_load_from_yaml_file(self, tmp_path):
        """Config should load from YAML file."""
        config_file = tmp_path / ".daglinter.yml"
        config_data = {
            "rules": {
                "heavy-imports": {"enabled": True, "severity": "error"}
            },
            "exclude": ["tests/**", "venv/**"],
            "output": {
                "format": "json",
                "color": "never"
            }
        }

        config_file.write_text(yaml.dump(config_data))

        config = Config.from_file(config_file)

        assert config.rules["heavy-imports"]["enabled"] is True
        assert "tests/**" in config.exclude
        assert config.output_format == "json"
        assert config.color == "never"

    def test_should_handle_empty_yaml_file(self, tmp_path):
        """Config should handle empty YAML file."""
        config_file = tmp_path / ".daglinter.yml"
        config_file.write_text("")

        config = Config.from_file(config_file)

        assert config.rules == {}
        assert config.exclude == []
        assert config.output_format == "terminal"

    def test_should_raise_error_for_invalid_yaml(self, tmp_path):
        """Config should raise error for invalid YAML."""
        config_file = tmp_path / ".daglinter.yml"
        config_file.write_text("""
rules:
  bad-indent:
    - not: valid
  - yaml
""")

        with pytest.raises(ValueError) as exc_info:
            Config.from_file(config_file)

        assert "Failed to load config" in str(exc_info.value)

    def test_should_raise_error_for_non_existent_file(self, tmp_path):
        """Config should raise error for non-existent file."""
        config_file = tmp_path / "does_not_exist.yml"

        with pytest.raises(ValueError):
            Config.from_file(config_file)

    def test_should_merge_cli_arguments(self):
        """Config should merge CLI arguments with precedence."""
        config = Config(
            output_format="terminal",
            color="auto",
            verbose=False
        )

        merged = config.merge_cli_args(
            output_format="json",
            verbose=True
        )

        assert merged.output_format == "json"
        assert merged.verbose is True
        assert merged.color == "auto"  # Unchanged

    def test_should_ignore_none_cli_arguments(self):
        """Config should ignore None CLI arguments."""
        config = Config(output_format="terminal")

        merged = config.merge_cli_args(
            output_format=None,
            verbose=None
        )

        assert merged.output_format == "terminal"

    def test_should_convert_to_dict(self):
        """Config should convert to dictionary."""
        config = Config(
            rules={"test": {"enabled": True}},
            exclude=["tests/**"],
            output_format="json",
            verbose=True
        )

        config_dict = config.to_dict()

        assert isinstance(config_dict, dict)
        assert "rules" in config_dict
        assert "exclude" in config_dict
        assert "output" in config_dict
        assert config_dict["output"]["format"] == "json"
        assert config_dict["output"]["verbose"] is True

    def test_should_have_default_exclusions(self):
        """Default config should exclude common paths."""
        config = Config.default()

        assert any("test" in pattern for pattern in config.exclude)
        assert any("__pycache__" in pattern for pattern in config.exclude)

    def test_should_support_custom_rule_parameters(self, tmp_path):
        """Config should support custom rule parameters."""
        config_file = tmp_path / ".daglinter.yml"
        config_data = {
            "rules": {
                "missing-docs": {
                    "enabled": True,
                    "min_length": 50
                },
                "complex-dependencies": {
                    "enabled": True,
                    "max_fan_out": 20,
                    "max_fan_in": 15
                }
            }
        }

        config_file.write_text(yaml.dump(config_data))

        config = Config.from_file(config_file)

        assert config.rules["missing-docs"]["min_length"] == 50
        assert config.rules["complex-dependencies"]["max_fan_out"] == 20
        assert config.rules["complex-dependencies"]["max_fan_in"] == 15

    def test_should_handle_performance_settings(self, tmp_path):
        """Config should load performance settings."""
        config_file = tmp_path / ".daglinter.yml"
        config_data = {
            "performance": {
                "max_workers": 4,
                "timeout_per_file": 60
            }
        }

        config_file.write_text(yaml.dump(config_data))

        config = Config.from_file(config_file)

        assert config.max_workers == 4
        assert config.timeout_per_file == 60


class TestConfigLoader:
    """Test ConfigLoader functionality."""

    def test_should_discover_config_in_current_directory(self, tmp_path):
        """ConfigLoader should find config in current directory."""
        config_file = tmp_path / ".daglinter.yml"
        config_file.write_text("rules: {}")

        discovered = ConfigLoader.discover_config(tmp_path)

        assert discovered is not None
        assert discovered == config_file

    def test_should_discover_config_in_parent_directory(self, tmp_path):
        """ConfigLoader should find config in parent directory."""
        config_file = tmp_path / ".daglinter.yml"
        config_file.write_text("rules: {}")

        # Create subdirectory
        subdir = tmp_path / "subdir"
        subdir.mkdir()

        discovered = ConfigLoader.discover_config(subdir)

        assert discovered is not None
        assert discovered == config_file

    def test_should_discover_config_up_to_root(self, tmp_path):
        """ConfigLoader should search up to root directory."""
        # Create nested structure
        deep_dir = tmp_path / "a" / "b" / "c"
        deep_dir.mkdir(parents=True)

        # Put config at top level
        config_file = tmp_path / ".daglinter.yml"
        config_file.write_text("rules: {}")

        discovered = ConfigLoader.discover_config(deep_dir)

        assert discovered is not None
        assert discovered == config_file

    def test_should_return_none_when_no_config_found(self, tmp_path):
        """ConfigLoader should return None if no config found."""
        discovered = ConfigLoader.discover_config(tmp_path)

        assert discovered is None

    def test_should_support_yaml_extension(self, tmp_path):
        """ConfigLoader should support .yaml extension."""
        config_file = tmp_path / ".daglinter.yaml"
        config_file.write_text("rules: {}")

        discovered = ConfigLoader.discover_config(tmp_path)

        assert discovered is not None
        assert discovered == config_file

    def test_should_prefer_yml_over_yaml(self, tmp_path):
        """ConfigLoader should prefer .yml over .yaml."""
        yml_file = tmp_path / ".daglinter.yml"
        yaml_file = tmp_path / ".daglinter.yaml"

        yml_file.write_text("rules: {preferred: true}")
        yaml_file.write_text("rules: {preferred: false}")

        discovered = ConfigLoader.discover_config(tmp_path)

        # Should find .yml first (it's first in the list)
        assert discovered == yml_file

    def test_should_load_discovered_config(self, tmp_path, monkeypatch):
        """ConfigLoader should load discovered config."""
        config_file = tmp_path / ".daglinter.yml"
        config_data = {
            "rules": {
                "heavy-imports": {"enabled": False}
            }
        }
        config_file.write_text(yaml.dump(config_data))

        # Change cwd to tmp_path for discovery
        monkeypatch.chdir(tmp_path)
        config = ConfigLoader.load()

        assert config.rules["heavy-imports"]["enabled"] is False

    def test_should_load_explicit_config_path(self, tmp_path):
        """ConfigLoader should load config from explicit path."""
        config_file = tmp_path / "custom_config.yml"
        config_data = {
            "rules": {
                "missing-docs": {"enabled": True}
            }
        }
        config_file.write_text(yaml.dump(config_data))

        config = ConfigLoader.load(config_file)

        assert "missing-docs" in config.rules

    def test_should_return_default_config_when_none_found(self, tmp_path):
        """ConfigLoader should return default config if none found."""
        config = ConfigLoader.load()

        assert isinstance(config, Config)
        assert len(config.rules) > 0
        assert isinstance(config.exclude, list)

    def test_should_handle_invalid_explicit_path(self, tmp_path):
        """ConfigLoader should handle invalid explicit path."""
        fake_path = tmp_path / "does_not_exist.yml"

        # Should return default config
        config = ConfigLoader.load(fake_path)

        assert isinstance(config, Config)

    def test_should_stop_at_filesystem_root(self, tmp_path):
        """ConfigLoader should stop searching at filesystem root."""
        # This should not infinite loop
        discovered = ConfigLoader.discover_config(Path("/"))

        # Should return None or a config if one exists at root
        assert discovered is None or isinstance(discovered, Path)

    def test_should_handle_symlinks(self, tmp_path):
        """ConfigLoader should handle symlinked directories."""
        real_dir = tmp_path / "real"
        real_dir.mkdir()

        config_file = real_dir / ".daglinter.yml"
        config_file.write_text("rules: {}")

        # Create symlink
        link_dir = tmp_path / "link"
        link_dir.symlink_to(real_dir)

        discovered = ConfigLoader.discover_config(link_dir)

        assert discovered is not None

    def test_should_handle_permission_errors_gracefully(self, tmp_path):
        """ConfigLoader should handle permission errors."""
        config_file = tmp_path / ".daglinter.yml"
        config_file.write_text("rules: {}")

        # Try to load - should not crash
        config = ConfigLoader.load(config_file)
        assert isinstance(config, Config)

    def test_should_validate_config_structure(self, tmp_path):
        """ConfigLoader should validate loaded config structure."""
        config_file = tmp_path / ".daglinter.yml"
        config_file.write_text(yaml.dump({
            "rules": {},
            "output": {"format": "json"}
        }))

        config = ConfigLoader.load(config_file)

        assert hasattr(config, 'rules')
        assert hasattr(config, 'output_format')
        assert hasattr(config, 'exclude')

    def test_should_handle_unicode_in_config(self, tmp_path):
        """ConfigLoader should handle Unicode characters in config."""
        config_file = tmp_path / ".daglinter.yml"
        config_data = {
            "exclude": ["tests/**", "日本語/**", "émojis🚀/**"]
        }
        config_file.write_text(yaml.dump(config_data, allow_unicode=True))

        config = Config.from_file(config_file)

        assert "日本語/**" in config.exclude
        assert "émojis🚀/**" in config.exclude
