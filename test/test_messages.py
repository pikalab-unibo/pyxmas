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
        self.query_message = messages.QueryMessage.create(
            sender="user@host.any",
            to="agent@host.any",
            impl=self._impl,
            query=self.parse_query("question?"),
            thread='conversation#1',
            depth=0
        )
        self.recommendation_message = messages.RecommendationMessage.create(
            sender="agent@host.any",
            to="user@host.any",
            impl=self._impl,
            query=self.parse_query("question?"),
            recommendation=self.parse_recommendation("answer!"),
            thread='conversation#1',
            depth=1
        )
        self.why_message = messages.WhyMessage.create(
            sender="user@host.any",
            to="agent@host.any",
            impl=self._impl,
            query=self.parse_query("question?"),
            recommendation=self.parse_recommendation("answer!"),
            thread='conversation#1',
            depth=2
        )
        self.why_not_message = messages.WhyNotMessage.create(
            sender="user@host.any",
            to="agent@host.any",
            impl=self._impl,
            query=self.parse_query("question?"),
            recommendation=self.parse_recommendation("answer!"),
            alternative=self.parse_recommendation("another_answer!"),
            thread='conversation#1',
            depth=2
        )
        self.accept_recommendation = messages.AcceptMessage.create(
            sender="user@host.any",
            to="agent@host.any",
            impl=self._impl,
            query=self.parse_query("question?"),
            recommendation=self.parse_recommendation("answer!"),
            thread='conversation#1',
            depth=2
        )
        self.recommendation_collides = messages.CollisionMessage.create(
            sender="user@host.any",
            to="agent@host.any",
            impl=self._impl,
            query=self.parse_query("question?"),
            recommendation=self.parse_recommendation("answer!"),
            feature=self.parse_feature("i_dont_really_like_answer"),
            thread='conversation#1',
            depth=2
        )
        self.disapprove_recommendation = messages.DisapproveMessage.create(
            sender="user@host.any",
            to="agent@host.any",
            impl=self._impl,
            query=self.parse_query("question?"),
            recommendation=self.parse_recommendation("answer!"),
            motivation=self.parse_motivation("answer_is_shitty!"),
            thread='conversation#1',
            depth=2
        )
        self.new_recommendation = messages.RecommendationMessage.create(
            sender="agent@host.any",
            to="user@host.any",
            impl=self._impl,
            query=self.parse_query("question?"),
            recommendation=self.parse_recommendation("another_answer!"),
            thread='conversation#1',
            depth=3
        )
        self.explanation1 = messages.MoreDetailsMessage.create(
            sender="agent@host.any",
            to="user@host.any",
            impl=self._impl,
            query=self.parse_query("question?"),
            recommendation=self.parse_recommendation("answer!"),
            explanation=self.parse_explanation("quick_and_dirty_explanation"),
            thread='conversation#1',
            depth=3
        )
        self.comparison = messages.ComparisonMessage.create(
            sender="agent@host.any",
            to="user@host.any",
            impl=self._impl,
            query=self.parse_query("question?"),
            recommendation=self.parse_recommendation("answer!"),
            alternative=self.parse_recommendation("another_answer!"),
            explanation=self.parse_explanation("answer_is_better"),
            thread='conversation#1',
            depth=3
        )
        self.invalid = messages.InvalidAlternativeMessage.create(
            sender="agent@host.any",
            to="user@host.any",
            impl=self._impl,
            query=self.parse_query("question?"),
            recommendation=self.parse_recommendation("answer!"),
            alternative=self.parse_recommendation("another_answer!"),
            explanation=self.parse_explanation("another_answer_is_invalid"),
            thread='conversation#1',
            depth=3
        )
        self.unclear = messages.UnclearExplanationMessage.create(
            sender="user@host.any",
            to="agent@host.any",
            impl=self._impl,
            query=self.parse_query("question?"),
            recommendation=self.parse_recommendation("answer!"),
            explanation=self.parse_explanation("quick_and_dirty_explanation"),
            thread='conversation#1',
            depth=4
        )
        self.accept_recommendation_after_explanation = messages.AcceptMessage.create(
            sender="user@host.any",
            to="agent@host.any",
            impl=self._impl,
            query=self.parse_query("question?"),
            recommendation=self.parse_recommendation("answer!"),
            explanation=self.parse_explanation("quick_and_dirty_explanation"),
            thread='conversation#1',
            depth=4
        )
        self.recommendation_collides_after_explanation = messages.CollisionMessage.create(
            sender="user@host.any",
            to="agent@host.any",
            impl=self._impl,
            query=self.parse_query("question?"),
            recommendation=self.parse_recommendation("answer!"),
            feature=self.parse_feature("i_dont_really_like_answer"),
            explanation=self.parse_explanation("quick_and_dirty_explanation"),
            thread='conversation#1',
            depth=4
        )
        self.disapprove_recommendation_after_explanation = messages.DisapproveMessage.create(
            sender="user@host.any",
            to="agent@host.any",
            impl=self._impl,
            query=self.parse_query("question?"),
            recommendation=self.parse_recommendation("answer!"),
            motivation=self.parse_motivation("answer_is_shitty!"),
            explanation=self.parse_explanation("quick_and_dirty_explanation"),
            thread='conversation#1',
            depth=4
        )
        self.accept_recommendation_after_comparison = messages.AcceptMessage.create(
            sender="user@host.any",
            to="agent@host.any",
            impl=self._impl,
            query=self.parse_query("question?"),
            recommendation=self.parse_recommendation("answer!"),
            explanation=self.parse_explanation("answer_is_better"),
            thread='conversation#1',
            depth=4
        )
        self.prefer_alternative_after_comparison = messages.PreferAlternativeMessage.create(
            sender="user@host.any",
            to="agent@host.any",
            impl=self._impl,
            query=self.parse_query("question?"),
            recommendation=self.parse_recommendation("answer!"),
            alternative=self.parse_recommendation("another_answer!"),
            thread='conversation#1',
            depth=4
        )
        self.override_invalid_recommendation = messages.OverrideRecommendationMessage.create(
            sender="user@host.any",
            to="agent@host.any",
            impl=self._impl,
            query=self.parse_query("question?"),
            recommendation=self.parse_recommendation("answer!"),
            alternative=self.parse_recommendation("another_answer!"),
            thread='conversation#1',
            depth=4
        )
        self.explanation2 = messages.MoreDetailsMessage.create(
            sender="agent@host.any",
            to="user@host.any",
            impl=self._impl,
            query=self.parse_query("question?"),
            recommendation=self.parse_recommendation("answer!"),
            explanation=self.parse_explanation("detailed_explanation"),
            thread='conversation#1',
            depth=5
        )

    def parse_query(self, string):
        return self._impl.query_type.parse(string)

    def parse_recommendation(self, string):
        return self._impl.recommendation_type.parse(string)

    def parse_feature(self, string):
        return self._impl.feature_type.parse(string)

    def parse_motivation(self, string):
        return self._impl.motivation_type.parse(string)

    def parse_explanation(self, string):
        return self._impl.explanation_type.parse(string)

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
        self.query_message_assertions(self.query_message)

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
        self.recommendation_message_assertions(self.recommendation_message)

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
        msg = self.query_message.make_recommendation_reply(self.parse_recommendation("answer!"))
        self.assertEqual(msg, self.recommendation_message)
        self.assertFalse(msg.is_terminal)

    def test_why_message_from_recommendation(self):
        msg = self.recommendation_message.make_why_reply()
        self.assertEqual(msg, self.why_message)
        self.assertFalse(msg.is_terminal)

    def test_why_not_message_from_recommendation(self):
        msg = self.recommendation_message.make_why_not_reply(self.parse_recommendation("another_answer!"))
        self.assertEqual(msg, self.why_not_message)
        self.assertFalse(msg.is_terminal)

    def test_accept_message_from_recommendation(self):
        msg = self.recommendation_message.make_accept_reply()
        self.assertEqual(msg, self.accept_recommendation)
        self.assertTrue(msg.is_terminal)

    def test_collision_message_from_recommendation(self):
        msg = self.recommendation_message.make_collision_reply(self.parse_feature("i_dont_really_like_answer"))
        self.assertEqual(msg, self.recommendation_collides)
        self.assertFalse(msg.is_terminal)

    def test_disapprove_message_from_recommendation(self):
        msg = self.recommendation_message.make_disapprove_reply(self.parse_motivation("answer_is_shitty!"))
        self.assertEqual(msg, self.disapprove_recommendation)
        self.assertFalse(msg.is_terminal)

    def test_recommendation_message_from_collision(self):
        msg = self.recommendation_collides.make_recommendation_reply(self.parse_recommendation("another_answer!"))
        self.assertEqual(msg, self.new_recommendation)
        self.assertFalse(msg.is_terminal)

    def test_recommendation_message_from_disapprove(self):
        msg = self.disapprove_recommendation.make_recommendation_reply(self.parse_recommendation("another_answer!"))
        self.assertEqual(msg, self.new_recommendation)
        self.assertFalse(msg.is_terminal)

    def test_more_details_message_from_why(self):
        msg = self.why_message.make_more_details_reply(self.parse_explanation("quick_and_dirty_explanation"))
        self.assertEqual(msg, self.explanation1)
        self.assertFalse(msg.is_terminal)

    def test_comparison_message_from_why_not(self):
        msg = self.why_not_message.make_comparison_reply(self.parse_explanation("answer_is_better"))
        self.assertEqual(msg, self.comparison)
        self.assertFalse(msg.is_terminal)

    def test_invalid_alternative_message_from_why_not(self):
        msg = self.why_not_message.make_invalid_alternative_reply(self.parse_explanation("another_answer_is_invalid"))
        self.assertEqual(msg, self.invalid)
        self.assertFalse(msg.is_terminal)

    def test_unclear_explanation_message_from_why_not(self):
        msg = self.explanation1.make_unclear_reply()
        self.assertEqual(msg, self.unclear)
        self.assertFalse(msg.is_terminal)

    def test_accept_message_from_more_details(self):
        msg = self.explanation1.make_accept_reply()
        self.assertEqual(msg, self.accept_recommendation_after_explanation)
        self.assertTrue(msg.is_terminal)

    def test_collision_message_from_more_details(self):
        msg = self.explanation1.make_collision_reply(self.parse_feature("i_dont_really_like_answer"))
        self.assertEqual(msg, self.recommendation_collides_after_explanation)
        self.assertFalse(msg.is_terminal)

    def test_disapprove_message_from_more_details(self):
        msg = self.explanation1.make_disapprove_reply(self.parse_motivation("answer_is_shitty!"))
        self.assertEqual(msg, self.disapprove_recommendation_after_explanation)
        self.assertFalse(msg.is_terminal)

    def test_accept_message_from_comparison(self):
        msg = self.comparison.make_accept_reply()
        self.assertEqual(msg, self.accept_recommendation_after_comparison)
        self.assertTrue(msg.is_terminal)

    def test_prefer_alternative_message_from_comparison(self):
        msg = self.comparison.make_prefer_alternative_reply()
        self.assertEqual(msg, self.prefer_alternative_after_comparison)
        self.assertTrue(msg.is_terminal)

    def test_override_message_from_invalid(self):
        msg = self.invalid.make_override_recommendation_reply()
        self.assertEqual(msg, self.override_invalid_recommendation)
        self.assertTrue(msg.is_terminal)

    def test_more_details_message_from_unclear(self):
        msg = self.unclear.make_more_details_reply(self.parse_explanation("detailed_explanation"))
        self.assertEqual(msg, self.explanation2)
        self.assertFalse(msg.is_terminal)


if __name__ == '__main__':
    unittest.main()
