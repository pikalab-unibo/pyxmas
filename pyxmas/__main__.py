import pyxmas
import spade
import spade.agent
import spade.behaviour

from Expectation.explainee_imp import ExplaineeAgent
from Expectation.recommender_imp import RecommenderAgent

pyxmas.enable_logging()

with pyxmas.System() as system:

    with RecommenderAgent("recommender@localhost", "password") as recommender:
        with ExplaineeAgent(user_id="34",jid="explainee@localhost", password="password") as explainee:
                    try:
                        explainee.sync_await(timeout=200)
                        recommender.sync_await(timeout=200)
                    except KeyboardInterrupt:
                        recommender.stop()
                        explainee.stop()

