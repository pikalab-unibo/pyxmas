import unittest
import pyxmas.protocol.data.strings as strings


string_types = strings.Types()


class TestStringTypes(unittest.TestCase):
    def test_query_type(self):
        source = "query"
        expected = strings.QueryString(source)
        self.assertEqual(expected, string_types.query_type("query"))
        self.assertEqual(expected, string_types.query_type.parse("query"))
        self.assertEqual(source, expected.serialize())
        self.assertEqual(source, expected.content)

    def test_recommendation_type(self):
        source = "recomm"
        expected = strings.RecommendationString(source)
        self.assertEqual(expected, string_types.recommendation_type("recomm"))
        self.assertEqual(expected, string_types.recommendation_type.parse("recomm"))
        self.assertEqual(source, expected.serialize())
        self.assertEqual(source, expected.content)

    def test_explanation_type(self):
        source = "expl"
        expected = strings.ExplanationString(source)
        self.assertEqual(expected, string_types.explanation_type("expl"))
        self.assertEqual(expected, string_types.explanation_type.parse("expl"))
        self.assertEqual(source, expected.serialize())
        self.assertEqual(source, expected.content)

    def test_motivation_type(self):
        source = "motivation"
        expected = strings.ExplanationString(source)
        self.assertEqual(expected, string_types.motivation_type("motivation"))
        self.assertEqual(expected, string_types.motivation_type.parse("motivation"))
        self.assertEqual(source, expected.serialize())
        self.assertEqual(source, expected.content)

    def test_feature_type(self):
        source = "feat"
        expected = strings.FeatureString(source)
        self.assertEqual(expected, string_types.feature_type("feat"))
        self.assertEqual(expected, string_types.feature_type.parse("feat"))
        self.assertEqual(source, expected.serialize())
        self.assertEqual(source, expected.content)


if __name__ == '__main__':
    unittest.main()
