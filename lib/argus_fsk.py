# SPDX-FileCopyrightText: 2024 Jerry Needell for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_rfm.rfm9xfsk`
====================================================

CircuitPython module for the RFM95/6/7/8 FSK 433/915mhz radio modules.

* Author(s): Jerry Needell

This is my adaptation of the Adafruit CircuitPython RFM9x library to use with rpi
specially made to operate argus satellite
"""

import time
from typing import Literal, Optional

from gpiozero import Button

from lib.pin_definitions import Definitions
from lib.rfmspi import RFMSPI
import lib.argus_fsk_consts as CONST



# pylint: disable=too-many-instance-attributes
# pylint: disable=too-many-public-methods
class RFM9xFSK(RFMSPI):
    """Interface to a RFM95/6/7/8 FSK radio module.  Allows sending and
    receiving bytes of data in FSK  mode at a support board frequency
    (433/915mhz).

    :param int frequency: The center frequency to configure for radio transmission and reception.
        Must be a frequency supported by your hardware (i.e. either 433 or 915mhz).
    :param bytes sync_word: A byte string up to 8 bytes long which represents the syncronization
        word used by received and transmitted packets. Read the datasheet for a full understanding
        of this value! However by default the library will set a value that matches the RadioHead
        Arduino library.
    :param int preamble_length: The number of bytes to pre-pend to a data packet as a preamble.
        This is by default 4 to match the RadioHead library.
    :param bool high_power: Indicate if the chip is a high power variant that supports boosted
        transmission power.  The default is True as it supports the common RFM69HCW modules sold by
        Adafruit.

    Also note this library tries to be compatible with raw RadioHead Arduino
    library communication. This means the library sets up the radio modulation
    to match RadioHead's defaults.
    Advanced RadioHead features like address/node specific packets
    or "reliable datagram" delivery are supported however due to the
    limitations noted, "reliable datagram" is still subject to missed packets.
    """

    operation_mode = RFMSPI.RegisterBits(CONST._OP_MODE, bits=3)
    low_frequency_mode = RFMSPI.RegisterBits(CONST._OP_MODE, offset=3, bits=1)
    modulation_type = RFMSPI.RegisterBits(CONST._OP_MODE, offset=5, bits=2)
    # Long range/LoRa mode can only be set in sleep mode!
    long_range_mode = RFMSPI.RegisterBits(CONST._OP_MODE, offset=7, bits=1)
    sync_on = RFMSPI.RegisterBits(CONST._SYNC_CONFIG, offset=4, bits=1)
    sync_size = RFMSPI.RegisterBits(CONST._SYNC_CONFIG, offset=0, bits=3)
    preamble_polarity = RFMSPI.RegisterBits(CONST._SYNC_CONFIG, offset=5, bits=1)
    output_power = RFMSPI.RegisterBits(CONST._PA_CONFIG, bits=4)
    max_power = RFMSPI.RegisterBits(CONST._PA_CONFIG, offset=4, bits=3)
    pa_select = RFMSPI.RegisterBits(CONST._PA_CONFIG, offset=7, bits=1)
    pa_dac = RFMSPI.RegisterBits(CONST._PA_DAC, bits=3)
    dio0_mapping = RFMSPI.RegisterBits(CONST._DIO_MAPPING1, offset=6, bits=2)
    lna_boost_hf = RFMSPI.RegisterBits(CONST._LNA, offset=0, bits=2)
    rx_bw_mantissa = RFMSPI.RegisterBits(CONST._RX_BW, offset=3, bits=2)
    rx_bw_exponent = RFMSPI.RegisterBits(CONST._RX_BW, offset=0, bits=3)
    afc_bw_mantissa = RFMSPI.RegisterBits(CONST._AFC_BW, offset=3, bits=2)
    afc_bw_exponent = RFMSPI.RegisterBits(CONST._AFC_BW, offset=0, bits=3)
    packet_format = RFMSPI.RegisterBits(CONST._PACKET_CONFIG_1, offset=7, bits=1)
    dc_free = RFMSPI.RegisterBits(CONST._PACKET_CONFIG_1, offset=5, bits=2)
    crc_on = RFMSPI.RegisterBits(CONST._PACKET_CONFIG_1, offset=4, bits=1)
    crc_auto_clear_off = RFMSPI.RegisterBits(CONST._PACKET_CONFIG_1, offset=3, bits=1)
    address_filter = RFMSPI.RegisterBits(CONST._PACKET_CONFIG_1, offset=1, bits=2)
    crc_type = RFMSPI.RegisterBits(CONST._PACKET_CONFIG_1, offset=0, bits=1)
    
    agc = RFMSPI.RegisterBits(CONST._RX_CFG, offset=3, bits=1)
    afc_auto_on = RFMSPI.RegisterBits(CONST._RX_CFG, offset=4, bits=1)
    
    data_mode = RFMSPI.RegisterBits(CONST._PACKET_CONFIG_2, offset=6, bits=1)
    payload_length = RFMSPI.RegisterBits(CONST._PACKET_CONFIG_2,  bits=8)    # this is going  over two registers, not sure if this will work
    
    mode_ready = RFMSPI.RegisterBits(CONST._IRQ_FLAGS_1, offset=7)
    ook_bit_sync_on = RFMSPI.RegisterBits(CONST._OOK_PEAK, offset=5, bits=1)
    ook_thresh_type = RFMSPI.RegisterBits(CONST._OOK_PEAK, offset=4, bits=2)
    ook_thresh_step = RFMSPI.RegisterBits(CONST._OOK_PEAK, offset=0, bits=3)
    ook_peak_thresh_dec = RFMSPI.RegisterBits(CONST._OOK_AVG, offset=5, bits=3)
    ook_average_offset = RFMSPI.RegisterBits(CONST._OOK_AVG, offset=2, bits=2)
    ook_average_thresh_filt = RFMSPI.RegisterBits(CONST._OOK_AVG, offset=0, bits=2)

    def __init__(  # noqa: PLR0913
        self,
        config_dict: dict,
    ) -> None:
        super().__init__() # here I should pass the stuff for  spi communication, but for now I will have this hardcoded on the layer below
        self.module = "RFM9X"
        self.high_power = int(config_dict.get("high_power", True))
        self.max_packet_length = config_dict.get("max_packet_length", 100)
        
        # No device type check!  Catch an error from the very first request and
        # throw a nicer message to indicate possible wiring problems.
        version = self.read_u8(address=CONST._VERSION)
        if version != 18:
            raise RuntimeError(
                "Failed to find rfm9x with expected version -- check wiring. Version found:",
                hex(version),
            )

        # Set sleep mode, wait 10s and confirm in sleep mode (basic device check).
        # Also set long range mode (LoRa mode) as it can only be done in sleep.
        self.sleep()
        time.sleep(0.01)
        self.long_range_mode = False
        if self.operation_mode != CONST.SLEEP_MODE or self.long_range_mode:
            raise RuntimeError("Failed to configure radio for FSK mode, check wiring!")
        
        # clear default setting for access to LF registers if frequency > 525MHz
        if config_dict.get("frequency", 433.707) > 525:
            self.low_frequency_mode = 0
            
        # turn on afc
        self.afc_auto_on = config_dict.get("afc_auto", 1)
        
        # turn on agc
        self.agc = 1
        
        # change preamble polarity to 0x55
        self.preamble_polarity = 1  # 0x55
        
        
        # set packet mode
        self.data_mode = config_dict.get("data_mode", 0)  # packet mode
        
        # Set mode idle
        self.idle()
        # Setup the chip in a similar way to the RadioHead RFM69 library.
        # Set FIFO TX condition to not empty and the default FIFO threshold to 15.
        self.write_u8(CONST._FIFO_THRESH, 0b10001111)
        # Set the syncronization word.
        self.sync_word = config_dict.get("sync_word", b"\x2D\xD4")
        self.preamble_length = config_dict.get("preamble_length", 4)  # Set the preamble length.
        self.frequency_mhz = config_dict.get("frequency", 433.707)  # Set frequency.
        
        # set the maximum payload length which is 100 bytes
        self.payload_length = config_dict.get("max_packet_length", 100)
        
        
        # Configure modulation for RadioHead library GFSK_Rb250Fd250 mode
        # by default.  Users with advanced knowledge can manually reconfigure
        # for any other mode (consulting the datasheet is absolutely
        # necessary!).
        self.modulation_shaping = config_dict.get("bt", 1.0)
        self.bitrate = config_dict.get("bit_rate", 4000)  # 4kbps
        self.frequency_deviation = config_dict.get("fdev", 1000)  # 1khz
        self.rx_bandwidth = config_dict.get("rx_bw", 15000)  # 10khz
        
        self.afc_bw_mantissa = 0b00
        self.afc_bw_exponent = 0b000
        
        self.packet_format = config_dict.get("packet_format", 0)  # variable length
        self.dc_free = config_dict.get("whitening", 0)  # no whitening
        # Set transmit power to 13 dBm, a safe value any module supports.
        self.tx_power = config_dict.get("power", 20)
        
        # Default to enable CRC checking on incoming packets.
        self.enable_crc = config_dict.get("crc", False)
        """CRC Enable state"""
        self.snr = None

    def idle(self) -> None:
        """Enter idle standby mode."""
        self.operation_mode = CONST.STANDBY_MODE

    def sleep(self) -> None:
        """Enter sleep mode."""
        self.operation_mode = CONST.SLEEP_MODE

    def listen(self) -> None:
        """Listen for packets to be received by the chip.  Use :py:func:`receive`
        to listen, wait and retrieve packets as they're available.
        """
        self.operation_mode = CONST.RX_MODE
        self.dio0_mapping = 0b00  # Interrupt on rx done.

    def transmit(self) -> None:
        """Transmit a packet which is queued in the FIFO.  This is a low level
        function for entering transmit mode and more.  For generating and
        transmitting a packet of data use :py:func:`send` instead.
        """
        self.operation_mode = CONST.TX_MODE
        self.dio0_mapping = 0b00  # Interrupt on tx done.

    @property
    def sync_word(self) -> bytearray:
        """The synchronization word value.  This is a byte string up to 8 bytes long (64 bits)
        which indicates the synchronization word for transmitted and received packets. Any
        received packet which does not include this sync word will be ignored. The default value
        is 0x2D, 0xD4 which matches the RadioHead RFM69 library. Setting a value of None will
        disable synchronization word matching entirely.
        """
        # Handle when sync word is disabled..
        if not self.sync_on:
            print("Setting sync word, but sync is disabled")
            return None
        # Sync word is not disabled so read the current value.
        sync_word_length = self.sync_size + 1  # Sync word size is offset by 1
        # according to datasheet.
        sync_word = bytearray(sync_word_length)
        self.read_into(CONST._SYNC_VALUE_1, sync_word)
        return sync_word

    @sync_word.setter
    def sync_word(self, val: Optional[bytearray]) -> None:
        # Handle disabling sync word when None value is set.
        print("Writing val: ", val)
        if val is None:
            print("sync word is none, disabling")
            self.sync_on = 0
        else:
            # Check sync word is at most 8 bytes.
            assert 1 <= len(val) <= 8
            # Update the value, size and turn on the sync word.
            self.write_from(CONST._SYNC_VALUE_1, val)
            self.sync_size = len(val) - 1  # Again sync word size is offset by
            # 1 according to datasheet.
            self.sync_on = 1
    
    @property
    def bitrate(self) -> float:
        """The modulation bitrate in bits/second (or chip rate if Manchester encoding is enabled).
        Can be a value from ~489 to 32mbit/s, but see the datasheet for the exact supported
        values.
        """
        msb = self.read_u8(CONST._BITRATE_MSB)
        lsb = self.read_u8(CONST._BITRATE_LSB)
        return CONST.FXOSC / ((msb << 8) | lsb)

    @bitrate.setter
    def bitrate(self, val: float) -> None:
        assert (CONST.FXOSC / 65535) <= val <= 32000000.0
        # Round up to the next closest bit-rate value with addition of 0.5.
        bitrate = int((CONST.FXOSC / val) + 0.5) & 0xFFFF
        self.write_u8(CONST._BITRATE_MSB, bitrate >> 8)
        self.write_u8(CONST._BITRATE_LSB, bitrate & 0xFF)

    @property
    def modulation_shaping(self) -> int:
        """
        The modulation shaping setting. Possible values are: 0 (no shaping), 1 (BT=1.0),
        2 (BT=0.5), and 3 (BT=0.3).
        """
        val = self.read_u8(CONST._PA_RAMP) >> 5
        shaping_map = {
            0b00: 0,
            0b01: 1.0,
            0b10: 0.5,
            0b11: 0.3,
        }
        return shaping_map.get(val, 0)

    @modulation_shaping.setter
    def modulation_shaping(self, val: float) -> None:
        possible_values = [0, 1.0, 0.5, 0.3]
        
        assert val in possible_values, f"modulation shaping must be one of {possible_values}"
        shaping_map = {
            0: 0b00,
            1.0: 0b01,
            0.5: 0b10,
            0.3: 0b11,
        }
        
        # only want to change the correct bits without affecting the other bits
        prev_reg_value = self.read_u8(CONST._PA_RAMP) & 0b00011111
        self.write_u8(CONST._PA_RAMP, (shaping_map[val] << 5) | prev_reg_value)
    
    @property
    def rx_bandwidth(self) -> float:
        """
        Receiver bandwidth in Hertz.

        RxBw = FXOSC / (RxBwMant * 2^(RxBwExp + 2))
        """
        mant_map = {
            0b00: 16,
            0b01: 20,
            0b10: 24,
        }

        mant = mant_map.get(self.rx_bw_mantissa)
        exp = self.rx_bw_exponent

        if mant is None:
            return 0.0

        return CONST.FXOSC / (mant * (2 ** (exp + 2)))

    @rx_bandwidth.setter
    def rx_bandwidth(self, val: float) -> None:
        """
        Set receiver bandwidth in Hertz.
        """
        assert val > 0

        mant_map = {
            0b00: 16,
            0b01: 20,
            0b10: 24,
        }

        best_error = None
        best_mant = None
        best_exp = None

        for mant_bits, mant in mant_map.items():
            for exp in range(0, 8):  # 3-bit exponent
                bw = CONST.FXOSC / (mant * (2 ** (exp + 2)))
                error = abs(bw - val)

                if best_error is None or error < best_error:
                    best_error = error
                    best_mant = mant_bits
                    best_exp = exp

        self.rx_bw_mantissa = best_mant
        self.rx_bw_exponent = best_exp


    @property
    def frequency_deviation(self) -> float:
        """The frequency deviation in Hertz."""
        msb = self.read_u8(CONST._FDEV_MSB)
        lsb = self.read_u8(CONST._FDEV_LSB)
        return CONST.FSTEP * ((msb << 8) | lsb)

    @frequency_deviation.setter
    def frequency_deviation(self, val: float) -> None:
        assert 0 <= val <= (CONST.FSTEP * 16383)  # fdev is a 14-bit unsigned value
        # Round up to the next closest integer value with addition of 0.5.
        fdev = int((val / CONST.FSTEP) + 0.5) & 0x3FFF
        self.write_u8(CONST._FDEV_MSB, fdev >> 8)
        self.write_u8(CONST._FDEV_LSB, fdev & 0xFF)

    @property
    def temperature(self) -> float:
        """The internal temperature of the chip.. See Sec 5.5.7 of the DataSheet
        calibrated or very accurate.
        """
        temp = self.read_u8(CONST._TEMP)
        
        if temp > 127:
            signed_val = temp - 256
        else:
            signed_val = temp

        # Step 2: Apply the -1°C per Lsb slope
        temp = signed_val * -1
        return temp

    @property
    def preamble_length(self) -> int:
        """The length of the preamble for sent and received packets, an unsigned
        16-bit value.  Received packets must match this length or they are
        ignored! Set to 4 to match the RF69.
        """
        msb = self.read_u8(CONST._PREAMBLE_MSB)
        lsb = self.read_u8(CONST._PREAMBLE_LSB)
        return ((msb << 8) | lsb) & 0xFFFF

    @preamble_length.setter
    def preamble_length(self, val: int) -> None:
        assert 0 <= val <= 65535
        self.write_u8(CONST._PREAMBLE_MSB, (val >> 8) & 0xFF)
        self.write_u8(CONST._PREAMBLE_LSB, val & 0xFF)

    @property
    def frequency_mhz(self) -> Literal[433.0, 915.0]:
        """The frequency of the radio in Megahertz. Only the allowed values for
        your radio must be specified (i.e. 433 vs. 915 mhz)!
        """
        msb = self.read_u8(CONST._FRF_MSB)
        mid = self.read_u8(CONST._FRF_MID)
        lsb = self.read_u8(CONST._FRF_LSB)
        frf = ((msb << 16) | (mid << 8) | lsb) & 0xFFFFFF
        frequency = (frf * CONST.FSTEP) / 1000000.0
        return frequency

    @frequency_mhz.setter
    def frequency_mhz(self, val: Literal[433.0, 915.0]) -> None:
        if val < 240 or val > 960:
            raise RuntimeError("frequency_mhz must be between 240 and 960")
        # Calculate FRF register 24-bit value.
        frf = int((val * 1000000.0) / CONST.FSTEP) & 0xFFFFFF
        # Extract byte values and update registers.
        msb = frf >> 16
        mid = (frf >> 8) & 0xFF
        lsb = frf & 0xFF
        self.write_u8(CONST._FRF_MSB, msb)
        self.write_u8(CONST._FRF_MID, mid)
        self.write_u8(CONST._FRF_LSB, lsb)

    @property
    def tx_power(self) -> int:
        """The transmit power in dBm. Can be set to a value from 5 to 23 for
        high power devices (RFM95/96/97/98, high_power=True) or -1 to 14 for low
        power devices. Only integer power levels are actually set (i.e. 12.5
        will result in a value of 12 dBm).
        The actual maximum setting for high_power=True is 20dBm but for values > 20
        the PA_BOOST will be enabled resulting in an additional gain of 3dBm.
        The actual setting is reduced by 3dBm.
        The reported value will reflect the reduced setting.
        """
        if self.high_power:
            return self.output_power + 5
        return self.output_power - 1

    @tx_power.setter
    def tx_power(self, val: int) -> None:
        val = int(val)
        if self.high_power:
            if val < 5 or val > 23:
                raise RuntimeError("tx_power must be between 5 and 23")
            # Enable power amp DAC if power is above 20 dB.
            # Lower setting by 3db when PA_BOOST enabled - see Data Sheet  Section 6.4
            if val > 20:
                self.pa_dac = CONST._PA_DAC_ENABLE
                val -= 3
            else:
                self.pa_dac = CONST._PA_DAC_DISABLE
            self.pa_select = int(True)
            self.output_power = (val - 5) & 0x0F
        else:
            assert -1 <= val <= 14
            self.pa_select = int(False)
            self.max_power = 0b111  # Allow max power output.
            self.output_power = (val + 1) & 0x0F

    @property
    def rssi(self) -> float:
        """
        The received strength indicator (in dBm)
        not clear if it is instant or if it of the last received message
        it should be constant, but from testing it seems to be from the last received message
        seeing as it only changes when it receives a message (messages we have been received is noise)
        """
        # Read RSSI register and convert to value using formula in datasheet.
        # Remember in LoRa mode the payload register changes function to RSSI!
        raw_rssi = self.read_u8(CONST._RSSI_VALUE)   # this seems to be the value for the last received packet
        
        return -raw_rssi / 2.0

    @property
    def enable_crc(self) -> bool:
        """Set to True to enable hardware CRC checking of incoming packets.
        Incoming packets that fail the CRC check are not processed.  Set to
        False to disable CRC checking and process all incoming packets."""
        return self.crc_on

    @enable_crc.setter
    def enable_crc(self, val: bool) -> None:
        # Optionally enable CRC checking on incoming packets.
        if val:
            self.crc_on = 1
            self.crc_type = 0  # use CCITT for RF69 compatibility
        else:
            self.crc_on = 0

    @property
    def crc_error(self) -> bool:
        """crc status"""
        return (self.read_u8(CONST._IRQ_FLAGS_2) & 0x2) >> 1

    @property
    def enable_address_filter(self) -> bool:
        """Set to True to enable address filtering.
        Incoming packets that do no match the node address  or broadcast address
        will be ignored."""
        return self.address_filter

    @enable_address_filter.setter
    def enable_address_filter(self, val: bool) -> None:
        # Enable address filtering  on incoming packets.
        if val:
            self.address_filter = 2  # accept node address or broadcast address
        else:
            self.address_filter = 0

    @property
    def fsk_node_address(self) -> int:
        """Node Address for Address Filtering"""
        return self.read_u8(CONST._NODE_ADDR)

    @fsk_node_address.setter
    def fsk_node_address(self, val: int) -> None:
        assert 0 <= val <= 255
        self.write_u8(CONST._NODE_ADDR, val)

    @property
    def fsk_broadcast_address(self) -> int:
        """Node Address for Address Filtering"""
        return self.read_u8(CONST._BROADCAST_ADDR)

    @fsk_broadcast_address.setter
    def fsk_broadcast_address(self, val: int) -> None:
        assert 0 <= val <= 255
        self.write_u8(CONST._BROADCAST_ADDR, val)

    @property
    def ook_fixed_threshold(self) -> int:
        """Fixed threshold for data slicer in OOK mode"""
        return self.read_u8(CONST._OOK_FIX)

    @ook_fixed_threshold.setter
    def ook_fixed_threshold(self, val: int) -> None:
        assert 0 <= val <= 255
        self.write_u8(CONST._OOK_FIX, val)

    def packet_sent(self) -> bool:
        """Transmit status"""
        return (self.read_u8(CONST._IRQ_FLAGS_2) & 0x8) >> 3

    def payload_ready(self) -> bool:
        """Receive status"""
        return (self.read_u8(CONST._IRQ_FLAGS_2) & 0x4) >> 2

    def clear_interrupt(self) -> None:
        """Clear interrupt Flags"""
        self.write_u8(CONST._IRQ_FLAGS_1, 0xFF)
        self.write_u8(CONST._IRQ_FLAGS_2, 0xFF)

    def fill_fifo(self, payload: bytes) -> None:
        """Write the payload to the FIFO."""
        complete_payload = bytearray(1)  # prepend packet length to payload
        complete_payload[0] = len(payload)
        # put the payload lengthe in the beginning of the packet for RFM69
        complete_payload = complete_payload + payload
        # Write payload to transmit fifo
        self.write_from(CONST._FIFO, complete_payload)

    def read_fifo(self) -> Optional[bytearray]:
        """Read the data from the FIFO."""
        # Read the length of the FIFO.
        fifo_length = self.read_u8(CONST._FIFO)
        packet = None  # return None if FIFO empty
        if fifo_length > 0:  # read and clear the FIFO if anything in it
            packet = bytearray(fifo_length)
            # read the packet
            self.read_into(CONST._FIFO, packet, fifo_length)
        return packet
