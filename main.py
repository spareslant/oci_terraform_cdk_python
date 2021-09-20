#!/usr/bin/env python
from constructs import Construct
from cdktf import App, TerraformOutput, TerraformStack
from imports.oci import (CoreDhcpOptionsOptions, CoreRouteTableRouteRules, CoreVcn, OciProvider,
    CoreInstance,
    CoreSubnet,
    CoreDhcpOptions,
    CoreDhcpOptionsOptions,
    CoreInstanceCreateVnicDetails,
    CoreInternetGateway,
    CoreRouteTable,
    CoreRouteTableAttachment,
    )
from account import get_compartment_id, get_availability_domain, get_key_pair

class MyStack(TerraformStack):
    def __init__(self, scope: Construct, ns: str):
        super().__init__(scope, ns)
        desired_compartment_id: str = get_compartment_id()
        desired_availability_domain = get_availability_domain()
        desired_image_id = "ocid1.image.oc1.uk-london-1.aaaaaaaa7p27563e2wyhmn533gp7g3wbohrhjacsy3r5rpujyr6n6atqppuq"
        public_key = get_key_pair()

        # define resources here
        OciProvider(self, "oci",
                config_file_profile="MYPROFILE")

        vcn = CoreVcn(self, "OCI_VCN",
                cidr_block="10.0.0.0/16",
                display_name="OCI_VCN",
                compartment_id=desired_compartment_id)

        dhcp = CoreDhcpOptions(self, "dhcp",
                compartment_id=desired_compartment_id,
                vcn_id=vcn.id,
                options=[
                    CoreDhcpOptionsOptions(
                    type="DomainNameServer",
                    server_type="VcnLocalPlusInternet")
                ]
            )
        
        public_subnet = CoreSubnet(self, "public_subnet",
                cidr_block="10.0.0.0/24",
                vcn_id=vcn.id,
                compartment_id=desired_compartment_id,
                display_name="public_subnet",
                dhcp_options_id=dhcp.id)

        igateway = CoreInternetGateway(self, "InternetGateway",
                compartment_id=desired_compartment_id,
                vcn_id=vcn.id)

        route_table = CoreRouteTable(self, "route_table",
                compartment_id=desired_compartment_id,
                vcn_id=vcn.id,
                route_rules=[
                    CoreRouteTableRouteRules(
                        network_entity_id=igateway.id,
                        destination="0.0.0.0/0"
                        ) 
                    ])
        CoreRouteTableAttachment(self, "RouteAttachment",
                subnet_id=public_subnet.id,
                route_table_id=route_table.id)

        
        vm = CoreInstance(self, "instance",
                compartment_id=desired_compartment_id,
                shape="VM.Standard.E2.1.Micro",
                availability_domain=desired_availability_domain,
                image=desired_image_id,
                create_vnic_details=[
                    CoreInstanceCreateVnicDetails(
                        subnet_id=public_subnet.id)
                    ],
                metadata={
                    "ssh_authorized_keys": public_key
                    })

        TerraformOutput(self, "vcn", 
                value=vcn.cidr_block)
        TerraformOutput(self, "publicSubnet", 
                value=public_subnet.cidr_block )
        TerraformOutput(self, "VM_public_ip", 
                value=vm.public_ip)
        
app = App()
MyStack(app, "oci_terraform_cdk_python")

app.synth()
