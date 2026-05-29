import uuid
from typing import TYPE_CHECKING, Dict, List, Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    ValidationInfo,
    field_validator,
)
from sqlalchemy import String as SAString
from sqlalchemy.dialects.postgresql import UUID as SQLUUID
from sqlmodel import (
    Column,
    Field,
    ForeignKey,
    Integer,
    Relationship,
    SQLModel,
)

from api.shared.enums import WebhookLevel, WebhookType
from api.shared.models.common import HttpsUrl

if TYPE_CHECKING:
    from api.shared.models.clusters import Cluster


_WEBHOOK_NAMESPACE_UUID = uuid.UUID("a08decbe-3681-494a-aa71-27f1a109cc16")


class TeamsWebhookBase(SQLModel):
    type: WebhookType = Field(sa_type=SAString, nullable=False)
    level: WebhookLevel = Field(sa_type=SAString, nullable=False)
    url: HttpsUrl = Field(sa_type=SAString, nullable=False)
    webhook_id: uuid.UUID = Field(sa_column=Column(SQLUUID(as_uuid=True), unique=True, nullable=False))

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True, use_enum_values=True)


class TeamsWebhookRequest(BaseModel):
    customer: Optional[Dict[WebhookLevel, List[HttpsUrl]]] = None
    platform: Optional[Dict[WebhookLevel, List[HttpsUrl]]] = None

    @field_validator("customer", "platform", mode="after")
    @classmethod
    def validate_no_duplicates(cls, value, info: ValidationInfo):
        if value is None:
            return value
        for level, urls in value.items():
            seen = set()
            for url in urls:
                if url in seen:
                    raise ValueError(f"Duplicate URL in '{info.field_name}' at level '{level.name}': {url}")
                seen.add(url)
        return value

    def convert_webhooks(self, cluster_name: str) -> List[TeamsWebhookBase]:
        """
        Converts the webhook request to a list of TeamsWebhookBase.

        Args:
            cluster_name: The name of the cluster these webhooks belong to

        Returns:
            List of TeamsWebhookBase
        """
        webhooks = []

        def generate_webhook_id(webhook_type: WebhookType, level: str, url: str) -> uuid.UUID:
            id_str = f"{cluster_name}_{webhook_type}_{level}_{url}"
            return uuid.uuid5(_WEBHOOK_NAMESPACE_UUID, id_str)

        if self.customer:
            for level, urls in self.customer.items():
                for url in urls:
                    webhook = TeamsWebhookBase(
                        type=WebhookType.customer,
                        level=level,
                        url=url,
                        webhook_id=generate_webhook_id(WebhookType.customer, level, str(url)),
                    )
                    webhooks.append(webhook)

        if self.platform:
            for level, urls in self.platform.items():
                for url in urls:
                    webhook = TeamsWebhookBase(
                        type=WebhookType.platform,
                        level=level,
                        url=url,
                        webhook_id=generate_webhook_id(WebhookType.platform, level, str(url)),
                    )
                    webhooks.append(webhook)

        return webhooks

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "customer": {"all": ["https://example.com/webhook1"]},
                "platform": {"all": ["https://example.com/webhook2"]},
            }
        }
    )


class TeamsWebhook(TeamsWebhookBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True, nullable=False)

    cluster_id: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer, ForeignKey("cluster.id", ondelete="CASCADE"), nullable=False, index=True),
    )

    cluster: "Cluster" = Relationship(
        back_populates="teams_webhooks",
        sa_relationship_kwargs={
            "lazy": "joined",
        },
    )
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)
