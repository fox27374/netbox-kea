# netbox-kea
Confiure KEA DHCP pools and reservations with Netbox

## Getting started
### Authentication
The Kea and Netbox credentials can be passes in with these environmental variables:
* NB_HOST
* NB_PORT
* NB_USERNAME
* NB_TOKEN
* KEA_HOST
* KEA_PORT
* KEA_USERNAME
* KEA_PASSWORD
The HOST variable must be a valid URL e.g. http://172.24.60.50 or https://netbox.example.com
Variable can directly be passes in or read from a **.env** file.
