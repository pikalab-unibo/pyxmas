from abc import ABC
import pyxmas.protocol as protocol
import pyxmas.protocol.messages as messages
import pyxmas.protocol.data as data


# https://www.plantuml.com/plantuml/svg/fLAnJiCm5Dpz5TwQ83hGiGEgH5k9eK0ZLHqGWuaVhLNRYMmdqB_73h8Qi1mJTOlUkxlS-Tv26w9C8pWwCWeOH6tEc88k5QiDgoHwlNd3q-aztXDcc3piDAXj0-gC_Wxm77_-Z71ZPrY0rkG0A0GwkOTAr8qR5r1MGe2anFtEYdIOR9kZ26IEIx_0gjiGJpOLrXQ6K8phauIRDG1z9-N96lYzo8eS3J8YiGSvdG_tidFyV4h-OVZ1x8PpfZkhj-lhf9PCaxfMLTE25TlaQ8pQwglcH7gf_V7iWeNRVWlzSR-29HZ2kBOULe54S0JWnxqBYAWdFEzaoO6exhUXHBhna32wm9MlCAsKwizgRP9Q_WWTV5pTxeCe2sWXQFwfCbanoL42d6enoWyEoIEOljYzirukKnkmcBYCSNoarpWXVC7_WLyKV83Ah9yYHrUcd5czHzaIpcYM23WR6t0M3vW0jw0Kez0TmG8aRGJ_1W00


class RecommenderBehaviour(protocol.Protocol, ABC):
    def __init__(self, thread: str = None, impl: data.Types = None):
        super().__init__(thread, impl)

    async def on_error(self, error: Exception) -> None:
        ...

    async def compute_recommendation(self, message: data.Query) -> data.Recommendation:
        ...


class RecommenderState(protocol.State, ABC):
    def __init__(self, parent: RecommenderBehaviour):
        super().__init__(parent)

    @property
    def parent(self) -> RecommenderBehaviour:
        return self._parent


class StateRecommenderError(RecommenderState):
    async def run(self):
        e = self.memory["last_error"]
        if e is None:
            raise RuntimeError("No error to handle in error state")
        self.log(msg=f"Handling error: {e}")
        await self.parent.on_error(e)
        self.log(msg=f"Handled error: {e}, going back to idle")
        self.set_next_state(StateIdle)


class StateIdle(RecommenderState):
    async def run(self):
        self.log(msg="Idle. Waiting for a query...")
        message = await self.receive()
        self.log(msg=f"Received message {message}")
        try:
            message = self.wrap_message(message)
            if not isinstance(message, messages.QueryMessage):
                raise RuntimeError(f"Un message type {type(message)} in idle state")
            self.memory['history'].append(message)
            self.log(msg=f"Going to computing recommendation state")
            self.set_next_state(StateComputingRecommendation)
        except Exception as e:
            self.log(msg=f"str(e). Going to error state")
            self.memory["last_error"] = e
            self.set_next_state(StateRecommenderError)


class StateComputingRecommendation(RecommenderState):
    async def run(self):
        message = self.memory["history"][-1]
        if message is None:
            raise RuntimeError("No message to compute recommendation from")
        if not isinstance(message, messages.QueryMessage):
            raise RuntimeError("Last message is not a query message")
        self.log(msg=f"Handling query: {message.query}")
        recommendation = await self.parent.compute_recommendation(message.query)
        self.log(msg=f"Computed recommendation: {recommendation}")
        reply = message.make_recommendation_reply(recommendation)
        self.log(msg=f"Sending recommendation: {reply}")
        await self.send(reply.delegate)
        self.log(msg=f"Sent recommendation: {reply}, going to waiting recommendation feedback state")
        self.set_next_state(StateWaitingRecommendationFeedback)


class StateWaitingRecommendationFeedback(RecommenderState):
    async def run(self):
        self.log(msg="Waiting for a recommendation feedback...")
        message = await self.receive()
        self.log(msg=f"Received message {message}")
        try:
            message = self.wrap_message(message)
            # TODO: wip
        except Exception as e:
            self.log(msg=f"str(e). Going to error state")
            self.memory["last_error"] = e
            self.set_next_state(StateRecommenderError)
