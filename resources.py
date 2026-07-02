"""Qt resource registration for the Radiation Toolbox plugin."""

import os.path

from qgis.PyQt.QtCore import QResource


_RESOURCE_PATH = os.path.join(os.path.dirname(__file__), "resources.rcc")
_REGISTERED = False


def qInitResources():
    """Register the compiled Qt binary resource file."""
    global _REGISTERED
    if not _REGISTERED:
        _REGISTERED = QResource.registerResource(_RESOURCE_PATH)
    return _REGISTERED


def qCleanupResources():
    """Unregister the compiled Qt binary resource file."""
    global _REGISTERED
    if _REGISTERED:
        _REGISTERED = not QResource.unregisterResource(_RESOURCE_PATH)
    return not _REGISTERED


qInitResources()
