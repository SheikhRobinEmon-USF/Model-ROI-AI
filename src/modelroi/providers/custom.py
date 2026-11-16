"""User-added Ollama responders exposed to the studio."""
import re

PREFIX = "ollama/"
NAMESPACE = "modelroi/"
JUDGE = "gpt-oss:20b"
NAME = r"^[a-z0-9][a-z0-9_-]{0,62}$"
# A model reference Ollama can pull: a library tag, or a host path such as hf.co/user/repo:quant.
REFERENCE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,180}(:[A-Za-z0-9._-]{1,80})?$")


def tag_for(model):
    return model.removeprefix(PREFIX)


def is_cloud(name):
    return name.endswith("-cloud") or name.endswith(":cloud")


def inventory(tags, builtins):
    models = []
    for item in tags:
        name = item.get("name")
        if not name or name in builtins or name == JUDGE or item.get("remote_model") or is_cloud(name):
            continue
        details = item.get("details") or {}
        models.append({"id": PREFIX + name, "name": name, "custom": True, "installed": True,
                       "label": name.removeprefix(NAMESPACE).removesuffix(":latest"),
                       "size": item.get("size"), "family": details.get("family"),
                       "parameters": details.get("parameter_size"), "quantization": details.get("quantization_level"),
                       "created_here": name.startswith(NAMESPACE)})
    return models
