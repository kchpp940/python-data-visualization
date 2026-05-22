"""Chapter 4 notebook initialization — alias of :mod:`src.ch3_init`.

Chapter 4 uses the same Matplotlib stack as Chapter 3, so this module
simply re-exports everything from :mod:`src.ch3_init` under the chapter-4
name for semantic clarity in notebooks.
"""

from src.ch3_init import *  # noqa: F401,F403
from src.ch3_init import __all__  # noqa: F401
