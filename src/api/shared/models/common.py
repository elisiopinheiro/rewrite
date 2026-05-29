from typing import Annotated

from pydantic import AfterValidator, AnyUrl, PlainSerializer, UrlConstraints, WithJsonSchema

HttpsUrl = Annotated[
    AnyUrl,
    UrlConstraints(allowed_schemes=["https"], max_length=2083),
    AfterValidator(str),
    PlainSerializer(lambda v: v, return_type=str),
    WithJsonSchema({"type": "string", "format": "uri", "maxLength": 2083, "minLength": 1}),
]
