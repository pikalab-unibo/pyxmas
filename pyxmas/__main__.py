import pyxmas
import spade
import spade.agent
import spade.behaviour

from Expectation.explainee_imp import ExplaineeAgent
from Expectation.recommender_imp import RecommenderAgent

pyxmas.enable_logging()

with pyxmas.System() as system:

    with RecommenderAgent("recommender@localhost", "password") as recommender:
        with ExplaineeAgent("explainee@localhost", "password") as explainee:
                    try:
                        explainee.sync_await(timeout=20)
                        recommender.sync_await(timeout=20)
                    except KeyboardInterrupt:
                        recommender.stop()
                        explainee.stop()

