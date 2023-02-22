from typing import Optional, Dict

import aioxmpp
import spade.message
from .data import *


__all__ = ['QueryMessage']


class MessageDecorator:
    def __init__(self, delegate: spade.message.Message):
        self._delegate = delegate

    @property
    def delegate(self):
        return self._delegate

    def make_reply(self, *args) -> 'MessageDecorator':
        return MessageDecorator(self._delegate.make_reply(*args))

    def prepare(self) -> aioxmpp.Message:
        return self._delegate.prepare()

    def __str__(self) -> str:
        return str(self._delegate)

    @classmethod
    def from_node(cls, node: aioxmpp.Message):
        return MessageDecorator(super().from_node(node))

    @property
    def to(self) -> str:
        return self._delegate.to

    @to.setter
    def to(self, value: str):
        self._delegate.to = value

    @property
    def sender(self) -> str:
        return self._delegate.sender

    @sender.setter
    def sender(self, value: str):
        self._delegate.sender = value

    @property
    def body(self) -> str:
        return self._delegate.body

    @body.setter
    def body(self, value: str):
        self._delegate.body = value

    @property
    def thread(self) -> str:
        return self._delegate.thread

    @thread.setter
    def thread(self, value: str):
        self._delegate.thread = value

    @property
    def metadata(self) -> dict:
        return self._delegate.metadata

    def set_metadata(self, key: str, value: str):
        self._delegate.set_metadata(key, value)

    def get_metadata(self, key: str) -> str:
        return self._delegate.get_metadata(key)

    def match(self, message) -> bool:
        return self._delegate.match(message)

    @property
    def id(self) -> int:
        return self._delegate.id

    def __eq__(self, other):
        return self._delegate.__eq__(other)


_default_data_types: Types = None


def set_default_data_types(types: Types):
    global _default_data_types
    _default_data_types = types


class BaseProtocolMessage(MessageDecorator):
    def __int__(self, delegate: spade.message.Message, impl: Types = None):
        super().__int__(delegate)
        if impl is None:
            impl = _default_data_types
        if impl is None:
            raise ValueError("No data types implementation provided")
        self._impl = impl
        self.set_metadata("pyxmas.protocol.messages.type", type(self).__name__)

    @property
    def type(self):
        return self.get_metadata("pyxmas.protocol.messages.type")

    def pack(self, *args):
        self.body = "\n".join([a.serialize() for a in args])

    def unpack(self, index: int, as_type: type):
        return as_type.parse(self.body.split("\n")[index])

    @classmethod
    def create(cls,
               to: Optional[str] = None,
               sender: Optional[str] = None,
               body: Optional[str] = None,
               thread: Optional[str] = None,
               metadata: Optional[Dict[str, str]] = None,
               impl: Types = None
               ):
        return cls(spade.message.Message(to, sender, body, thread, metadata), impl)

    @classmethod
    def wrap(cls, message: spade.message.Message, impl: Types = None):
        return cls(message, impl)


class QueryMessage(BaseProtocolMessage):
    @property
    def query(self):
        return self.unpack(0, self._impl.query_type)

    @query.setter
    def query(self, value):
        self.pack(value)
