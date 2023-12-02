import json

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

    def __init__(self,JSON):
        self.user_id = JSON["uuid"]
        self.JSON = JSON

    def __str__(self):
        return self.user_id

    def __eq__(self, other):
        return other is not None and self.user_id == other.user_id

    def __hash__(self):
        return hash(self.user_id)

    def serialize(self) -> str:
        return json.dumps(self.JSON)

    @classmethod
    def parse(cls, input: str):
        JSON = json.loads(input)
        return cls(JSON)

class Recommendation(Serializable):
        
    def __init__(self, response: dict):
        self.response = response
        self.recipe_id = response["recipe"]["recipe_id"]
        self.recipe = response["recipe"]["recipe"]["RecipeName"]
        self.explanation = response["recipe"]["explanations"][0]["content"]

    def __str__(self):
        return self.recipe

    def __eq__(self, other):
        return other is not None and self.recipe_id == other.recipe_id

    def __hash__(self):
        return hash(self.recipe_id)

    def serialize(self) -> str:
        return json.dumps(self.response)
    
    @classmethod
    def parse(cls, input: str):
        response = json.loads(input)
        return cls(response)

class Explanation(Serializable):
        
    def __init__(self, reccommandation : Recommendation):
        self.recommendation = reccommandation
        self.explanation = reccommandation.explanation

    def __str__(self):
        return self.explanation

    def __eq__(self, other):
        return other is not None and self.recommendation.recipe_id == other.recommendation.recipe_id and self.explanation == other.explanation

    def __hash__(self):
        return hash(self.recommendation.recipe_id)

    def serialize(self) -> str:
        return json.dumps(self.recommendation.response)
    
    @classmethod
    def parse(cls, input: str):
        response = json.loads(input)
        response = Recommendation(response)
        return cls(response)


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
