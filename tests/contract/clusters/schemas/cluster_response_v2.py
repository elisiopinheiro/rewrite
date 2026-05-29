from typing import List

from contract.clusters.schemas.cluster_response_v1 import ClusterResponseContractV1
from pydantic import BaseModel


class ClusterResponseContractV2(BaseModel):
    count: int
    clusters: List[ClusterResponseContractV1]
