from helper import DHCP, Netbox

def main():
    dhcp = DHCP()
    nb = Netbox()

    # Get all prefixes from Netbox where the Kea DHCP server
    # is configured.
    nb.get_dhcp_prefixes()

    # Get all IP addresses that have a DHCP reservation configured
    dhcp_subnets = nb.get_dhcp_ip_addresses()

    # Configure the Kea DHCP server with the subnets and reservations
    # configured in Netbox
    dhcp.add_subnet4(dhcp_subnets)
    dhcp.add_reservation(dhcp_subnets)

if __name__ == "__main__":
    main()