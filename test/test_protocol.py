import test
import unittest
import pyxmas.protocol.recommender
from pyxmas.protocol.messages import get_default_data_types


class TestRecommenderAgent(test.TestAgent):
    class TestRecommenderProtocol(pyxmas.protocol.recommender.RecommenderBehaviour):
        def __init__(self):
            super().__init__(impl=get_default_data_types())

    async def setup(self):
        self.add_behaviour(self.TestRecommenderProtocol())


class TestExample(test.SharedXmppServiceTestCase):
    def test_loading_recommender_behaviour(self):
        with TestRecommenderAgent("alice") as agent:
            agent.sync_await(timeout=10)


if __name__ == '__main__':
    unittest.main()
