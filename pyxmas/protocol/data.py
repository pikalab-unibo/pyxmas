class Serializable:
    @classmethod
    def parse(cls, input: str):
        ...

    def serialize(self) -> str:
        str(self)


class Query(Serializable):
    pass


class Recommendation(Serializable):
    pass


class Explanation(Serializable):
    pass


class Motivation(Serializable):
    pass


class Feature(Serializable):
    pass


class Implementations:
    @property
    def query_type(self):
        return Query

    @property
    def recommendation_type(self):
        return Recommendation

    @property
    def explanation_type(self):
        return Explanation

    @property
    def motivation_type(self):
        return Motivation

    @property
    def feature_type(self):
        return Feature

