CONFIG = {
    "server": "",
    "cameras": [
        "101",
        "201",
        "301"
    ]
}
import os


def getConfig(text):
    try:
        if os.environ[text]:
            return os.environ[text]
    except:
        pass
    return CONFIG[text]
