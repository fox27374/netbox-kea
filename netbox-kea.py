from helper import DHCP, Netbox

def main():
    dhcp = DHCP()
    nb = Netbox()

    subnets_to_add = nb.get_dhcp4_subnets()
    dhcp.add_subnet4(subnets_to_add)

if __name__ == "__main__":
    main()