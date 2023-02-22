import pyxmas.protocol.data as data


__all__ = ["Types", "QueryString", "RecommendationString", "ExplanationString", "MotivationString", "FeatureString"]


class BaseString(data.Serializable):
    def __init__(self, content: str):
        self._content = content

    @property
    def content(self) -> str:
        return self._content

    def __str__(self):
        return self._content

    def __eq__(self, other):
        return self._content == other.content

    def __hash__(self):
        return hash(self._content)

    def serialize(self) -> str:
        return self._content

    @classmethod
    def parse(cls, input: str):
        return cls(input)


class QueryString(data.Query, BaseString):
    pass


class RecommendationString(data.Recommendation, BaseString):
    pass


class ExplanationString(data.Explanation, BaseString):
    pass


class MotivationString(data.Motivation, BaseString):
    pass


class FeatureString(data.Feature, BaseString):
    pass


class Types:
    @property
    def query_type(self):
        return QueryString

    @property
    def recommendation_type(self):
        return RecommendationString

    @property
    def explanation_type(self):
        return ExplanationString

    @property
    def motivation_type(self):
        return MotivationString

    @property
    def feature_type(self):
        return FeatureString
