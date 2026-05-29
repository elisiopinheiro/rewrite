#!/bin/bash

set -e

# Fills the API/DB with cluster information from a json file in array format

# https://miller.readthedocs.io/en/latest/
# Converts the validated clusters csv file into json
# mlr --icsv --ojson --jlistwrap cat clusters.csv > clusters.json

API_URL="https://clusters-4wm.apps.4wm-services.eu-central-1.aws.cloud.bmw"
API_CREDENTIALS="admin:$API_PWD"

jq -c '.[]' clusters.json | while read -r i; do
    curl --request POST "$API_URL/v1/clusters" \
	--header 'Content-Type: application/json' \
	--basic -u "$API_CREDENTIALS" \
	--data-raw "$i" \
	-o -
	echo ""
done
