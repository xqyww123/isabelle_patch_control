"""Feature name <-> conda package name (plan decision 10).  tools/common.py imports this too."""


def package_name(feature: str) -> str:
    return "isabelle-" + feature.replace("_", "-")


def feature_name(package: str) -> str | None:
    """The inverse of package_name; None when the name cannot be a feature package's."""
    if package.startswith("isabelle-"):
        return package[len("isabelle-"):].replace("-", "_")
    return None
