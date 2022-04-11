import pynetbox
from datetime import datetime
from flask import Flask, Response

class DhcpCiscoNetbox:
    def __init__(self, url, token):
        self.nb = pynetbox.api(url, token, ssl_verify=False)

    def prefix2split(self, prefix):
        ip = prefix.split('/')
        return ip

    def dhcpclientid(self, prefix):
        cf = prefix.custom_fields
        return cf.get('DHCP Client-id')

    def create_dhcp_header(self):
        time =  datetime.strftime(datetime.now(), '%b %d %Y %I:%M %p')
        template = f'''*time* {time}
*version* 2
!IP address Type Hardware address Lease expiration\n'''
        return template

    def create_dhcp_line(self, prefix):
        address = prefix.address
        ip, mask = self.prefix2split(address)
        client_id = self.dhcpclientid(prefix)
        if client_id and ip and mask:
            return f'{ip} /{mask} id {client_id} Infinite\n'
        return None

    def create_dhcp_footer(self):
        return '*end*'

    def file_generation(self, tag):
        try:
            complite = ''
            # Header file
            complite += self.create_dhcp_header()

            # Netbox Get information
            prefix_nb = self.nb.ipam.ip_addresses.filter(tag=tag)

            # Line file
            for prefix in prefix_nb:
                line = self.create_dhcp_line(prefix)
                if not line:
                    continue
                complite += line

            # Footer file
            complite += self.create_dhcp_footer()
            return complite
        except pynetbox.RequestError:
            return None

app = Flask(__name__)

@app.route('/dhcp/<tag>', methods=['GET'])
def cisco_dhcp(tag):
    netbox = DhcpCiscoNetbox('https://netbox.pmcorp.loc/', '1f528ccd50d81f8051b7a0ef28737ef0ede5c30c')
    response = netbox.file_generation(tag)
    if not response:
        return f'Netbox TAG: {tag} - Not Found',404
    return Response(response, mimetype='text/plain', headers={'Content-Disposition': f'attachment;filename={tag}'})

if __name__ == '__main__':
    #app.run()
    app.run(host='127.0.0.1', port=8889, debug=False)
