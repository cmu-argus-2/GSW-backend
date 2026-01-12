
import asyncio
from lib.argus_fsk import RFM9xFSK

from radio_config import config_dict


# lets start testing the new fsk class
rfm = RFM9xFSK(config_dict)


# for OOK on RFM69 or RFM9xFSK
# rfm.modulation_type = 1

# send startup message from my_node
# rfm.send(bytes("startup message from node {}".format(rfm.node), "UTF-8"))
rfm.listen()
# Wait to receive packets.
print("Waiting for packets...")
# initialize flag and timer


# pylint: disable=too-few-public-methods
class Packet:
    """Simple class to hold an  value. Use .value to to read or write."""

    def __init__(self):
        self.received = False
        
        
rssiInterval = 0.3
lastRssiTime = asyncio.get_event_loop().time()


# print the sync register 0x27
op_mode = rfm.read_u8(0x01)
sync_reg = rfm.read_u8(0x27)
rx_config = rfm.read_u8(0x0D)
print(f"Operation Mode Register (bits): {op_mode:08b}")
print(f"Sync Register (bits): {sync_reg:08b}")
print(f"RX Config Register (bits): {rx_config:08b}")

# setup interrupt callback function
async def wait_for_packets(packet_status):
    global lastRssiTime

    while True:
        if rfm.payload_ready():
            packet = await rfm.asyncio_receive(with_header=False, timeout=None)
            if packet is not None:
                packet_status.received = True
                # Received a packet!
                # Print out the raw bytes of the packet:
                print(f"Received (raw bytes): {packet}")
                print([hex(x) for x in packet])
                
        if asyncio.get_event_loop().time() - lastRssiTime > rssiInterval:
            lastRssiTime = asyncio.get_event_loop().time()
            print(f"RSSI: {rfm.last_rssi}")
            op_mode = rfm.read_u8(0x01)
            print(f"Operation Mode Register (bits): {op_mode:08b}")

        await asyncio.sleep(0.001)


async def main():
    packet_status = Packet()
    task1 = asyncio.create_task(wait_for_packets(packet_status))

    await asyncio.gather(task1)  # Don't forget "await"!


asyncio.run(main())
