# https://www.plantuml.com/plantuml/svg/hL8zJ_Cm4DxzAxmrUVLse6C7LAaD4WEKHgew80OhkROM_h1i9z1_pr5BD2376CGOv_cuvvvREC-ixwGWHzu21MdyYRRW6ikDvrgHntzFT3gzfZl6FLU76Xej9QYMlV-bSxhfm9wAJKcYW3bz2S_KWZDQEQ1xgoLb1r2Ua3XfwBTrO5VGS1VSFWEBkYGHtCMqmrVAbUby11TyC1_ghfz7j9BPbrg8Cwge_z_ydBxYZXbZTTS32joLv3k55NZWmY5rTpo5WOVlOtjRg-hL2AO-VC4pXADdzLKYtLTIEsFnKL8yu5Or0fWDC-P8N8hCf-JqMc6psMePDLSvHI-rDCoYG0y3bz3xlVP5FIb94fhkCSqTFwE0vqwhAvpbyeMnwadOUfgLVI13KgpTVCg3XJtO0kUhopy8FaF9MzKpmTiYA_FiDvbdqSpvb1wivIsSxsG1gksaU0C0

from abc import ABC
from typing import Iterable, List
import pyxmas.protocol as protocol
import pyxmas.protocol.messages as messages
import pyxmas.protocol.data as data


__all__ = [
    'ExplaineeBehaviour',
    'StateError',
    'StateInit',
    'StateAwaitingRecommendation',
    'StateAwaitingDetails',
    'StateAwaitingComparativeExplanation',
    'StateHandlingComparison',
    'StateHandlingInvalid',
]


def _get_all_state_classes():
    return [
        StateError,
        StateInit,
        StateAwaitingRecommendation,
        StateAwaitingDetails,
        StateAwaitingComparativeExplanation,
        StateHandlingComparison,
        StateHandlingInvalid
    ]


class ExplaineeBehaviour(protocol.Protocol, ABC):
    def __init__(self, query: data.Query, recipient: str, thread: str = None, impl: data.Types = None):
        super().__init__(thread, impl)
        self._query = query
        self._recipient = recipient

    def setup(self) -> None:
        for state in _get_all_state_classes():
            self.add_transitions(state, state.reachable_states(), error=StateError)

    @property
    def query(self) -> data.Query:
        return self._query

    @property
    def recipient(self) -> str:
        return self._recipient

    async def on_error(self, error: Exception) -> None:
        ...

    async def handle_recommendation(self,
                                    message: messages.RecommendationMessage
                                    ) -> messages.ResponseToRecommendationMessage:
        ...

    async def handle_details(self,
                             message: messages.MoreDetailsMessage
                             ) -> messages.ResponseToMoreDetailsMessage:
        ...

    async def handle_comparison(self,
                                message: messages.ComparisonMessage
                                ) -> messages.ResponseToComparisonMessage:
        ...

    async def handle_invalid_alternative(self,
                                         message: messages.InvalidAlternativeMessage
                                         ) -> messages.ResponseToInvalidAlternativeMessage:
        ...


class ExplaineeState(protocol.State, ABC):
    def __init__(self, parent: ExplaineeBehaviour):
        super().__init__(parent, parent.thread)

    @property
    def parent(self) -> ExplaineeBehaviour:
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


class StateError(ExplaineeState):
    async def action(self):
        e = self.memory["last_error"]
        if e is None:
            raise RuntimeError(f"No error to handle in {self.name()} state")
        self.log(msg=f"Handling error: {e}")
        await self.parent.on_error(e)
        self.log(msg=f"Handled error: {e}")
        self.set_next_state(StateInit)

    @classmethod
    def reachable_states(cls) -> Iterable[type]:
        return [StateInit]


class StateEnd(ExplaineeState):
    async def action(self):
        self.log(msg=f"Ok, I'm done")
        self.kill(0)

    @classmethod
    def reachable_states(cls) -> Iterable[type]:
        return []


class StateInit(ExplaineeState):
    async def action(self):
        self.log(msg=f"Issuing query ${self.parent.query}")
        message = messages.QueryMessage(
            query=self.parent.query,
            to=self.parent.recipient
        )
        await self.send(message)
        self.memory['history'].append(message)
        self.log(msg=f"Sent ${message}")
        self.set_next_state(StateAwaitingRecommendation)

    @classmethod
    def reachable_states(cls) -> Iterable[type]:
        return [StateAwaitingRecommendation]


class StateAwaitingRecommendation(ExplaineeState):
    async def action(self):
        message = await self.receive()
        if message is None:
            raise RuntimeError("No actual message received")
        self.log(msg=f"Received message {message}")
        message = self.wrap_message(message)
        self.memory['history'].append(message)
        if not isinstance(message, messages.RecommendationMessage):
            raise RuntimeError("Last message is not a recommendation message")
        self.log(msg=f"Computing answer for recommendation: {message.recommendation}")
        answer = self.parent.handle_recommendation(message)
        self.log(msg=f"Computed answer for recommendation {message.recommendation}: ${answer}")
        await self.send(answer)
        self.log(msg=f"Sent answer for recommendation {message.recommendation}: ${answer}")
        self.memory['history'].append(answer)
        if isinstance(answer, messages.DisapproveMessage) or isinstance(answer, messages.CollisionMessage):
            self.set_next_state(StateAwaitingRecommendation)
        elif isinstance(answer, messages.WhyMessage):
            self.set_next_state(StateAwaitingDetails)
        elif isinstance(answer, messages.WhyNotMessage):
            self.set_next_state(StateAwaitingComparativeExplanation)
        elif isinstance(answer, messages.AcceptMessage):
            self.set_next_state(StateEnd)
        else:
            raise RuntimeError(f"Method {self.parent.handle_recommendation.__name__} returned unexpected message type: "
                               f"{type(answer)}")

    @classmethod
    def reachable_states(cls) -> Iterable[type]:
        return [StateAwaitingRecommendation, StateAwaitingDetails, StateAwaitingComparativeExplanation, StateEnd]


class StateAwaitingDetails(ExplaineeState):
    async def action(self):
        message = await self.receive()
        if message is None:
            raise RuntimeError("No actual message received")
        self.log(msg=f"Received message {message}")
        message = self.wrap_message(message)
        self.memory['history'].append(message)
        if not isinstance(message, messages.MoreDetailsMessage):
            raise RuntimeError("Last message is not an explanation message")
        self.log(msg=f"Computing answer for explanation: {message.explanation}")
        answer = self.parent.handle_details(message)
        self.log(msg=f"Computed answer for explanation {message.explanation}: ${answer}")
        await self.send(answer)
        self.log(msg=f"Sent answer for explanation {message.explanation}: ${answer}")
        self.memory['history'].append(answer)
        if isinstance(answer, messages.DisapproveMessage) or isinstance(answer, messages.CollisionMessage):
            self.set_next_state(StateAwaitingRecommendation)
        elif isinstance(answer, messages.UnclearExplanationMessage):
            self.set_next_state(StateAwaitingDetails)
        elif isinstance(answer, messages.AcceptMessage):
            self.set_next_state(StateEnd)
        else:
            raise RuntimeError(f"Method {self.parent.handle_details.__name__} returned unexpected message type: "
                               f"{type(answer)}")

    @classmethod
    def reachable_states(cls) -> Iterable[type]:
        return [StateAwaitingRecommendation, StateAwaitingDetails, StateEnd]


class StateAwaitingComparativeExplanation(ExplaineeState):
    async def action(self):
        message = await self.receive()
        if message is None:
            raise RuntimeError("No actual message received")
        self.log(msg=f"Received message {message}")
        message = self.wrap_message(message)
        self.memory['history'].append(message)
        if isinstance(message, messages.ComparisonMessage):
            self.log(msg=f"Received comparison message: ${message}")
            self.set_next_state(StateHandlingComparison)
        elif isinstance(message, messages.InvalidAlternativeMessage):
            self.log(msg=f"Received invalid alternative message: ${message}")
            self.set_next_state(StateHandlingInvalid)
        else:
            raise RuntimeError("Last message is not a contrastive explanation message")

    @classmethod
    def reachable_states(cls) -> Iterable[type]:
        return [StateHandlingComparison, StateHandlingInvalid]


class StateHandlingComparison(ExplaineeState):
    async def action(self):
        message = self.parent.memory["history"][-1]
        if message is None:
            raise RuntimeError("No message to compute handle")
        if not isinstance(message, messages.ComparisonMessage):
            raise RuntimeError("Last message is not a comparison message")
        self.log(msg=f"Computing answer for message: {message}")
        answer = self.parent.handle_comparison(message)
        self.log(msg=f"Computed answer for comparison: ${answer}")
        await self.send(answer)
        self.log(msg=f"Sent answer for comparison: ${answer}")
        self.memory['history'].append(answer)
        if isinstance(answer, messages.PreferAlternativeMessage) or isinstance(answer, messages.AcceptMessage):
            self.set_next_state(StateEnd)
        else:
            raise RuntimeError(f"Method {self.parent.handle_comparison.__name__} returned unexpected message type: "
                               f"{type(answer)}")

    @classmethod
    def reachable_states(cls) -> Iterable[type]:
        return [StateEnd]


class StateHandlingInvalid(ExplaineeState):
    async def action(self):
        message = self.parent.memory["history"][-1]
        if message is None:
            raise RuntimeError("No message to handle")
        if not isinstance(message, messages.InvalidAlternativeMessage):
            raise RuntimeError("Last message is not an invalid alternative message")
        self.log(msg=f"Computing answer for message: {message}")
        answer = self.parent.handle_invalid_alternative(message)
        self.log(msg=f"Computed answer for comparison: ${answer}")
        await self.send(answer)
        self.log(msg=f"Sent answer for comparison: ${answer}")
        self.memory['history'].append(answer)
        if isinstance(answer, messages.OverrideRecommendationMessage) or isinstance(answer, messages.AcceptMessage):
            self.set_next_state(StateEnd)
        else:
            raise RuntimeError(f"Method {self.parent.handle_invalid_alternative.__name__} returned unexpected "
                               f"message type: {type(answer)}")

    @classmethod
    def reachable_states(cls) -> Iterable[type]:
        return [StateEnd]
