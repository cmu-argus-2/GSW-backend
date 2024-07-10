# Argus Groundstation backend code

This code receives data from the satellite and uploads that data to an influxDB instance running on a different raspberry pi or the cloud.

## Setup
First please install all required packages shown in `requirements.txt`. This is also designed to run on a raspberry pi with the raspberry pi builtin packages. 

You will then need to configure your environment. Within `lib`, you will need to create a `passwords.py` file which contains information that the server will use to connect and store information in the database. This file should contain `INFLUXDB_TOKEN`, which is the API token to communicate with your InfluxDB instance. `INFLUXDB_IP`, the hostname and port which you can use to connect to your database. `INFLUXDB_ORGANIZATION`, which is the organization you created during your InfluxDB instance setup. 

## Running
Currently the functionality is a receive loop that gets data from the satellite and logs it in the InfluxDB instance. This receive loop can be run with 

`python3 main.py`
