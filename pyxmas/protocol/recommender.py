# https://www.plantuml.com/plantuml/svg/fLAnJiCm5Dpz5TwQ83hGiGEgH5k9eK0ZLHqGWuaVhLNRYMmdqB_73h8Qi1mJTOlUkxlS-Tv26w9C8pWwCWeOH6tEc88k5QiDgoHwlNd3q-aztXDcc3piDAXj0-gC_Wxm77_-Z71ZPrY0rkG0A0GwkOTAr8qR5r1MGe2anFtEYdIOR9kZ26IEIx_0gjiGJpOLrXQ6K8phauIRDG1z9-N96lYzo8eS3J8YiGSvdG_tidFyV4h-OVZ1x8PpfZkhj-lhf9PCaxfMLTE25TlaQ8pQwglcH7gf_V7iWeNRVWlzSR-29HZ2kBOULe54S0JWnxqBYAWdFEzaoO6exhUXHBhna32wm9MlCAsKwizgRP9Q_WWTV5pTxeCe2sWXQFwfCbanoL42d6enoWyEoIEOljYzirukKnkmcBYCSNoarpWXVC7_WLyKV83Ah9yYHrUcd5czHzaIpcYM23WR6t0M3vW0jw0Kez0TmG8aRGJ_1W00

from abc import ABC
from typing import Iterable, Callable, List
import pyxmas.protocol as protocol
import pyxmas.protocol.messages as messages
import pyxmas.protocol.data as data


__all__ = [
    'RecommenderBehaviour',
    'StateError',
    'StateIdle',
    'StateComputingRecommendation',
    'StateWaitingRecommendationFeedback',
    'StateComputingComparativeExplanation',
    'StateComputingExplanation',
    'StateWaitingComparisonFeedback',
    'StateWaitingInvalidFeedback',
    'StateWaitingExplanationFeedback',
]


def _get_all_state_classes():
    return [
        StateError,
        StateIdle,
        StateComputingRecommendation,
        StateWaitingRecommendationFeedback,
        StateComputingComparativeExplanation,
        StateComputingExplanation,
        StateWaitingComparisonFeedback,
        StateWaitingInvalidFeedback,
        StateWaitingExplanationFeedback,
    ]


class RecommenderBehaviour(protocol.Protocol, ABC):
    def __init__(self, thread: str = None, impl: data.Types = None):
        super().__init__(thread, impl)

    def setup(self) -> None:
        for state in _get_all_state_classes():
            self.add_transitions(state, state.reachable_states(), error=StateError)

    async def on_error(self, error: Exception) -> None:
        ...

    async def compute_recommendation(self, message: data.Query) -> data.Recommendation:
        ...

    async def compute_explanation(self, message: data.Query, recommendation: data.Recommendation) -> data.Explanation:
        ...

    async def compute_contrastive_explanation(self,
                                              message: data.Query,
                                              recommendation: data.Recommendation,
                                              alternative: data.Recommendation) -> data.Explanation:
        ...

    async def is_valid(self,
                       message: data.Query,
                       recommendation: data.Recommendation,
                       alternative: data.Recommendation) -> bool:
        ...

    async def on_collision(self,
                           message: data.Query,
                           recommendation: data.Recommendation,
                           feature: data.Feature):
        ...

    async def on_disagree(self,
                          message: data.Query,
                          recommendation: data.Recommendation,
                          motivation: data.Motivation):
        ...

    async def on_accept(self,
                        message: data.Query,
                        recommendation: data.Recommendation,
                        explanation: data.Explanation = None):
        ...

    async def on_unclear(self,
                        message: data.Query,
                        recommendation: data.Recommendation,
                        explanation: data.Explanation
                        ):
        ...

    async def on_prefer_alternative(self,
                        message: data.Query,
                        recommendation: data.Recommendation,
                        alternative: data.Recommendation
                        ):
        ...

    async def on_override_alternative(self,
                        message: data.Query,
                        recommendation: data.Recommendation,
                        alternative: data.Recommendation
                        ):
        ...


class RecommenderState(protocol.State, ABC):
    def __init__(self, parent: RecommenderBehaviour):
        super().__init__(parent)

    @property
    def parent(self) -> RecommenderBehaviour:
        return self._parent

    @classmethod
    def reachable_states(cls) -> List[type]:
        ...

    async def run(self):
        try:
            self.log(f"Entering state {self.name()}")
            await self.action()
        except Exception as e:
            self.log(msg=f"Error in state {self.name()} | {str(e)}")
            self.memory["last_error"] = e
            self.set_next_state(StateError)
        finally:
            if self.next_state is None:
                self.log(f"Moving out from state {self.name()}, no next state")
            else:
                self.log(f"Moving from state {self.name()} to state {self.next_state.name()}")

    async def action(self):
        ...


class StateError(RecommenderState):
    async def action(self):
        e = self.memory["last_error"]
        if e is None:
            raise RuntimeError(f"No error to handle in {self.name()} state")
        self.log(msg=f"Handling error: {e}")
        await self.parent.on_error(e)
        self.log(msg=f"Handled error: {e}")
        self.set_next_state(StateIdle)

    @classmethod
    def reachable_states(cls) -> Iterable[type]:
        return [StateIdle]


class StateIdle(RecommenderState):
    async def action(self):
        self.log(msg="Waiting for a query...")
        message = await self.receive()
        self.log(msg=f"Received message {message}")
        message = self.wrap_message(message)
        if not isinstance(message, messages.QueryMessage):
            raise RuntimeError(f"Unexpected message type {type(message)} in {self.name()} state")
        self.memory['history'].append(message)
        self.log(msg=f"Stored message in history")
        self.set_next_state(StateComputingRecommendation)

    @classmethod
    def reachable_states(cls) -> Iterable[type]:
        return [StateComputingRecommendation]


class StateComputingRecommendation(RecommenderState):
    async def action(self):
        message = self.memory["history"][-1]
        self.log(msg=f"Retrieved last message from history: {message}")
        if message is None:
            raise RuntimeError("No message to compute recommendation from")
        if not isinstance(message, messages.QueryMessage):
            raise RuntimeError("Last message is not a query message")
        self.log(msg=f"Computing recommendation for query: {message.query}")
        recommendation = await self.parent.compute_recommendation(message.query)
        self.log(msg=f"Computed recommendation: {recommendation}")
        reply = message.make_recommendation_reply(recommendation)
        self.log(msg=f"Sending recommendation: {reply}...")
        await self.send(reply.delegate)
        self.log(msg=f"Recommendation sent")
        self.set_next_state(StateWaitingRecommendationFeedback)

    @classmethod
    def reachable_states(cls) -> Iterable[type]:
        return [StateWaitingRecommendationFeedback]


class BaseWaitingState(RecommenderState, ABC):
    def __init__(self, parent: RecommenderBehaviour):
        super().__init__(parent)
        self._handlers = {
            messages.AcceptMessage: self.handle_accept,
            messages.CollisionMessage: self.handle_collision,
            messages.DisapproveMessage: self.handle_disagree,
        }

    def add_handler_for(self, message_type: type, handler: Callable):
        self._handlers[message_type] = handler

    def remove_handlers_for(self, *message_types: type):
        for message_type in message_types:
            del self._handlers[message_type]

    async def handle_accept(self, message: messages.AcceptMessage):
        self.log(msg=f"Handling accept")
        await self.parent.on_accept(message.query, message.recommendation)
        self.log(msg=f"Handled accept")
        self.set_next_state(StateIdle)

    async def handle_collision(self, message: messages.CollisionMessage):
        self.log(msg=f"Handling collision over feature: {message.feature}")
        await self.parent.on_collision(message.query, message.recommendation, message.feature)
        self.log(msg=f"Handled collision over feature: {message.feature}")
        self.set_next_state(StateComputingRecommendation)

    async def handle_disagree(self, message: messages.DisapproveMessage):
        self.log(msg=f"Handling disapprove because of motivation: {message.motivation}")
        await self.parent.on_disagree(message.query, message.recommendation, message.motivation)
        self.log(msg=f"Handled disapprove because of motivation: {message.motivation}")
        self.set_next_state(StateComputingRecommendation)

    async def action(self):
        self.log(msg="Waiting for feedback...")
        message = await self.receive()
        self.log(msg=f"Received message {message}")
        message = self.wrap_message(message)
        self.memory['history'].append(message)
        self.log(msg="Store last message in history")
        for message_type, handler in self._handlers.items():
            if isinstance(message, message_type):
                handler(message)
                return
        del self.memory["history"][-1]
        self.log(msg="Remove last message from history")
        raise RuntimeError(f"Unexpected message type {type(message)} in {self.name()} state")

    @classmethod
    def reachable_states(cls) -> List[type]:
        return [StateIdle, StateComputingRecommendation]


class StateWaitingRecommendationFeedback(BaseWaitingState):
    def __init__(self, parent: RecommenderBehaviour):
        super().__init__(parent)
        self.add_handler_for(messages.WhyMessage, self.handle_why)
        self.add_handler_for(messages.WhyNotMessage, self.handle_why_not)

    def handle_why(self, message: messages.WhyMessage):
        self.log(msg=f"Received explanation request")
        self.set_next_state(StateComputingExplanation)


    def handle_why_not(self, message: messages.WhyNotMessage):
        self.log(msg=f"Received contrastive explanation request")
        self.set_next_state(StateComputingComparativeExplanation)

    @classmethod
    def reachable_states(cls) -> Iterable[type]:
        return super().reachable_states() + [StateComputingExplanation, StateComputingComparativeExplanation]


class StateComputingComparativeExplanation(RecommenderState):
    async def action(self):
        message = self.memory["history"][-1]
        self.log(msg=f"Retrieved last message from history: {message}")
        if message is None:
            raise RuntimeError("No message to compute recommendation from")
        if not isinstance(message, messages.WhyNotMessage):
            raise RuntimeError("Last message is not a contrastive explanation request")
        self.log(msg=f"Checking if alternative recommendation {message.alternative}, is valid for query {message.query}")
        is_valid = await self.parent.is_valid(message.query, message.recommendation, message.alternative)
        if is_valid:
            self.log(msg=f"Alternative recommendation {message.alternative} is valid for query {message.query}")
        else:
            self.log(msg=f"Alternative recommendation {message.alternative} is invalid for query {message.query}")
        self.log(msg=f"Computing contrastive explanation for query: {message.query}, "
                     f"recommendation: {message.recommendation}, "
                     f"and alternative: {message.alternative}")
        explanation = await self.parent.compute_contrastive_explanation(message.query, message.recommendation,
                                                                        message.alternative)
        self.log(msg=f"Computed contrastive explanation: {explanation}")
        if is_valid:
            reply = message.make_comparison_reply(explanation)
            self.log(f"Sending comparative reply {reply}")
        else:
            reply = message.make_invalid_alternative_reply(explanation)
            self.log(f"Sending invalid reply {reply}")
        await self.send(reply.delegate)
        self.log(msg=f"Reply sent")
        self.set_next_state(StateWaitingComparisonFeedback if is_valid else StateWaitingInvalidFeedback)

    @classmethod
    def reachable_states(cls) -> Iterable[type]:
        return [StateWaitingComparisonFeedback, StateWaitingInvalidFeedback]


class StateComputingExplanation(RecommenderState):
    async def action(self):
        message = self.memory["history"][-1]
        self.log(msg=f"Retrieved last message from history: {message}")
        if message is None:
            raise RuntimeError("No message to compute recommendation from")
        if not isinstance(message, messages.WhyMessage):
            raise RuntimeError("Last message is not an explanation request")
        self.log(msg=f"Computing explanation for query: {message.query}, and recommendation: {message.recommendation}")
        explanation = await self.parent.compute_explanation(message.query, message.recommendation)
        self.log(msg=f"Computed explanation: {explanation}")
        reply = message.make_more_details_reply(explanation)
        self.log(f"Sending more details reply {reply}")
        await self.send(reply.delegate)
        self.log(msg=f"Reply sent")
        self.set_next_state(StateWaitingExplanationFeedback)

    @classmethod
    def reachable_states(cls) -> Iterable[type]:
        return [StateWaitingExplanationFeedback]


class BaseWaitingContrastiveFeedbackState(BaseWaitingState):
    def __init__(self, parent: RecommenderBehaviour):
        super().__init__(parent)
        self.remove_handlers_for(messages.DisapproveMessage, messages.CollisionMessage)

    @classmethod
    def reachable_states(cls) -> Iterable[type]:
        lst = super().reachable_states()
        lst.remove(StateComputingRecommendation)
        return lst


class StateWaitingComparisonFeedback(BaseWaitingContrastiveFeedbackState):
    def __init__(self, parent: RecommenderBehaviour):
        super().__init__(parent)
        self.add_handler_for(messages.UnclearExplanationMessage, self.handle_prefer)

    def handle_prefer(self, message: messages.PreferAlternativeMessage):
        self.log(msg=f"Flagging as preferred recommendation {message.alternative} over {message.recommendation}")
        self.parent.on_prefer_alternative(message.query, message.recommendation, message.alternative)
        self.log(msg=f"Flagged as preferred recommendation {message.alternative} over {message.recommendation}")
        self.set_next_state(StateIdle)


class StateWaitingInvalidFeedback(BaseWaitingContrastiveFeedbackState):
    def __init__(self, parent: RecommenderBehaviour):
        super().__init__(parent)
        self.add_handler_for(messages.OverrideRecommendationMessage, self.handle_override)

    def handle_override(self, message: messages.OverrideRecommendationMessage):
        self.log(msg=f"Overriding recommendation {message.recommendation} with {message.alternative}")
        self.parent.on_override_alternative(message.query, message.recommendation, message.alternative)
        self.log(msg=f"Overridden recommendation {message.recommendation} with {message.alternative}")
        self.set_next_state(StateIdle)


class StateWaitingExplanationFeedback(BaseWaitingState):
    def __init__(self, parent: RecommenderBehaviour):
        super().__init__(parent)
        self.add_handler_for(messages.UnclearExplanationMessage, self.handle_unclear)

    def handle_unclear(self, message: messages.UnclearExplanationMessage):
        self.log(msg=f"Flagging as unclear: {message.explanation}")
        self.parent.on_unclear(message.query, message.recommendation, message.explanation)
        self.log(msg=f"Flagged as unclear: {message.explanation}")
        self.set_next_state(StateComputingExplanation)

    @classmethod
    def reachable_states(cls) -> Iterable[type]:
        return super().reachable_states() + [StateComputingExplanation]
