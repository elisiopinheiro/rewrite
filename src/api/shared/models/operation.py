from datetime import datetime
from typing import Optional

from pydantic import model_validator
from sqlmodel import Column, Field, ForeignKey, Integer, SQLModel


class OperationBase(SQLModel):
    type: str
    timestamp: Optional[datetime] = None
    status: str
    cluster_repository: Optional[str] = None
    cicd_url: str


class Operation(OperationBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True, nullable=False)
    cluster_id: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer, ForeignKey("cluster.id", ondelete="SET NULL"), index=True),
    )


class OperationCreate(OperationBase):
    #############################################################################################
    #   This code block needs to be removed after all clusters are migrated to the new schema   #
    #############################################################################################
    jenkins_url: Optional[str] = None
    cicd_url: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def validate_cicd_url(cls, values):
        cicd_url = values.get("cicd_url") or values.get("jenkins_url")
        if not cicd_url:
            raise ValueError("cicd_url or jenkins_url is required")
        values["cicd_url"] = cicd_url
        return values


# The code (pass) needs to be uncommented after the cleanup
# pass
