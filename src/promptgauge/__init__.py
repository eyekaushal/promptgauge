"""promptgauge: which lines of your system prompt actually do anything.

The only re-export module in the package: this is the public SDK surface.
"""

# `promptgauge.ablate` is both the subpackage `ablate/` and the SDK function below. Python binds a
# subpackage onto its parent the first time it is imported, which would overwrite the function if
# that happened later. Importing the subpackage here first means the function binding wins for good.
from promptgauge import ablate as _ablate_package  # noqa: F401
from promptgauge import scorers
from promptgauge.sdk import ablate, evaluate

__all__ = ["evaluate", "ablate", "scorers"]
__version__ = "0.1.0"
