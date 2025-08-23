import re

from types import GenericAlias

from jwskate import Jwk

ULID = r'^[A-Z0-9]{26}$'


class AnySchema:
    def __init__(self, *schemas):
        self.schemas = schemas

    def __call__(self, **kwargs):
        for schema in self.schemas:
            if set(kwargs) & set(schema.__annotations__) != set(kwargs):
                continue
            return schema(**kwargs)


class SchemaMeta(type):
    def __or__(cls, other_cls):
        return AnySchema(cls, other_cls)


class Schema(metaclass=SchemaMeta):
    def __init__(self, **kwargs):
        for name, value in kwargs.items():
            if name in self.__annotations__:
                vartype = self.__annotations__[name]

                if isinstance(vartype, GenericAlias):
                    varsubtype = vartype.__args__[0]
                    value = [varsubtype(**i) for i in value]

                elif type(value) != vartype:
                    value = vartype(value)

                setattr(self, name, value)

    def __str__(self):
        return '<{} {}>'.format(
            self.__class__.__name__,
            ' '.join((
                f'{k}={getattr(self, k)}'
                for k in dir(self)
                if k in self.__annotations__
            ))
        )


class AuthRequestSchema(Schema):
    client: str = 'browser'
    purpose: str = 'vaults-access'
    rev: int = 1


class AuthResponseSchema(Schema):
    code: str
    id: str
    publicKey: str

    def __init__(self, **kwargs):
        if not re.match(ULID, kwargs['id']):
            raise ValueError('id')
        super().__init__(**kwargs)

    def get_public_key_jwk(self) -> Jwk:
        """Get JSON Web Key."""
        return Jwk(self.publicKey)


class TermEntriesSearchQuerySchema(Schema):
    term: str
    type: str = 'term'


class UrlEntriesSearchQuerySchema(Schema):
    url: str
    type: str = 'url'


class EntrySchema(Schema):
    entryID: str
    sourceID: str


class EntriesSearchBodySchema(Schema):
    entries: list[EntrySchema]


class SaveNewEntryPayloadSchema(Schema):
    properties: dict
    type: str
