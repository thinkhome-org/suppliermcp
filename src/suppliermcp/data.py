from pathlib import Path


def data_dir(name: str) -> Path:
    package = Path(__file__).resolve().parent
    bundled = package / name
    # Editable installs read the same canonical files as the plugin builder.
    return bundled if bundled.is_dir() else package.parents[1] / name
