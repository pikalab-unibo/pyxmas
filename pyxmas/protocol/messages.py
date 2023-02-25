from typing import Optional, Dict, Union, Protocol, runtime_checkable
import re
from functools import lru_cache
import aioxmpp
import spade.message
import pyxmas.protocol.data as data

__all__ = ['set_default_data_types', 'METADATA_TYPE', 'create_xml_tag', 'QueryMessage', 'RecommendationMessage']


@runtime_checkable
class MessageLike(Protocol):
    @property
    def sender(self) -> aioxmpp.JID:
        ...

    @property
    def to(self) -> aioxmpp.JID:
        ...

    @property
    def thread(self) -> str:
        ...

    @property
    def metadata(self) -> Dict[str, str]:
        ...

    @property
    def body(self) -> str:
        ...

    @body.setter
    def body(self, value: str):
        ...

    def make_reply(self, *args) -> 'MessageLike':
        ...

    def prepare(self) -> aioxmpp.Message:
        ...

    def __str__(self) -> str:
        ...

    @classmethod
    def from_node(cls, node: aioxmpp.Message) -> 'MessageLike':
        ...

    def set_metadata(self, key: str, value: str):
        ...

    def get_metadata(self, key: str) -> str:
        ...

    def match(self, message) -> bool:
        ...

    @property
    def id(self) -> int:
        ...

    def __eq__(self, other) -> bool:
        ...


@lru_cache()
def xml_tag_pattern(name: str):
    name = re.escape(name)
    return re.compile(f"<{name}>(.*)</{name}>")


def get_xml_tag_value(input: str, name: str):
    pattern = xml_tag_pattern(name)
    match = pattern.match(input)
    if match:
        m = match.group(1)
        if m:
            return m
        else:
            return None
    return None


def create_xml_tag(name: str, value: data.Serializable):
    value = "" if value is None else value.serialize()
    return f"<{name}>{value}</{name}>"


def update_xml_tag_value(input: str, name: str, value: data.Serializable):
    pattern = xml_tag_pattern(name)
    new_tag = create_xml_tag(name, value)
    match = pattern.match(input)
    if match:
        return pattern.sub(new_tag, input)
    elif input:
        return f"{input}\n{new_tag}"
    else:
        return new_tag


_default_data_types: data.Types = None


def set_default_data_types(types: data.Types):
    global _default_data_types
    _default_data_types = types


class MessageDecorator(MessageLike):
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


METADATA_TYPE = "pyxmas.protocol.messages.type"


class BaseProtocolMessage(MessageDecorator):
    def __init__(self, delegate: spade.message.Message, impl: data.Types = None):
        super().__init__(delegate)
        if impl is None:
            impl = _default_data_types
        if impl is None:
            raise ValueError("No data types implementation provided")
        self._impl = impl
        self.set_metadata(METADATA_TYPE, type(self).__name__)

    @property
    def type(self):
        return self.get_metadata(METADATA_TYPE)

    def pack(self, **kwargs):
        if self.body is None:
            self.body = ""
        for name in kwargs:
            self.body = update_xml_tag_value(self.body, name, kwargs[name])

    def unpack(self, name: str, as_type: type):
        value = get_xml_tag_value(self.body, name)
        if value:
            return as_type.parse(value)
        return None

    @classmethod
    def create(cls,
               to: Optional[str] = None,
               sender: Optional[str] = None,
               body: Optional[str] = None,
               thread: Optional[str] = None,
               metadata: Optional[Dict[str, str]] = None,
               impl: data.Types = None
               ) -> 'BaseProtocolMessage':
        return cls(spade.message.Message(to, sender, body, thread, metadata), impl)

    @classmethod
    def wrap(cls, message: Union[spade.message.Message, MessageDecorator],
             impl: data.Types = None) -> 'BaseProtocolMessage':
        while isinstance(message, MessageDecorator):
            message = message.delegate
        return cls(message, impl)


class MessageWithQuery:
    @property
    def query(self) -> data.Query:
        return self.unpack("query", self._impl.query_type)

    @query.setter
    def query(self, value: data.Query):
        self.pack(query=value)


class QueryMessage(BaseProtocolMessage, MessageWithQuery):

    @classmethod
    def create(cls,
               query: data.Query,
               to: Optional[str] = None,
               sender: Optional[str] = None,
               body: Optional[str] = None,
               thread: Optional[str] = None,
               metadata: Optional[Dict[str, str]] = None,
               impl: data.Types = None,
               ) -> 'QueryMessage':
        instance = super().create(to, sender, body, thread, metadata, impl)
        instance.query = query
        return instance

    def make_recommendation_reply(self, recommendation: data.Recommendation):
        reply = self.make_reply()
        reply = RecommendationMessage.wrap(reply, self._impl)
        reply.recommendation = recommendation
        return reply


class MessageWithRecommendation:
    @property
    def recommendation(self) -> data.Query:
        return self.unpack("recommendation", self._impl.query_type)

    @recommendation.setter
    def recommendation(self, value: data.Query):
        self.pack(recommendation=value)


class RecommendationMessage(BaseProtocolMessage, MessageWithQuery, MessageWithRecommendation):
    @classmethod
    def create(cls,
               query: data.Query,
               recommendation: data.Recommendation,
               to: Optional[str] = None,
               sender: Optional[str] = None,
               body: Optional[str] = None,
               thread: Optional[str] = None,
               metadata: Optional[Dict[str, str]] = None,
               impl: data.Types = None,
               ) -> 'RecommendationMessage':
        instance = super().create(to, sender, body, thread, metadata, impl)
        instance.query = query
        instance.recommendation = recommendation
        return instance
