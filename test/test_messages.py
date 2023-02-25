import unittest
import pyxmas.protocol.messages as messages
import pyxmas.protocol.data.strings as strings
from spade.message import Message as SpadeMessage
import aioxmpp

impl = strings.Types()


def jid(string: str) -> aioxmpp.JID:
    return aioxmpp.JID.fromstr(string)


class TestMessageWrappers(unittest.TestCase):

    def query_message_assertions(self, msg, query="question?", query2="another_question?", sender="user@host.any",
                                 to="agent@host.any", thread="conversation#1"):
        self.assertIsInstance(msg, messages.QueryMessage)
        self.assertIsInstance(msg.delegate, SpadeMessage)
        self.assertEqual(msg.to, jid(to))
        self.assertEqual(msg.sender, jid(sender))
        self.assertEqual(msg.thread, thread)
        self.assertEqual(msg.metadata, {messages.METADATA_TYPE: messages.QueryMessage.__name__})
        self.assertEqual(msg.query, impl.query_type.parse(query))
        self.assertTrue(messages.create_xml_tag("query", impl.query_type.parse(query)) in msg.body)
        msg.query = impl.query_type.parse(query2)
        self.assertNotEqual(msg.query, impl.query_type.parse(query))
        self.assertFalse(messages.create_xml_tag("query", impl.query_type.parse(query)) in msg.body)
        self.assertEqual(msg.query, impl.query_type.parse(query2))
        self.assertTrue(messages.create_xml_tag("query", impl.query_type.parse(query2)) in msg.body)

    def test_query_message_creation(self):
        msg = messages.QueryMessage.create(
            sender="user@host.any",
            to="agent@host.any",
            impl=impl,
            query=impl.query_type.parse("question?"),
            thread='conversation#1'
        )
        self.query_message_assertions(msg)

    def test_query_message_wrapping(self):
        msg = messages.QueryMessage.wrap(
            SpadeMessage(
                sender="user@host.any",
                to="agent@host.any",
                thread='conversation#1',
                body=messages.create_xml_tag("query", impl.query_type.parse("question?"))
            ),
            impl
        )
        self.query_message_assertions(msg)


if __name__ == '__main__':
    unittest.main()
