from abc import ABC
from typing import Union, Iterable

import spade
import spade.behaviour as behaviours

import pyxmas
import pyxmas.protocol.messages as messages
import pyxmas.protocol.data as data


# noinspection PyUnresolvedReferences
class Protocol(behaviours.FSMBehaviour, pyxmas.Behaviour, ABC):
    def __init__(self, thread: str = None, impl: data.Types = None):
        behaviours.FSMBehaviour.__init__(self)
        self._initialize_random_thread(thread)
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

    # noinspection PyMethodOverriding
    def add_state(self, state: type, initial: bool = False):
        super().add_state(state.name(), state(self), initial)

    def has_transition(self, src: str, dest: str):
        return dest in (self._transitions[src] or [])

    def add_transition_if_not_exists(self, src: str, dest: str):
        if not self.has_transition(src, dest):
            self.add_transition(src, dest)

    def add_transitions(self, src: type, dests: Iterable[type], error: type = None):
        self.add_state(src)
        if error is not None:
            self.add_state(error)
            self.add_transition_if_not_exists(src.name(), error.name())
        for dest in dests:
            self.add_state(dest)
            self.add_transition_if_not_exists(src.name(), dest.name())
            if error is not None:
                self.add_transition_if_not_exists(dest.name(), error.name())


class State(behaviours.State, pyxmas.Behaviour, ABC):
    def __init__(self, parent: Protocol):
        behaviours.State.__init__(self)
        self._initialize_random_thread()
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

    @classmethod
    def name(cls) -> str:
        return cls.__name__.replace("State", "")

    def set_next_state(self, state_name: Union[str, type]) -> None:
        if isinstance(state_name, str):
            super().set_next_state(state_name)
        elif isinstance(state_name, type):
            super().set_next_state(state_name.name())
        else:
            raise TypeError(f"Invalid type {type(state_name)} for state_name")
