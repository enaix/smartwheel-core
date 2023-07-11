from typing import Callable
from PyQt6.QtCore import QObject


class _HandlersApi(QObject):
    """
    Settings object API for communicating with settings handlers.

    Is preferred over using app.Classes.Settings directly
    """
    getter: Callable = None
    """
    Settings value getter function. Please view smartwheel.settings.getValue documentation
    """

    setter: Callable = None
    """
    Settings value setter function. Please view smartwheel.settings.setValue documentation
    """

    handlers: dict = None
    """
    Dictionary of all loaded settings handlers. Points to smartwheel.settings.handlers
    
    Useful for calling other handlers that are not meant to be used directly
    """

    externalRegistries: dict = None
    """
    Dictionary of external settings registries by name
    """

    _savePreset: Callable = None
    """
    Save the specified preset. Please view smartwheel.settings.savePreset documentation
    
    Note: presets are handled automatically by the application
    """

    _loadPreset: Callable = None
    """
    Load the specified preset. Please view smartwheel.settings.loadPreset documentation
    
    Note: presets are handled automatically by the application
    """

    _setCustomPreset: Callable = None
    """
    Set custom preset on settings edit. Please view smartwheel.settings.setCustom documentation
    
    Note: presets are handled automatically by the application
    """

    _showLinkedWidgets: Callable = None
    """
    Show/hide linked widgets of the external registry selector. Please view smartwheel.settings.showLinkedWidgets documentation
    """

    _hooks: dict = None
    """
    Settings application hooks. Should not be used directly, see getter/setter functions instead
    """

    def __init__(self):
        super(_HandlersApi, self).__init__()

    def __new__(cls):
        """
        Singleton implementation
        """
        if not hasattr(cls, "instance"):
            cls.instance = super(_HandlersApi, cls).__new__(cls)
        return cls.instance


HandlersApi = _HandlersApi()
