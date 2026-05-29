"""Teams webhook schemas."""

from __future__ import annotations

import uuid
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, field_validator

from app.core.types import HttpsUrl


class WebhookType(StrEnum):
    PLATFORM = "platform"
    CUSTOMER = "customer"


class WebhookLevel(StrEnum):
    ALL = "all"


class TeamsWebhookRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    webhook_type: WebhookType
    level: WebhookLevel
    url: HttpsUrl
    webhook_id: uuid.UUID


_WEBHOOK_NAMESPACE_UUID = uuid.UUID("a08decbe-3681-494a-aa71-27f1a109cc16")


class WebhookChannelWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    all: list[HttpsUrl] | None = None

    @field_validator("all", mode="after")
    @classmethod
    def validate_no_duplicates(cls, value: list[HttpsUrl] | None) -> list[HttpsUrl] | None:
        if value is None:
            return value
        seen: set[str] = set()
        for url in value:
            if url in seen:
                raise ValueError(f"Duplicate URL at level '{WebhookLevel.ALL.value}': {url}")
            seen.add(url)
        return value


class TeamsWebhookWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    customer: WebhookChannelWrite | None = None
    platform: WebhookChannelWrite | None = None

    def to_items(self, cluster_name: str) -> list[TeamsWebhookRead]:
        items: list[TeamsWebhookRead] = []

        def generate_webhook_id(webhook_type: WebhookType, level: str, url: str) -> uuid.UUID:
            return uuid.uuid5(_WEBHOOK_NAMESPACE_UUID, f"{cluster_name}_{webhook_type}_{level}_{url}")

        for webhook_type, channels in (
            (WebhookType.CUSTOMER, self.customer),
            (WebhookType.PLATFORM, self.platform),
        ):
            if channels is None:
                continue
            for url in channels.all or []:
                items.append(
                    TeamsWebhookRead(
                        webhook_type=webhook_type,
                        level=WebhookLevel.ALL,
                        url=url,
                        webhook_id=generate_webhook_id(webhook_type, WebhookLevel.ALL.value, str(url)),
                    )
                )
        return items
