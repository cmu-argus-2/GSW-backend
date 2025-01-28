# Argus Groundstation Software

This is the software module for the Argus groundstation. It interfaces with a LoRa radio over SPI and communicates with Argus during ground passes. For receiving commands to uplink and to store downlinked data, it shall push this data to the groundstation's database ([Link to repo](url)). 

## Setup
First please install all required packages shown in `requirements.txt`. This is also designed to run on a Raspberry Pi with the Pi's builtin packages. 

## Running
Currently the functionality is a receive loop that gets data from the satellite and logs this data to the terminal. This receive loop can be run with 

`python3 main.py`
