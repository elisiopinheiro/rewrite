#!/bin/bash

set -e

# Create a json including the cluster info stored in Bitbucket
# Some values still need be manually changed("internal","environment","release") afterwards

cluster_list=$(curl -u $QX_NUMBER:$BITBUCKET_PERSONAL_TOKEN https://atc.bmwgroup.net/bitbucket/rest/api/1.0/projects/EIGHTEEN/repos\?limit\=1000  | jq -r '.values[].slug')

TMP_JSON=/tmp/clusters.json
echo [] > $TMP_JSON

cat /tmp/clusters.json
for cluster in ${cluster_list}
do
    echo "$cluster"
    cd /tmp/ || exit
    git clone "ssh://git@git.bmwgroup.net:7999/eighteen/$cluster.git" --depth 1 || true
    cd /tmp/$cluster || exit
    yq -o=json eval values.yaml > values.json
    jq -r '{ name: .common.cluster_name, subscription: (if .common.azure_subscription_id ? then .common.azure_subscription_id else .common.aws_account_id end), provider: .common.cluster_type, release: "main", environment: "development", "internal": true, repository: .applications.repository, node_min_count: .common.node_min_count, node_max_count: .common.node_max_count, provider_region: (if .common.azure_location ? then .common.azure_location else .common.aws_region end), tshirt_size: .common.tshirt_size, infra_revision: .common.infra_revision, kubernetes_version: (if .common.azure_k8s_version ? then .common.azure_k8s_version else .common.aws_k8s_version end) } '  values.json > parsed.json
    out=$(jq --slurpfile t parsed.json '. += $t' /tmp/clusters.json)
    echo $out > $TMP_JSON
    jq -r '(map(keys) | add | unique) as $cols | map(. as $row | $cols | map($row[.])) as $rows | $cols, $rows[] | @csv'  /tmp/clusters.json > /tmp/clusters.csv
done

cat $TMP_JSON | jq .
