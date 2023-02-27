from abc import ABC
from typing import Union

import spade
import spade.behaviour as behaviours

import pyxmas
import pyxmas.protocol.messages as messages
import pyxmas.protocol.data as data


class Protocol(behaviours.FSMBehaviour, pyxmas.Behaviour, ABC):
    def __init__(self, thread: str = None, impl: data.Types = None):
        super(behaviours.FSMBehaviour).__init__()
        super(pyxmas.Behaviour).__init__(thread)
        self._impl = impl if impl is not None else messages.get_default_data_types()
        self._memory = dict(
            history=list(),
            last_error=None,
        )

    @property
    def impl(self) -> data.Types:
        return self._impl

    @property
    def memory(self) -> dict:
        return self._memory

    def add_state(self, name: str, state: type, initial: bool = False) -> None:
        super().add_state(state.__name__, state(self), initial)


class State(behaviours.State, pyxmas.Behaviour, ABC):
    def __init__(self, parent: Protocol):
        super(behaviours.State).__init__()
        super(pyxmas.Behaviour).__init__(parent._thread)
        self._parent = parent

    @property
    def parent(self) -> Protocol:
        return self._parent

    @property
    def impl(self) -> data.Types:
        return self._parent.impl

    @property
    def memory(self) -> dict:
        return self._parent.memory

    def wrap_message(self, message: spade.message.Message) -> messages.BaseProtocolMessage:
        return messages.wrap(message, impl=self.impl)

    @property
    def name(self) -> str:
        return type(self).__qualname__

    def set_next_state(self, state_name: Union[str, type]) -> None:
        if isinstance(state_name, str):
            super().set_next_state(state_name)
        elif isinstance(state_name, type):
            super().set_next_state(state_name.__name__)
        else:
            raise TypeError(f"Invalid type {type(state_name)} for state_name")
