import unittest
import pyxmas.protocol.messages as messages
import pyxmas.protocol.data as data
import pyxmas.protocol.data.strings as strings
from spade.message import Message as SpadeMessage
import aioxmpp


def jid(string: str) -> aioxmpp.JID:
    return aioxmpp.JID.fromstr(string)


class TestMessageWrappers(unittest.TestCase):

    def __init__(self, methodName='runTest', impl: data.Types = strings.Types()):
        super().__init__(methodName)
        self._impl = impl

    def parse_query(self, string):
        return self._impl.query_type.parse(string)

    def parse_recommendation(self, string):
        return self._impl.recommendation_type.parse(string)

    def query_message_assertions(self, msg: messages.MessageLike, query="question?", query2="another_question?",
                                 sender="user@host.any", to="agent@host.any", thread="conversation#1"):
        self.assertIsInstance(msg, messages.MessageLike)
        self.assertIsInstance(msg, messages.QueryMessage)
        self.assertIsInstance(msg.delegate, messages.MessageLike)
        self.assertIsInstance(msg.delegate, SpadeMessage)
        self.assertEqual(msg.to, jid(to))
        self.assertEqual(msg.sender, jid(sender))
        self.assertEqual(msg.thread, thread)
        self.assertEqual(msg.type, messages.QueryMessage.__name__)
        self.assertEqual(msg.depth, 0)
        self.assertEqual(msg.query, self.parse_query(query))
        self.assertTrue(messages.create_xml_tag("query", self.parse_query(query)) in msg.body)
        msg.query = self.parse_query(query2)
        self.assertNotEqual(msg.query, self.parse_query(query))
        self.assertFalse(messages.create_xml_tag("query", self.parse_query(query)) in msg.body)
        self.assertEqual(msg.query, self.parse_query(query2))
        self.assertTrue(messages.create_xml_tag("query", self.parse_query(query2)) in msg.body)

    def test_query_message_creation(self):
        msg = messages.QueryMessage.create(
            sender="user@host.any",
            to="agent@host.any",
            impl=self._impl,
            query=self.parse_query("question?"),
            thread='conversation#1',
            depth=0
        )
        self.query_message_assertions(msg)

    def test_query_message_wrapping(self):
        msg = messages.QueryMessage.wrap(
            SpadeMessage(
                sender="user@host.any",
                to="agent@host.any",
                thread='conversation#1',
                body=messages.create_xml_tag("query", self.parse_query("question?")),
                metadata={
                    messages.METADATA_TYPE: messages.QueryMessage.__name__,
                    messages.METADATA_DEPTH: "0"
                }
            ),
            self._impl
        )
        self.query_message_assertions(msg)

    def recommendation_message_assertions(self, msg: messages.MessageLike, query="question?", recommendation="answer!",
                                          recommendation2="another_answer!", sender="agent@host.any",
                                          to="user@host.any", thread="conversation#1"):
        self.assertIsInstance(msg, messages.MessageLike)
        self.assertIsInstance(msg, messages.RecommendationMessage)
        self.assertIsInstance(msg.delegate, messages.MessageLike)
        self.assertIsInstance(msg.delegate, SpadeMessage)
        self.assertEqual(msg.to, jid(to))
        self.assertEqual(msg.sender, jid(sender))
        self.assertEqual(msg.thread, thread)
        self.assertEqual(msg.type, messages.RecommendationMessage.__name__)
        self.assertEqual(msg.depth, 1)
        self.assertEqual(msg.query, self.parse_query(query))
        self.assertEqual(msg.recommendation, self.parse_recommendation(recommendation))
        self.assertTrue(messages.create_xml_tag("query", self.parse_query(query)) in msg.body)
        self.assertTrue(messages.create_xml_tag("recommendation", self.parse_recommendation(recommendation)) in msg.body)
        msg.recommendation = self.parse_recommendation(recommendation2)
        self.assertEqual(msg.query, self.parse_query(query))
        self.assertNotEqual(msg.recommendation, self.parse_recommendation(recommendation))
        self.assertTrue(messages.create_xml_tag("query", self.parse_query(query)) in msg.body)
        self.assertFalse(messages.create_xml_tag("recommendation", self.parse_recommendation(recommendation)) in msg.body)
        self.assertEqual(msg.recommendation, self.parse_recommendation(recommendation2))
        self.assertTrue(messages.create_xml_tag("recommendation", self.parse_recommendation(recommendation2)) in msg.body)

    def test_recommendation_message_creation(self):
        msg = messages.RecommendationMessage.create(
            sender="agent@host.any",
            to="user@host.any",
            impl=self._impl,
            query=self.parse_query("question?"),
            recommendation=self.parse_recommendation("answer!"),
            thread='conversation#1',
            depth=1
        )
        self.recommendation_message_assertions(msg)

    def test_recommendation_message_wrapping(self):
        msg = messages.RecommendationMessage.wrap(
            SpadeMessage(
                sender="agent@host.any",
                to="user@host.any",
                thread='conversation#1',
                body=f"""
                {messages.create_xml_tag("query", self.parse_query("question?"))}
                {messages.create_xml_tag("recommendation", self.parse_query("answer!"))}
                """,
                metadata={
                    messages.METADATA_TYPE: messages.RecommendationMessage.__name__,
                    messages.METADATA_DEPTH: "1"
                }
            ),
            self._impl
        )
        self.recommendation_message_assertions(msg)

    def test_recommendation_message_from_query(self):
        msg = messages.QueryMessage.create(
            sender="user@host.any",
            to="agent@host.any",
            impl=self._impl,
            query=self.parse_query("question?"),
            thread='conversation#1'
        )
        msg = msg.make_recommendation_reply(self.parse_recommendation("answer!"))
        self.recommendation_message_assertions(msg)


if __name__ == '__main__':
    unittest.main()
