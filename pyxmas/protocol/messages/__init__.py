from typing import Optional, Dict, Protocol, runtime_checkable, Union
import re
from functools import lru_cache
import aioxmpp
import spade.message
import pyxmas.protocol.data as data

__all__ = ['set_default_data_types',
           'METADATA_DEPTH',
           'METADATA_TYPE',
           'create_xml_tag',
           'MessageLike',
           'AcceptMessage',
           'CollisionMessage',
           'ComparisonMessage',
           'DisapproveMessage',
           'InvalidAlternativeMessage',
           'MoreDetailsMessage',
           'OverrideRecommendationMessage',
           'PreferAlternativeMessage',
           'QueryMessage',
           'RecommendationMessage',
           'UnclearExplanationMessage',
           'WhyMessage',
           'WhyNotMessage',
           ]


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

    def __hash__(self) -> int:
        ...


MessageLike.register(spade.message.Message)


def messages_equal(a: MessageLike, b: MessageLike) -> bool:
    return a is b or (a is not None and b is not None and
                      a.sender == b.sender and
                      a.to == b.to and
                      a.thread == b.thread and
                      a.metadata == b.metadata and
                      a.body == b.body
                      )


def message_hash(message: MessageLike) -> int:
    return hash((message.sender, message.to, message.thread, message.metadata, message.body))


spade.message.Message.__eq__ = messages_equal
spade.message.Message.__hash__ = message_hash


@lru_cache()
def xml_tag_pattern(name: str):
    name = re.escape(name)
    return re.compile(f"<{name}>(.*?)</{name}>", re.DOTALL | re.MULTILINE)


def get_xml_tag_value(input: str, name: str):
    pattern = xml_tag_pattern(name)
    for match in pattern.finditer(input):
        content = match.group(1)
        if content:
            return content
    return None


def create_xml_tag(name: str, value: data.Serializable):
    value = "" if value is None else value.serialize()
    return f"<{name}>{value}</{name}>"


def update_xml_tag_value(input: str, name: str, value: data.Serializable):
    pattern = xml_tag_pattern(name)
    for match in pattern.finditer(input):
        if value is None:
            return input[:match.start()] + input[match.end():].strip()
        return input[:match.start(1)] + value.serialize() + input[match.end(1):]
    if value is None:
        return input
    new_tag = create_xml_tag(name, value)
    if input:
        return f"{input}\n{new_tag}"
    else:
        return new_tag


_default_data_types: data.Types = None


def get_default_data_types() -> data.Types:
    global _default_data_types
    if _default_data_types is None:
        import pyxmas.protocol.data.strings as strings
        _default_data_types = strings.Types()
    return _default_data_types


def set_default_data_types(types: data.Types):
    global _default_data_types
    _default_data_types = types


class MessageDecorator(MessageLike):
    def __init__(self, delegate: MessageLike):
        while isinstance(delegate, MessageDecorator):
            delegate = delegate.delegate
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

    def __repr__(self):
        return str(self._delegate)

    @classmethod
    def from_node(cls, node: aioxmpp.Message):
        return MessageDecorator(super().from_node(node))

    @property
    def to(self) -> aioxmpp.JID:
        return self._delegate.to

    @to.setter
    def to(self, value: aioxmpp.JID):
        self._delegate.to = value

    @property
    def sender(self) -> aioxmpp.JID:
        return self._delegate.sender

    @sender.setter
    def sender(self, value: aioxmpp.JID):
        self._delegate.sender = value

    @property
    def body(self) -> str:
        return self._delegate.body

    @body.setter
    def body(self, value: str):
        if value and "\n" in value:
            lines = value.split("\n")
            lines.sort()
            value = "\n".join(lines)
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
        return messages_equal(self, other)

    def __hash__(self):
        return message_hash(self)


METADATA_TYPE = "pyxmas.protocol.messages.type"
METADATA_DEPTH = "pyxmas.protocol.messages.depth"


class BaseProtocolMessage(MessageDecorator):
    def __init__(self, delegate: MessageLike, impl: data.Types = None, depth: int = None):
        super().__init__(delegate)
        if impl is None:
            impl = _default_data_types
        if impl is None:
            raise ValueError("No data types implementation provided")
        self._impl = impl
        if METADATA_TYPE in self.metadata:
            assert self.get_metadata(METADATA_TYPE) == type(self).__name__, \
                f"Attempt to wrap a message of type {self.get_metadata(METADATA_TYPE)} as {type(self).__name__}"
        else:
            self.set_metadata(METADATA_TYPE, type(self).__name__)
        if depth is not None:
            self.set_metadata(METADATA_DEPTH, str(depth))

    @property
    def is_terminal(self):
        return False

    @property
    def depth(self):
        return int(self.get_metadata(METADATA_DEPTH))

    @depth.setter
    def depth(self, value: int):
        self.set_metadata(METADATA_DEPTH, str(value))

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

    # noinspection PyTypeChecker
    @classmethod
    def create(cls,
               to: Optional[str] = None,
               sender: Optional[str] = None,
               body: Optional[str] = None,
               thread: Optional[str] = None,
               metadata: Optional[Dict[str, str]] = None,
               impl: data.Types = None,
               depth: int = 0
               ) -> 'BaseProtocolMessage':
        return cls(spade.message.Message(to, sender, body, thread, metadata), impl, depth)

    @classmethod
    def wrap(cls, message: MessageLike, impl: data.Types = None, override_type: bool = False) -> 'BaseProtocolMessage':
        if override_type:
            message.set_metadata(METADATA_TYPE, cls.__name__)
        return cls(message, impl)


# noinspection PyUnresolvedReferences
class MessageWithQuery:
    @property
    def query(self) -> data.Query:
        return self.unpack("query", self._impl.query_type)

    @query.setter
    def query(self, value: data.Query):
        self.pack(query=value)


# noinspection PyMethodOverriding,PyTypeChecker
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
               depth: int = 0
               ) -> 'QueryMessage':
        instance = super().create(to, sender, body, thread, metadata, impl, depth)
        instance.query = query
        return instance

    def make_recommendation_reply(self, recommendation: data.Recommendation) -> 'RecommendationMessage':
        reply = self.make_reply()
        reply = RecommendationMessage.wrap(reply, self._impl, override_type=True)
        reply.recommendation = recommendation
        reply.depth = self.depth + 1
        return reply


# noinspection PyUnresolvedReferences
class MessageWithRecommendation:
    @property
    def recommendation(self) -> data.Recommendation:
        return self.unpack("recommendation", self._impl.recommendation_type)

    @recommendation.setter
    def recommendation(self, value: data.Recommendation):
        self.pack(recommendation=value)


# noinspection PyUnresolvedReferences
class MessageWithApproveCapability:
    def make_accept_reply(self) -> 'AcceptMessage':
        reply = self.make_reply()
        reply = AcceptMessage.wrap(reply, self._impl, override_type=True)
        reply.depth = self.depth + 1
        return reply


# noinspection PyUnresolvedReferences
class MessageWithComplainCapabilities:
    def make_collision_reply(self, feature: data.Feature) -> 'CollisionMessage':
        reply = self.make_reply()
        reply = CollisionMessage.wrap(reply, self._impl, override_type=True)
        reply.feature = feature
        reply.depth = self.depth + 1
        return reply

    def make_disapprove_reply(self, motivation: data.Motivation) -> 'DisapproveMessage':
        reply = self.make_reply()
        reply = DisapproveMessage.wrap(reply, self._impl, override_type=True)
        reply.motivation = motivation
        reply.depth = self.depth + 1
        return reply


# noinspection PyMethodOverriding,PyTypeChecker
class RecommendationMessage(BaseProtocolMessage, MessageWithQuery, MessageWithRecommendation,
                            MessageWithApproveCapability, MessageWithComplainCapabilities):
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
               depth: int = 0
               ) -> 'RecommendationMessage':
        instance = super().create(to, sender, body, thread, metadata, impl, depth)
        instance.query = query
        instance.recommendation = recommendation
        return instance

    def make_why_reply(self) -> 'WhyMessage':
        reply = self.make_reply()
        reply = WhyMessage.wrap(reply, self._impl, override_type=True)
        reply.depth = self.depth + 1
        return reply

    def make_why_not_reply(self, alternative: data.Recommendation) -> 'WhyNotMessage':
        reply = self.make_reply()
        reply = WhyNotMessage.wrap(reply, self._impl, override_type=True)
        reply.alternative = alternative
        reply.depth = self.depth + 1
        return reply


# noinspection PyMethodOverriding,PyTypeChecker
class WhyMessage(BaseProtocolMessage, MessageWithQuery, MessageWithRecommendation):
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
               depth: int = 0
               ) -> 'WhyMessage':
        instance = super().create(to, sender, body, thread, metadata, impl, depth)
        instance.query = query
        instance.recommendation = recommendation
        return instance

    def make_more_details_reply(self, explanation: data.Explanation) -> 'MoreDetailsMessage':
        reply = self.make_reply()
        reply = MoreDetailsMessage.wrap(reply, self._impl, override_type=True)
        reply.explanation = explanation
        reply.depth = self.depth + 1
        return reply


# noinspection PyUnresolvedReferences
class MessageWithExplanation:
    @property
    def explanation(self) -> data.Explanation:
        return self.unpack("explanation", self._impl.explanation_type)

    @explanation.setter
    def explanation(self, value: data.Explanation):
        self.pack(explanation=value)


# noinspection PyMethodOverriding,PyTypeChecker
class AcceptMessage(BaseProtocolMessage, MessageWithQuery, MessageWithRecommendation, MessageWithExplanation):
    @classmethod
    def create(cls,
               query: data.Query,
               recommendation: data.Recommendation,
               explanation: data.Explanation = None,
               to: Optional[str] = None,
               sender: Optional[str] = None,
               body: Optional[str] = None,
               thread: Optional[str] = None,
               metadata: Optional[Dict[str, str]] = None,
               impl: data.Types = None,
               depth: int = 0
               ) -> 'AcceptMessage':
        instance = super().create(to, sender, body, thread, metadata, impl, depth)
        instance.query = query
        instance.recommendation = recommendation
        instance.explanation = explanation
        return instance

    @property
    def is_terminal(self):
        return True


# noinspection PyUnresolvedReferences
class MessageWithAlternative:
    @property
    def alternative(self) -> data.Recommendation:
        return self.unpack("alternative", self._impl.recommendation_type)

    @alternative.setter
    def alternative(self, value: data.Recommendation):
        self.pack(alternative=value)


# noinspection PyMethodOverriding,PyTypeChecker
class WhyNotMessage(BaseProtocolMessage, MessageWithQuery, MessageWithRecommendation, MessageWithAlternative):
    @classmethod
    def create(cls,
               query: data.Query,
               recommendation: data.Recommendation,
               alternative: data.Recommendation,
               to: Optional[str] = None,
               sender: Optional[str] = None,
               body: Optional[str] = None,
               thread: Optional[str] = None,
               metadata: Optional[Dict[str, str]] = None,
               impl: data.Types = None,
               depth: int = 0
               ) -> 'WhyNotMessage':
        instance = super().create(to, sender, body, thread, metadata, impl, depth)
        instance.query = query
        instance.recommendation = recommendation
        instance.alternative = alternative
        return instance

    def make_comparison_reply(self, explanation: data.Explanation) -> 'ComparisonMessage':
        reply = self.make_reply()
        reply = ComparisonMessage.wrap(reply, self._impl, override_type=True)
        reply.explanation = explanation
        reply.depth = self.depth + 1
        return reply

    def make_invalid_alternative_reply(self, explanation: data.Explanation) -> 'InvalidAlternativeMessage':
        reply = self.make_reply()
        reply = InvalidAlternativeMessage.wrap(reply, self._impl, override_type=True)
        reply.explanation = explanation
        reply.depth = self.depth + 1
        return reply


# noinspection PyUnresolvedReferences
class MessageWithFeature:
    @property
    def feature(self) -> data.Feature:
        return self.unpack("feature", self._impl.feature_type)

    @feature.setter
    def feature(self, value: data.Feature):
        self.pack(feature=value)


# noinspection PyUnresolvedReferences
class MessageWithRestartCapability:
    def make_recommendation_reply(self, recommendation: data.Recommendation) -> 'RecommendationMessage':
        reply = self.make_reply()
        reply = RecommendationMessage.wrap(reply, self._impl, override_type=True)
        reply.body = None
        reply.query = self.query
        reply.recommendation = recommendation
        reply.depth = self.depth + 1
        return reply


# noinspection PyMethodOverriding,PyTypeChecker
class CollisionMessage(BaseProtocolMessage, MessageWithQuery, MessageWithRecommendation, MessageWithFeature,
                       MessageWithExplanation, MessageWithRestartCapability):
    @classmethod
    def create(cls,
               query: data.Query,
               recommendation: data.Recommendation,
               feature: data.Feature,
               explanation: data.Explanation = None,
               to: Optional[str] = None,
               sender: Optional[str] = None,
               body: Optional[str] = None,
               thread: Optional[str] = None,
               metadata: Optional[Dict[str, str]] = None,
               impl: data.Types = None,
               depth: int = 0
               ) -> 'CollisionMessage':
        instance = super().create(to, sender, body, thread, metadata, impl, depth)
        instance.query = query
        instance.recommendation = recommendation
        instance.feature = feature
        instance.explanation = explanation
        return instance


# noinspection PyUnresolvedReferences
class MessageWithMotivation:
    @property
    def motivation(self) -> data.Motivation:
        return self.unpack("motivation", self._impl.motivation_type)

    @motivation.setter
    def motivation(self, value: data.Motivation):
        self.pack(motivation=value)


# noinspection PyMethodOverriding, PyTypeChecker
class DisapproveMessage(BaseProtocolMessage, MessageWithQuery, MessageWithRecommendation, MessageWithMotivation,
                        MessageWithExplanation, MessageWithRestartCapability):
    @classmethod
    def create(cls,
               query: data.Query,
               recommendation: data.Recommendation,
               motivation: data.Motivation,
               explanation: data.Explanation = None,
               to: Optional[str] = None,
               sender: Optional[str] = None,
               body: Optional[str] = None,
               thread: Optional[str] = None,
               metadata: Optional[Dict[str, str]] = None,
               impl: data.Types = None,
               depth: int = 0
               ) -> 'DisapproveMessage':
        instance = super().create(to, sender, body, thread, metadata, impl, depth)
        instance.query = query
        instance.recommendation = recommendation
        instance.motivation = motivation
        instance.explanation = explanation
        return instance


# noinspection PyMethodOverriding, PyTypeChecker
class MoreDetailsMessage(BaseProtocolMessage, MessageWithQuery, MessageWithRecommendation, MessageWithExplanation,
                         MessageWithApproveCapability, MessageWithComplainCapabilities):
    @classmethod
    def create(cls,
               query: data.Query,
               recommendation: data.Recommendation,
               explanation: data.Explanation,
               to: Optional[str] = None,
               sender: Optional[str] = None,
               body: Optional[str] = None,
               thread: Optional[str] = None,
               metadata: Optional[Dict[str, str]] = None,
               impl: data.Types = None,
               depth: int = 0
               ) -> 'MoreDetailsMessage':
        instance = super().create(to, sender, body, thread, metadata, impl, depth)
        instance.query = query
        instance.recommendation = recommendation
        instance.explanation = explanation
        return instance

    def make_unclear_reply(self) -> 'UnclearExplanationMessage':
        reply = self.make_reply()
        reply = UnclearExplanationMessage.wrap(reply, self._impl, override_type=True)
        reply.depth = self.depth + 1
        return reply


# noinspection PyMethodOverriding, PyTypeChecker
class ComparisonMessage(BaseProtocolMessage, MessageWithQuery, MessageWithRecommendation, MessageWithAlternative,
                        MessageWithExplanation, MessageWithApproveCapability):
    @classmethod
    def create(cls,
               query: data.Query,
               recommendation: data.Recommendation,
               alternative: data.Recommendation,
               explanation: data.Explanation,
               to: Optional[str] = None,
               sender: Optional[str] = None,
               body: Optional[str] = None,
               thread: Optional[str] = None,
               metadata: Optional[Dict[str, str]] = None,
               impl: data.Types = None,
               depth: int = 0
               ) -> 'ComparisonMessage':
        instance = super().create(to, sender, body, thread, metadata, impl, depth)
        instance.query = query
        instance.recommendation = recommendation
        instance.alternative = alternative
        instance.explanation = explanation
        return instance

    def make_accept_reply(self) -> 'AcceptMessage':
        reply = super().make_accept_reply()
        reply.body = None
        reply.query = self.query
        reply.recommendation = self.recommendation
        reply.explanation = self.explanation
        return reply

    def make_prefer_alternative_reply(self) -> 'PreferAlternativeMessage':
        reply = self.make_reply()
        reply = PreferAlternativeMessage.wrap(reply, self._impl, override_type=True)
        reply.body = None
        reply.query = self.query
        reply.recommendation = self.recommendation
        reply.alternative = self.alternative
        reply.depth = self.depth + 1
        return reply


# noinspection PyMethodOverriding, PyTypeChecker
class InvalidAlternativeMessage(BaseProtocolMessage, MessageWithQuery, MessageWithRecommendation,
                                MessageWithAlternative, MessageWithExplanation, MessageWithApproveCapability):
    @classmethod
    def create(cls,
               query: data.Query,
               recommendation: data.Recommendation,
               alternative: data.Recommendation,
               explanation: data.Explanation,
               to: Optional[str] = None,
               sender: Optional[str] = None,
               body: Optional[str] = None,
               thread: Optional[str] = None,
               metadata: Optional[Dict[str, str]] = None,
               impl: data.Types = None,
               depth: int = 0
               ) -> 'InvalidAlternativeMessage':
        instance = super().create(to, sender, body, thread, metadata, impl, depth)
        instance.query = query
        instance.recommendation = recommendation
        instance.alternative = alternative
        instance.explanation = explanation
        return instance

    def make_override_recommendation_reply(self) -> 'OverrideRecommendationMessage':
        reply = self.make_reply()
        reply = OverrideRecommendationMessage.wrap(reply, self._impl, override_type=True)
        reply.body = None
        reply.query = self.query
        reply.recommendation = self.recommendation
        reply.alternative = self.alternative
        reply.depth = self.depth + 1
        return reply


# noinspection PyMethodOverriding, PyTypeChecker
class UnclearExplanationMessage(BaseProtocolMessage, MessageWithQuery, MessageWithRecommendation,
                                MessageWithExplanation):
    @classmethod
    def create(cls,
               query: data.Query,
               recommendation: data.Recommendation,
               explanation: data.Explanation,
               to: Optional[str] = None,
               sender: Optional[str] = None,
               body: Optional[str] = None,
               thread: Optional[str] = None,
               metadata: Optional[Dict[str, str]] = None,
               impl: data.Types = None,
               depth: int = 0
               ) -> 'UnclearExplanationMessage':
        instance = super().create(to, sender, body, thread, metadata, impl, depth)
        instance.query = query
        instance.recommendation = recommendation
        instance.explanation = explanation
        return instance

    def make_more_details_reply(self, explanation: data.Explanation) -> 'MoreDetailsMessage':
        reply = self.make_reply()
        reply = MoreDetailsMessage.wrap(reply, self._impl, override_type=True)
        reply.explanation = explanation
        reply.depth = self.depth + 1
        return reply


# noinspection PyMethodOverriding, PyTypeChecker
class OverrideRecommendationMessage(BaseProtocolMessage, MessageWithQuery, MessageWithRecommendation,
                                    MessageWithAlternative):
    @classmethod
    def create(cls,
               query: data.Query,
               recommendation: data.Recommendation,
               alternative: data.Explanation,
               to: Optional[str] = None,
               sender: Optional[str] = None,
               body: Optional[str] = None,
               thread: Optional[str] = None,
               metadata: Optional[Dict[str, str]] = None,
               impl: data.Types = None,
               depth: int = 0
               ) -> 'OverrideRecommendationMessage':
        instance = super().create(to, sender, body, thread, metadata, impl, depth)
        instance.query = query
        instance.recommendation = recommendation
        instance.alternative = alternative
        return instance

    @property
    def is_terminal(self):
        return True


# noinspection PyMethodOverriding, PyTypeChecker
class PreferAlternativeMessage(BaseProtocolMessage, MessageWithQuery, MessageWithRecommendation,
                               MessageWithAlternative):
    @classmethod
    def create(cls,
               query: data.Query,
               recommendation: data.Recommendation,
               alternative: data.Explanation,
               to: Optional[str] = None,
               sender: Optional[str] = None,
               body: Optional[str] = None,
               thread: Optional[str] = None,
               metadata: Optional[Dict[str, str]] = None,
               impl: data.Types = None,
               depth: int = 0
               ) -> 'PreferAlternativeMessage':
        instance = super().create(to, sender, body, thread, metadata, impl, depth)
        instance.query = query
        instance.recommendation = recommendation
        instance.alternative = alternative
        return instance

    @property
    def is_terminal(self):
        return True


MESSAGE_TYPES = {
    t.__name__: t for t in [AcceptMessage,
                            CollisionMessage,
                            ComparisonMessage,
                            DisapproveMessage,
                            InvalidAlternativeMessage,
                            MoreDetailsMessage,
                            OverrideRecommendationMessage,
                            PreferAlternativeMessage,
                            QueryMessage,
                            RecommendationMessage,
                            UnclearExplanationMessage,
                            WhyMessage,
                            WhyNotMessage]
}


def wrap(message: spade.message.Message, impl: data.Types = None):
    if impl is None:
        impl = _default_data_types
    if METADATA_TYPE in message.metadata:
        message_type = message.metadata[METADATA_TYPE]
        if message_type in MESSAGE_TYPES:
            return MESSAGE_TYPES[message_type].wrap(message, impl)
        else:
            raise ValueError(f"Unknown message type: {message_type}")
    else:
        raise ValueError(f"Message has no {METADATA_TYPE} metadata field, hence it cannot be wrapped")


ResponseToRecommendationMessage = Union[WhyMessage, WhyNotMessage, AcceptMessage, CollisionMessage, DisapproveMessage]

ResponseToMoreDetailsMessage = Union[UnclearExplanationMessage, AcceptMessage, CollisionMessage, DisapproveMessage]

ResponseToComparisonMessage = Union[AcceptMessage, PreferAlternativeMessage]

ResponseToInvalidAlternativeMessage = Union[AcceptMessage, OverrideRecommendationMessage]
