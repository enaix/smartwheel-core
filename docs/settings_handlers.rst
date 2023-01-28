settings\_handlers package
==========================

Each handler module must contain one or more classes inherited from `BaseHandler` and have `handlers` dictionary that links each setting type to the class.

```
{"setting_type": SettingHandler}
```

initElem method creates the widget, links it to the custom setter function and returns it. Please see `settings_handlers.basic` module for examples 

Submodules
----------

settings\_handlers.base module
------------------------------

.. automodule:: settings_handlers.base
   :members:
   :undoc-members:
   :show-inheritance:

Module contents
---------------

.. automodule:: settings_handlers
   :members:
   :undoc-members:
   :show-inheritance:
