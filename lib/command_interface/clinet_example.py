"""
This is a simple client example that will connect to xmlrpc server and call the function
"""



address = ("0.0.0.0", 8000)


import xmlrpc.client

server = xmlrpc.client.ServerProxy('http://172.20.70.133:8000')

print('Reponse:', server.add(1, 2))

print('Pinging server:', server.ping())



# lets try and send a command
cmd_name = "FORCE_REBOOT"
cmd_args = {}

server.add_command({"cmd_name": cmd_name, "cmd_args": cmd_args})