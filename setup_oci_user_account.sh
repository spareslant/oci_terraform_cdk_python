#! /bin/bash
# Make sure you have setup your tenancy API in ~/.oci/config file first
# This script will create 
# a user => cdk-user
# a group => cdk-group
# a compartment => CDK
# gives permissions for cdk-user to perform any actions/manage resources in CDK compartment
# setup ~/.oci/config file for cdk-user

set -euo pipefail

OCI_COMPARTMENT="CDK"
OCI_USER="cdk-user"
OCI_GROUP="cdk-group"

function get_oci_config_value() {
    local section="$1"
    local field="$2"
    local value=$(python - $section $field << EOI
import configparser
import os, sys
c = configparser.ConfigParser()
c.read(os.environ['HOME'] + '/.oci/config')
print(c[sys.argv[1]][sys.argv[2]])
EOI
)
    echo $value
}

function write_oci_config_file() {
    local section="$1"
    local user_file="$2"
    python - "$section" "$user_file" << EOI
import configparser
import os, sys, json

section = sys.argv[1]
file = sys.argv[2]
with open(file) as f:
    user_data = json.load(f)

oci_user_config_file = os.environ['HOME'] + '/.oci/config'
c = configparser.ConfigParser()
c.read(oci_user_config_file)

c[section] = user_data
with open(oci_user_config_file, 'w') as configFile:
    c.write(configFile)
EOI
}

tenancyID=$(get_oci_config_value "DEFAULT" "tenancy")
rootCompartmentID=$tenancyID
tenancyRegion=$(get_oci_config_value "DEFAULT" "region")

echo "INFO: Create $OCI_COMPARTMENT compartment ...."
oci iam compartment create \
    --name $OCI_COMPARTMENT \
    --compartment-id $rootCompartmentID \
    --description "$OCI_COMPARTMENT Compartment" \
    || :

echo "INFO: Create $OCI_USER user ...."
oci iam user create \
    --name $OCI_USER \
    --compartment-id $rootCompartmentID \
    --description "$OCI_USER user" \
    || :

echo "INFO: Create $OCI_GROUP group ...."
oci iam group create \
    --name $OCI_GROUP \
    --compartment-id $rootCompartmentID \
    --description "$OCI_GROUP group" \
    || :

echo "INFO: Add $OCI_USER to $OCI_GROUP ...."
cdk_user_ocid=$(oci iam user list --name $OCI_USER | jq -r '.data[0].id')
cdk_group_ocid=$(oci iam group list --name $OCI_GROUP | jq -r '.data[0].id')
oci iam group add-user \
    --user-id $cdk_user_ocid \
    --group-id $cdk_group_ocid \
    || :

echo "INFO: sleeping for 40 secs before creating policy...."
sleep 40

# Allow $OCI_GROUP to do anything in compartment $OCI_COMPARTMENT
echo "INFO: create policy for $OCI_GROUP to manage resources in $OCI_COMPARTMENT compartment ...."
compartmentID=$(oci iam compartment list  \
    --compartment-id $rootCompartmentID \
    --lifecycle-state ACTIVE \
    | jq -r --arg OCI_COMPARTMENT "$OCI_COMPARTMENT" '.data[] | select(.name == $OCI_COMPARTMENT) | .id')

statements="Allow group $OCI_GROUP to manage all-resources in compartment $OCI_COMPARTMENT"

cat <<POLICY > /tmp/statements.json
[ "$statements" ]
POLICY

oci iam policy create \
    --name "${OCI_COMPARTMENT}_Policy" \
    --compartment-id $compartmentID \
    --description "Policies for $OCI_COMPARTMENT" \
    --statements file:///tmp/statements.json \
    || :

echo "INFO: Generate API keys for $OCI_USER ...."
openssl genrsa -out ~/.oci/${OCI_USER}_private_api_key.pem 2048
openssl rsa -pubout -in ~/.oci/${OCI_USER}_private_api_key.pem -out ~/.oci/${OCI_USER}_public_api_key.pem
chmod go-rwx ~/.oci/${OCI_USER}_private_api_key.pem

echo "INFO: Upload public key for $OCI_USER ...."
oci iam user api-key upload --user-id $cdk_user_ocid --key-file ~/.oci/${OCI_USER}_public_api_key.pem

# preapre $OCI_USER profile in ~/.oci/config file
#cdk_user_fingerprint=$(oci iam user api-key list --user-id $cdk_user_ocid | jq -r '.data[0].fingerprint')
cdk_user_fingerprint=$(openssl rsa -pubout -outform DER -in ~/.oci/${OCI_USER}_private_api_key.pem 2> /dev/null | openssl md5 -c)

cat <<CONFIG > /tmp/oci_user_config.json
{
    "user": "$cdk_user_ocid",
    "fingerprint": "$cdk_user_fingerprint",
    "tenancy": "$tenancyID",
    "region": "$tenancyRegion",
    "key_file": "~/.oci/${OCI_USER}_private_api_key.pem"
}
CONFIG

echo "INFO: update ~/.oci/config file ...."
write_oci_config_file "$OCI_USER" "/tmp/oci_user_config.json"

echo "INFO: sleeping for 40 secs. Waiting for the user $OCI_USER to become active...."
sleep 40

echo "INFO: verify $OCI_USER access ...."
oci iam user get --user-id $cdk_user_ocid --profile $OCI_USER

echo "========== SUCCESS =========="
