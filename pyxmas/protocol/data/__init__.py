__all__ = ["Query", "Recommendation", "Explanation", "Motivation", "Feature", "Types", "Serializable"]


class Serializable:
    @classmethod
    def parse(cls, input: str):
        ...

    def serialize(self) -> str:
        str(self)

    def __eq__(self, o: object) -> bool:
        ...

    def __hash__(self) -> int:
        ...


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


class Types:
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
