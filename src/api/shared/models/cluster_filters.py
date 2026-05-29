from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field
from sqlalchemy.sql import operators
from sqlalchemy.sql.elements import BinaryExpression

from api.shared.enums import AzureSkuTier, ClusterStatus, Environment, Provider
from api.shared.models.clusters import Cluster


class Operator(str, Enum):
    EQUAL = "="
    NOT_EQUAL = "!="


class FilterMixin(BaseModel):
    """
    A mixin class that provides filtering functionality based
        on the values of the fields in the instance.

    Attributes:
    operator_map (dict): A dictionary mapping operator symbols to
        corresponding operator functions.
    """

    _OPERATOR_MAP_ = {
        "=": operators.eq,
        "!=": operators.ne,
    }

    def prepare_filters(self) -> list[BinaryExpression]:
        """
        Prepare and return a list of filters based on the values of the fields
            in the instance.
        It iterates the fields in the instance, and based on their metadata, it
            determines what operator to use (equal, not equal) and what fields
            to add to the filters.
        If the field has a label 'operator' it means that it this variable can have a
            filter different to equal (i.e. name != 4wm).
        If the variable is of type 'Operator' it shouldn't be added to the filters

        Based on:
        https://github.com/sqlalchemy/sqlalchemy/discussions/6406#discussioncomment-4387977
        https://github.com/juliotrigo/sqlalchemy-filters/blob/master/sqlalchemy_filters/filters.py#L55

        Returns:
            list: A list of filters to be applied to the cluster data.
        """
        filters: list[BinaryExpression] = []
        for field_name, field in self.__class__.model_fields.items():
            value = getattr(self, field_name, None)
            operator_field = (field.json_schema_extra or {}).get("operator", "__undefined__")
            operator_value = getattr(self, operator_field, Operator.EQUAL)

            if value is not None and not isinstance(value, Operator):
                filters.append(self._OPERATOR_MAP_[operator_value](getattr(Cluster, field_name), value))

        return filters


class ClusterFilters(FilterMixin, BaseModel):
    name: Optional[str] = None
    subscription: Optional[str] = None
    account_name: Optional[str] = None
    status: Optional[ClusterStatus] = None
    provider: Optional[Provider] = None
    release: Optional[str] = Field(None, json_schema_extra={"operator": "release_condition"})
    release_condition: Operator = Operator.EQUAL
    environment: Optional[Environment] = None
    internal: Optional[bool] = None
    multi_tenant: Optional[bool] = None
    node_min_count: Optional[int] = None
    node_min_count_gt: Optional[int] = None
    node_min_count_lt: Optional[int] = None
    node_max_count: Optional[int] = None
    provider_region: Optional[str] = None
    tshirt_size: Optional[str] = None
    infra_revision: Optional[str] = Field(None, json_schema_extra={"operator": "infra_revision_condition"})
    infra_revision_condition: Operator = Operator.EQUAL
    repository: Optional[str] = None
    kubernetes_version: Optional[str] = None
    owner_group: Optional[str] = None
    cmdb_app_id: Optional[str] = None
    cmdb_appd_id: Optional[str] = None
    azure_sku_tier: Optional[AzureSkuTier] = None
    gateway_api_enabled: Optional[bool] = None
    headlamp_enabled: Optional[bool] = None
