#!/bin/sh
set -e

echo ""
echo "------------------------------------------------------------------"
echo "---------- GENERATE CLUSTERS-4WM-API DATABASE DUMP FILE ----------"
echo "------------------------------------------------------------------"

current_aws_credentials_lifetime=$(grep "valid_until" $HOME/.aws/credentials | grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}')
now=$(date --utc +"%F %H:%M")

if [[ "$current_aws_credentials_lifetime" < "$now" ]];
then
 echo "Your AWS credentials expired, waiting login..."
 bmwaws login
fi

connection_string='clusters-4wm-int-replica.calxwmhjhlhu.eu-central-1.rds.amazonaws.com'

export VAULT_ADDR="https://vault.4wm-secrets.eu-central-1.aws.cloud.bmw"
echo ""
echo ""
echo "Please input your Q account info below!"
echo ""
read -p "QX: " Q_ACCOUNT
vault login -method=ldap username="$Q_ACCOUNT"
db_password=$(vault kv get -field=password "kv/applications/clusters-4wm-int/database")
username=$(vault kv get -field=username "kv/applications/clusters-4wm-int/database")
dbname='clusters4wm'
port=5432

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
filename="${SCRIPT_DIR}/${dbname}_$(date +%Y%m%d_%H%M%S).sql"

# Create the directory if it doesn't exist
mkdir -p "$(dirname "$filename")"

# Flags:
 # -T <pattern> : Excludes the tables identified by the specified pattern from the dump.
pg_dump postgresql://"$username":"$db_password"@$connection_string:$port/$dbname -f "$filename" -T=*operation*

echo ""
echo ""
echo "Dump file generated in $filename"
echo ""
echo "Bye bye :)"

# # Insert dumped data into local database
# PGPASSWORD="password" psql -h localhost -U cluster_app -d clusters <<EOF
# \i ./'$filename';
# EOF
