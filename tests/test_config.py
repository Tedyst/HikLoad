import hikload.config as config


def test_defaultvar():
    config.CONFIG["server"] = "1"
    assert config.CONFIG["server"] == "1"


def test_envvar():
    import os
    os.environ["server"] = "1"
    assert config.CONFIG["server"] == "1"
