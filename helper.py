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

        self._connect()
        self._get_subnet4_ids()
        self._del_subnet4_ids()

    def _connect(self):
        """Connect to the KEA DHCP server and retun the handler"""
        auth = BasicAuth(self.username, self.password)
        self.server = Kea(f"{self.host}:{self.port}", auth=auth)

    def _get_subnet4_ids(self):
        """Get subnet IDs"""
        subnets = self.server.dhcp4.subnet4_list()
        for subnet in subnets:
            self.subnet_ids.append(subnet.id)

    def _del_subnet4_ids(self):
        """Delete subnets"""
        for id in self.subnet_ids:
            del_subnet = self.server.dhcp4.subnet4_del(subnet_id=id)

        #return {"code": del_subnet.result, "text": del_subnet.text}

    def add_subnet4(self, subnets):
        """Add a subnet"""
        for subnet in subnets:
            subnet_to_add = Subnet4(
                id=subnet['id'],
                subnet=subnet['subnet'],
                pools=[{"pool": subnet['pool']}],
                option_data=[
                    {"name": "routers", "data": subnet['routers']},
                    {"name": "domain-name-servers", "data": subnet['nameservers']}
                ]
            )
            
            add_subnet = self.server.dhcp4.subnet4_add(subnets=[subnet_to_add])
            if add_subnet.result > 0:
                print({"code": add_subnet.result, "text": add_subnet.text})


class Netbox:
    def __init__(self):
        self.host = config['NB_HOST']
        self.port = config['NB_PORT']
        self.username = config['NB_USERNAME']
        self.token = config['NB_TOKEN']
        self.subnets = []

        self.connect()

    def connect(self):
        self.nb = api(f"{self.host}:{self.port}", token=self.token)
        self.nb.http_session.verify = False

    def get_dhcp4_subnets(self):
        subnets = self.nb.ipam.prefixes.all()
        for subnet in subnets:
            if subnet['custom_fields']['dhcp_server'] == "kea":
                self.subnets.append(self._format_subnet(subnet))
        return self.subnets

    def _format_subnet(self, nb_subnet):
        subnet = {}
        # Use VLAN id or Netbox subnet ID
        if nb_subnet['vlan']['vid']:
            subnet['id'] = nb_subnet['vlan']['vid']
        else:
            subnet['id'] = nb_subnet['id']

        subnet['subnet'] = nb_subnet['prefix']
        subnet['pool'] = nb_subnet['custom_fields']['dhcp_pool']
        subnet['routers'] = nb_subnet['custom_fields']['dhcp_option_routers']
        subnet['nameservers'] = nb_subnet['custom_fields']['dhcp_option_nameservers']

        return subnet