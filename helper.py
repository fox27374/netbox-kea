from pyisckea import Kea
from httpx import BasicAuth
from pynetbox import api
from pyisckea.models.dhcp4.subnet import Subnet4
from requests import packages
from os import environ
from dotenv import dotenv_values

config = {
    **dotenv_values(".env"),
    **environ
}

packages.urllib3.disable_warnings()

class DHCP:
    def __init__(self):
        self.host = config['KEA_HOST']
        self.port = config['KEA_PORT']
        self.username = config['KEA_USERNAME']
        self.password = config['KEA_PASSWORD']
        self.subnet_ids = []
        self.reservations = []

        self._connect()
        self._get_subnet4_ids()
        self._get_reservations()
        self._del_reservations()
        self._del_subnet4_ids()

    def _connect(self):
        """Connect to the KEA DHCP server and retun the handler"""
        auth = BasicAuth(self.username, self.password)
        try:
            self.server = Kea(f"{self.host}:{self.port}", auth=auth)
        except Exception as e:
            print(f"Unable to connect to Kea: {e}")

    def _get_subnet4_ids(self):
        """Get subnet IDs"""
        try:
            subnets = self.server.dhcp4.subnet4_list()
        except Exception as e:
            print(f"Unable to get subnets from Kea: {e}")

        for subnet in subnets:
            self.subnet_ids.append(subnet.id)

    def _get_reservations(self):
        """Get reservations"""
        for id in self.subnet_ids:
            try:
                reservations = self.server.dhcp4.reservation_get_all(subnet_id=id)
            except Exception as e:
                print(f"Unable to get reservatrions from Kea: {e}")

            for reservation in reservations:
                self.reservations.append({"subnet_id": id, "ip_address": reservation.ip_address})

    def _del_reservations(self):
        """Delete reservations"""
        for reservation in self.reservations:
            try:
                self.server.dhcp4.reservation_del_by_ip(subnet_id=reservation['subnet_id'], ip_address=reservation['ip_address'])
            except Exception as e:
                print(f"Unable to delete reservation from Kea: {e}")

    def _del_subnet4_ids(self):
        """Delete subnets"""
        for id in self.subnet_ids:
            try:
                self.server.dhcp4.subnet4_del(subnet_id=id)
            except Exception as e:
                print(f"Unable to delete subnet from Kea: {e}")

    def add_subnet4(self, subnets):
        """Add subnet and all reservations"""
        for key, content in subnets.items():
            subnet_to_add = Subnet4(
                id=content.get('vid') or key,
                subnet=content.get('subnet'),
                pools=[{"pool": content.get('pool')}],
                option_data=[
                    {"name": "routers", "data": content.get('routers')},
                    {"name": "domain-name-servers", "data": content.get('nameservers')}
                ]
            )

            try:
                add_subnet = self.server.dhcp4.subnet4_add(subnets=[subnet_to_add])
                if add_subnet.result > 0:
                    print({"code": add_subnet.result, "text": add_subnet.text})
            except Exception as e:
                print(f"Unable to add subnet from Kea: {e}")
            

    def add_reservation(self, subnets):
        for key, content in subnets.items():
            for reservation in content.get('reservations'):
                try:
                    add_reservation = self.server.dhcp4.reservation_add(
                        ip_address=reservation.get('ip_address').split('/')[0],
                        subnet_id=content.get('vid') or key,
                        hw_address=reservation.get('client_id')
                        )
                    if add_reservation.result > 0:
                        print({"code": add_reservation.result, "text": add_reservation.text})
                except Exception as e:
                    print(f"Unable to add subnet from Kea: {e}")


class Netbox:
    def __init__(self):
        self.host = config['NB_HOST']
        self.port = config['NB_PORT']
        self.username = config['NB_USERNAME']
        self.token = config['NB_TOKEN']
        self.prefixes = {}

        self.connect()

    def connect(self):
        try:
            self.nb = api(f"{self.host}:{self.port}", token=self.token)
            self.nb.http_session.verify = False
        except Exception as e:
            print(f"Unable to connect to Netbox: {e}")

    def get_dhcp_prefixes(self):
        try:
            prefixes = self.nb.ipam.prefixes.filter(cf_dhcp_server='kea')
        except Exception as e:
            print(f"Unable to get prefixes from Netbox: {e}")

        for prefix in prefixes:
            self.prefixes[prefix['id']] = self._format_prefix(prefix)

        return self.prefixes
    
    def get_dhcp_ip_addresses(self):
        try:
            ip_addresses = self.nb.ipam.ip_addresses.filter(cf_dhcp_reservation=True)
        except Exception as e:
            print(f"Unable to get ip addresses from Netbox: {e}")

        for ip_address in ip_addresses:
            reservation = {}
            reservation['ip_address'] = ip_address['address']
            reservation['client_id'] = ip_address['custom_fields']['dhcp_client_identifier']
            id = self._get_ip_prefix(ip_address['address'])
            self.prefixes[id]['reservations'].append(reservation)

        return self.prefixes

    def _get_ip_prefix(self, ip_address):
        id = 0
        try:
            ip_prefixes = self.nb.ipam.prefixes.filter(contains=ip_address, cf_dhcp_server='kea')
        except Exception as e:
            print(f"Unable to get prefix id from Netbox: {e}")

        for ip_prefix in ip_prefixes:
            id = ip_prefix['id']

        return id

    def _format_prefix(self, nb_prefix):
        prefix = {}
        prefix['vid'] = nb_prefix['vlan']['vid'] or None
        prefix['subnet'] = nb_prefix['prefix']
        prefix['pool'] = nb_prefix['custom_fields']['dhcp_pool']
        prefix['routers'] = nb_prefix['custom_fields']['dhcp_option_routers']
        prefix['nameservers'] = nb_prefix['custom_fields']['dhcp_option_nameservers']
        prefix['reservations'] = []

        return prefix