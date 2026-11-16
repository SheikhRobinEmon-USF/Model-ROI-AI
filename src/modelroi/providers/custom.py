"""User-deployed Ollama responders exposed to the studio."""
PREFIX = "ollama/"


def tag_for(model):
    return model.removeprefix(PREFIX)


def inventory(tags, builtins):
    return [{"id": PREFIX + name, "name": name, "custom": True, "installed": True}
            for item in tags if (name := item.get("name")) and name not in builtins
            and name != "gpt-oss:20b" and not item.get("remote_model")
            and not name.endswith("-cloud") and not name.endswith(":cloud")]
