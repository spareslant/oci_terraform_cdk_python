import oci
from Crypto.PublicKey import RSA
import os


keys_dir = "keys"

config = oci.config.from_file("~/.oci/config", "MYPROFILE")
identity = oci.identity.IdentityClient(config)
user = identity.get_user(config["user"]).data
compartment_id = user.compartment_id

# compartments = identity.list_compartments(compartment_id, compartment_id_in_subtree=True, lifecycle_state="ACTIVE", access_level="ACCESSIBLE")

# print(compartments.data)
# print(compartments.data[0])

def get_availability_domain():
    list_availability_domains_response = oci.pagination.list_call_get_all_results(
        identity.list_availability_domains,
        compartment_id
    )
    availability_domain = list_availability_domains_response.data[0]

    return availability_domain.name

def get_compartment_id(comp_name="ocilabs") -> str:

    desired_compartment_id: str = ""

    for comp in oci.pagination.list_call_get_all_results_generator(
            identity.list_compartments,
            'record',
            compartment_id,
            compartment_id_in_subtree=True,
            lifecycle_state="ACTIVE", access_level="ACCESSIBLE"):
        if comp.name == comp_name:
            desired_compartment_id = comp.id
    return desired_compartment_id

def generate_key_pair():
    os.mkdir("keys")
    key = RSA.generate(2048)
    private_key = key.export_key("PEM")
    file_out = open(f"{keys_dir}/private.pem", "wb")
    file_out.write(private_key)
    file_out.close()
    os.chmod(f"{keys_dir}/private.pem", 0o600)

    public_key = key.publickey().export_key("OpenSSH")
    file_out = open(f"{keys_dir}/public.pem", "wb")
    file_out.write(public_key)
    file_out.close()

    return public_key.decode("utf-8")


def get_key_pair(use_existing_keys=True):
    if use_existing_keys:
        if not os.path.isfile(f"{keys_dir}/private.pem"):
            return generate_key_pair()
        else:
            with open(f"{keys_dir}/public.pem", 'rb') as f:
                public_key = f.read()
            return public_key.decode("utf-8")
    else:
        return generate_key_pair()


if  __name__ == '__main__':
    print(f"desired_compartment_id = {get_compartment_id()}")
    print(f"availability_domain = {get_availability_domain()}")
    print(get_key_pair())
