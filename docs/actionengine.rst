actionengine module
===================

Actionengine is the interaction interface between serial (keyboard/device driver) and the wheel.

In order to execute any action, you need to emit the signal

`callAction.emit((bind, command))`

where `bind` is a dict that contains name of the knob/button/keyboard by "name" key and `command` is the unique command of the device.

`command = {"string": "command_name"}`

Actionengine searches for the matching command name in the corresponding `device` dictionary and executes the registered actions.

`{"string": "click1"} -> (actionengine) "button1": [ ... {"command": "click1", "actions": [...]} ... ]`

Each action has following parameters:

    * name
    * description
    * type - When the action is executed (in wheel or module mode)

Any action is executed with following parameters:

    * action - Name of action
    * checkState - If true, execute only if current mode matches with onState/mode (see below)
    * onState - In which mode to execute this action (same with mode by default)
    * mode - With which app mode does this action work
    * repeat - How many times to repeat this actions (default - 0)

As an example, `onState` may differ from `mode` in case if a button opens a wheel (it 'talks' with wheel mode, but is executed only in module mode).
So, onState=module and mode=wheel

Available actions are stored in `commandActions` dict.

.. automodule:: actionengine
   :members:
   :undoc-members:
   :show-inheritance:
