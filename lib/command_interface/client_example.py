"""
This is a simple client example that will connect to xmlrpc server and call the function
"""




import xmlrpc.client

# ground station ip
server = xmlrpc.client.ServerProxy('http://172.20.70.133:8000')

# print('Reponse:', server.add(1, 2))
# print('Pinging server:', server.ping())



# lets try and send a command
cmd_name = "REQUEST_TM_HAL"
cmd_args = {}

#cmd_name = "SUM"
#cmd_args = {"op1": 5, "op2": 10}


# this will send the command to the ground station and the ground station will add it to the command queue and transmit it to the satellite
server.add_command(cmd_name, cmd_args)
