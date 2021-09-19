import oci

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



if  __name__ == '__main__':
    print(f"desired_compartment_id = {get_compartment_id()}")
    print(f"availability_domain = {get_availability_domain().name}")
