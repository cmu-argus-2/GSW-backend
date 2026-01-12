"""
RFM Radio Module for Raspberry Pi using spidev

Converted from Adafruit CircuitPython RFM library
Original Author(s): Jerry Needell
Adapted for Raspberry Pi with spidev
"""

import asyncio
import random
import time
import spidev
from typing import Callable, Optional

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_RFM.git"

# RadioHead specific compatibility constants.
_RH_BROADCAST_ADDRESS = 0xFF

# The acknowledgement bit in the FLAGS
_RH_FLAGS_ACK = 0x80
_RH_FLAGS_RETRY = 0x40

# Timing constants
_TICKS_PERIOD = 1 << 29
_TICKS_MAX = _TICKS_PERIOD - 1
_TICKS_HALFPERIOD = _TICKS_PERIOD // 2


def ticks_diff(ticks1: int, ticks2: int) -> int:
    """Compute the signed difference between two ticks values"""
    diff = (ticks1 - ticks2) & _TICKS_MAX
    diff = ((diff + _TICKS_HALFPERIOD) & _TICKS_MAX) - _TICKS_HALFPERIOD
    return diff


def asyncio_to_blocking(function):
    """Run async function as normal blocking function"""
    def blocking_function(self, *args, **kwargs):
        return asyncio.run(function(self, *args, **kwargs))
    return blocking_function


async def asyncio_check_timeout(flag: Callable, limit: float, timeout_poll: float) -> bool:
    """Test for timeout waiting for specified flag"""
    timed_out = False
    start = time.monotonic()
    while not timed_out and not flag():
        if time.monotonic() - start >= limit:
            timed_out = True
        await asyncio.sleep(timeout_poll)
    return timed_out


class RFMSPI:
    """Base class for SPI type devices on Raspberry Pi"""

    class RegisterBits:
        """Simplify register access"""

        def __init__(self, address: int, *, offset: int = 0, bits: int = 1) -> None:
            assert 0 <= offset <= 7
            assert 1 <= bits <= 8
            assert (offset + bits) <= 8
            self._address = address
            self._mask = 0
            for _ in range(bits):
                self._mask <<= 1
                self._mask |= 1
            self._mask <<= offset
            self._offset = offset

        def __get__(self, obj: Optional["RFM"], objtype: type) -> int:
            reg_value = obj.read_u8(self._address)
            return (reg_value & self._mask) >> self._offset

        def __set__(self, obj: Optional["RFM"], val: int) -> None:
            reg_value = obj.read_u8(self._address)
            reg_value &= ~self._mask
            reg_value |= (val & 0xFF) << self._offset
            obj.write_u8(self._address, reg_value)

    def __init__(
        self,
        spi_bus: int = 0,
        spi_device: int = 0,
        max_speed_hz: int = 5000000,
    ):
        """
        Initialize RFM module on Raspberry Pi
        
        Args:
            spi_bus: SPI bus number (0 or 1)
            spi_device: SPI device/CS number (0 or 1)
            max_speed_hz: SPI clock speed in Hz
        """
        self.spi = spidev.SpiDev()
        self.spi.open(spi_bus, spi_device)
        self.spi.max_speed_hz = max_speed_hz
        self.spi.mode = 0  # SPI mode 0 (polarity=0, phase=0)
        
        # Initialize last RSSI reading
        self.last_rssi = 0.0
        """The RSSI of the last received packet"""
        
        self.last_snr = 0.0
        """The SNR of the last received packet"""
        
        # Initialize timeouts and delays
        self.ack_wait = 0.1
        """The delay time before attempting a retry after not receiving an ACK"""
        
        self.receive_timeout = 0.5
        """The amount of time to poll for a received packet"""
        
        self.xmit_timeout = 2.0
        """The amount of time to wait for the HW to transmit the packet"""
        
        self.ack_retries = 5
        """The number of ACK retries before reporting a failure"""
        
        self.ack_delay: Optional[float] = None
        """The delay time before attempting to send an ACK"""
        
        # Initialize sequence number counter for reliable datagram mode
        self.sequence_number = 0
        
        # Create seen IDs list
        self.seen_ids = bytearray(256)
        
        # Initialize packet header
        self.node = _RH_BROADCAST_ADDRESS
        """The default address of this Node (0-255)"""
        
        self.destination = _RH_BROADCAST_ADDRESS
        """The default destination address for packet transmissions (0-255)"""
        
        self.identifier = 0
        """Automatically set to the sequence number when send_with_ack() used"""
        
        self.flags = 0
        """Upper 4 bits reserved for Reliable Datagram Mode"""
        
        self.radiohead = False
        """Enable RadioHead compatibility"""
        
        self.crc_error_count = 0
        self.timeout_poll = 0.001

    def close(self):
        """Close the SPI connection"""
        self.spi.close()

    def read_into(self, address: int, buf: bytearray, length: Optional[int] = None) -> None:
        """Read a number of bytes from the specified address into the provided buffer"""
        if length is None:
            length = len(buf)
        
        # Read operation: address with MSB=0
        write_buf = [address & 0x7F]
        result = self.spi.xfer2(write_buf + [0] * length)
        
        # Copy result to buffer (skip the first byte which was the address)
        for i in range(length):
            buf[i] = result[i + 1]

    def read_u8(self, address: int) -> int:
        """Read a single byte from the provided address"""
        buf = bytearray(1)
        self.read_into(address, buf, length=1)
        return buf[0]

    def write_from(self, address: int, buf: bytes, length: Optional[int] = None) -> None:
        """Write a number of bytes to the provided address"""
        if length is None:
            length = len(buf)
        
        # Write operation: address with MSB=1
        write_buf = [(address | 0x80) & 0xFF] + list(buf[:length])
        self.spi.xfer2(write_buf)

    def write_u8(self, address: int, val: int) -> None:
        """Write a byte register to the chip"""
        write_buf = [(address | 0x80) & 0xFF, val & 0xFF]
        self.spi.xfer2(write_buf)

    async def asyncio_send(
        self,
        data: bytes,
        *,
        keep_listening: bool = False,
        destination: Optional[int] = None,
        node: Optional[int] = None,
        identifier: Optional[int] = None,
        flags: Optional[int] = None,
    ) -> bool:
        """
        Send a string of data using the transmitter.
        You can only send 252 bytes at a time.
        
        Returns: True if success or False if the send timed out.
        """
        self.idle()  # Stop receiving to clear FIFO
        
        # Combine header and data to form payload
        if self.radiohead:
            payload = bytearray(4)
            payload[0] = self.destination if destination is None else destination
            payload[1] = self.node if node is None else node
            payload[2] = self.identifier if identifier is None else identifier
            payload[3] = self.flags if flags is None else flags
            payload = payload + data
        elif destination is not None:
            payload = destination.to_bytes(1, "big") + data
        else:
            payload = data
        
        assert 0 < len(payload) <= self.max_packet_length
        
        self.fill_fifo(payload)
        self.transmit()
        
        # print regop
        op_mode = self.read_u8(0x01)
        print(f"Operation Mode Register (bits): {op_mode:08b}")
        print("This is packet sent before wait: ", self.packet_sent())
    
    
        # Wait for packet_sent interrupt
        timed_out = await asyncio_check_timeout(
            self.packet_sent, self.xmit_timeout, self.timeout_poll
        )
        
        print("This is packet sent: ", self.packet_sent())
                
        if keep_listening:
            print("Listening after send")
            self.listen()
        else:
            print("Going back to idle")
            self.idle()
        
        self.clear_interrupt()
        return not timed_out

    send = asyncio_to_blocking(asyncio_send)

    async def asyncio_send_with_ack(self, data: bytes) -> bool:
        """
        Reliable Datagram mode:
        Send a packet with data and wait for an ACK response.
        """
        if not self.radiohead:
            raise RuntimeError("send_with_ack only supported in RadioHead mode")
        
        retries_remaining = self.ack_retries if self.ack_retries else 1
        got_ack = False
        self.sequence_number = (self.sequence_number + 1) & 0xFF
        
        while not got_ack and retries_remaining:
            self.identifier = self.sequence_number
            await self.asyncio_send(data, keep_listening=True)
            
            if self.destination == _RH_BROADCAST_ADDRESS:
                got_ack = True
            else:
                ack_packet = await self.asyncio_receive(timeout=self.ack_wait, with_header=True)
                if ack_packet is not None:
                    if ack_packet[3] & _RH_FLAGS_ACK:
                        if ack_packet[2] == self.identifier:
                            got_ack = True
                            break
            
            if not got_ack:
                await asyncio.sleep(self.ack_wait + self.ack_wait * random.random())
            
            retries_remaining -= 1
            self.flags |= _RH_FLAGS_RETRY
        
        self.flags = 0
        return got_ack

    send_with_ack = asyncio_to_blocking(asyncio_send_with_ack)

    async def asyncio_receive(
        self,
        *,
        keep_listening: bool = True,
        with_header: bool = False,
        timeout: Optional[float] = None,
    ) -> Optional[bytearray]:
        """
        Wait to receive a packet from the receiver.
        
        Returns the payload bytes or None if timeout elapsed.
        """
        if not self.radiohead and with_header:
            raise RuntimeError("with_header only supported for RadioHead mode")
        
        if timeout is None:
            timeout = self.receive_timeout
        
        self.listen()
        timed_out = await asyncio_check_timeout(self.payload_ready, timeout, self.timeout_poll)
        
        packet = None
        self.last_rssi = self.rssi
        self.last_snr = self.snr
        self.idle()
        
        if not timed_out:
            if self.enable_crc and self.crc_error:
                self.crc_error_count += 1
            else:
                packet = self.read_fifo()
                if (packet is not None) and self.radiohead:
                    if len(packet) < 5:
                        packet = None
                    if packet is not None:
                        if (
                            self.node != _RH_BROADCAST_ADDRESS
                            and packet[0] != _RH_BROADCAST_ADDRESS
                            and packet[0] != self.node
                        ):
                            packet = None
                        if not with_header and packet is not None:
                            packet = packet[4:]
        
        if keep_listening:
            self.listen()
        else:
            self.idle()
        
        self.clear_interrupt()
        return packet

    receive = asyncio_to_blocking(asyncio_receive)

    async def asyncio_receive_with_ack(
        self,
        *,
        keep_listening: bool = True,
        with_header: bool = False,
        timeout: Optional[float] = None,
    ) -> Optional[bytearray]:
        """
        Reliable Datagram mode:
        Wait to receive a packet then send an ACK in response.
        """
        if not self.radiohead:
            raise RuntimeError("receive_with_ack only supported for RadioHead mode")
        
        if timeout is None:
            timeout = self.receive_timeout
        
        self.listen()
        timed_out = await asyncio_check_timeout(self.payload_ready, timeout, self.timeout_poll)
        
        packet = None
        self.last_rssi = self.rssi
        self.last_snr = self.snr
        self.idle()
        
        if not timed_out:
            if self.enable_crc and self.crc_error:
                self.crc_error_count += 1
            else:
                packet = self.read_fifo()
                if (packet is not None) and self.radiohead:
                    if len(packet) < 5:
                        packet = None
                    if packet is not None:
                        if (
                            self.node != _RH_BROADCAST_ADDRESS
                            and packet[0] != _RH_BROADCAST_ADDRESS
                            and packet[0] != self.node
                        ):
                            packet = None
                        elif ((packet[3] & _RH_FLAGS_ACK) == 0) and (
                            packet[0] != _RH_BROADCAST_ADDRESS
                        ):
                            if self.ack_delay is not None:
                                await asyncio.sleep(self.ack_delay)
                            
                            await self.asyncio_send(
                                b"!",
                                destination=packet[1],
                                node=packet[0],
                                identifier=packet[2],
                                flags=(packet[3] | _RH_FLAGS_ACK),
                                keep_listening=keep_listening,
                            )
                            
                            if (self.seen_ids[packet[1]] == packet[2]) and (
                                packet[3] & _RH_FLAGS_RETRY
                            ):
                                packet = None
                            else:
                                self.seen_ids[packet[1]] = packet[2]
                        
                        if packet is not None and (packet[3] & _RH_FLAGS_ACK) != 0:
                            packet = None
                        
                        if not with_header and packet is not None:
                            packet = packet[4:]
        
        if keep_listening:
            self.listen()
        else:
            self.idle()
        
        self.clear_interrupt()
        return packet

    receive_with_ack = asyncio_to_blocking(asyncio_receive_with_ack)
