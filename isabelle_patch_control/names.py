"""Feature name <-> conda package name (plan decision 10).  tools/common.py imports this too."""

_EXCEPTIONS = {"dev_patches": "qiyuan-dev-patches"}


def package_name(feature: str) -> str:
    return _EXCEPTIONS.get(feature, "isabelle-" + feature.replace("_", "-"))


def feature_name(package: str) -> str | None:
    """The inverse of package_name; None when the name cannot be a feature package's."""
    for feature, name in _EXCEPTIONS.items():
        if name == package:
            return feature
    if package.startswith("isabelle-"):
        return package[len("isabelle-"):].replace("-", "_")
    return None
