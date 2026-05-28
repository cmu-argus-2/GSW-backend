import math
import time
from collections import namedtuple

try:
    import spidev
except ImportError:
    print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    print("could not import spidev, cannot connect to satellite via RF.")
    print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
from gpiozero import Button

from lib.pin_definitions import Definitions

# TODO: FALTA FDEV, BR, PREAMBLE SIZE NOS PARAMS
#       PACKET TYPE, WHITE, CRC, PL LENGTH
#       RX BW


class GFSK(object):
    def __init__(
        self,
        channel,
        txrx_state_pin,
        fifo_thresh_pin,
        fifo_full_pin,
        fifo_empty_pin,
        mode_ready_pin,
        address,
        freq,
        tx_power,
        packet_type,
        whitening,
        crc_on,
        crc_type,
        crc_autoclear,
        receive_all,
        acks,
        crypto  
    ):
        self._channel = channel
        self._mode = None
        self._freq = freq
        self._tx_power = tx_power
        self._receive_all = receive_all
        self._acks = acks

        self._last_header_id = 0

        self._rx_state = 0
        self._partial_data = []
        self._tx_done = True
        self._tx_payload = None

        self._last_payload = None
        self.crypto = crypto

        self.cad_timeout = 0
        self.send_retries = 2
        self.wait_packet_sent_timeout = 0.2
        self.retry_timeout = 0.2

        self.crc_error_count = 0
        
        self.receive_success = False
        self.last_payload = None

        self.dioTRxState = Button(txrx_state_pin, pull_up=False)
        print("TXRX PIN", txrx_state_pin)
        self.dioFifoThresh = Button(fifo_thresh_pin, pull_up=False)
        print("FIFO THRESH PIN", fifo_thresh_pin)
        self.dioFifoFull = Button(fifo_full_pin, pull_up=False)
        print("FIFO FULL PIN", fifo_full_pin)
        self.dioFifoEmpty = Button(fifo_empty_pin, pull_up=False)
        print("FIFO EMPTY PIN", fifo_empty_pin)
        self.dioModeReady = Button(mode_ready_pin, pull_up=False)
        print("MODE READY PIN", mode_ready_pin)

        self.spi = spidev.SpiDev()
        self.spi.open(0, self._channel)
        self.spi.max_speed_hz = 5000000

        self._spi_write(
            Definitions.REG_01_OP_MODE,
            Definitions.MODE_SLEEP
        )
        time.sleep(0.1)

        self.setDIOMapping((0b00) << 6, (0b00) << 4, (0b00) << 2, 0b00,
                           (0b00) << 6, (0b11) << 4)

        self.setOpParams(Definitions.FSK_OOK_MODE,
                         Definitions.FSK_MOD,
                         Definitions.LOW_FREQ_MODE)

        self.set_mode_idle()

        #self.setRfFrequency(434_707_000 + 10_000)
        self.setRfFrequency(434_707_000 + 10_000 - 200)
        self.setFDev(7_200)
        self.setBitRate(19_200)
        self.setPaRamp(Definitions.PA_MOD_BT_05, 0b1001)
        self.setPreambleSize(128)
        self.setSyncWord(0b00 << 6, 0b1 << 5, 0b1 << 4, 0b0 << 3)
        self.setPacketConfig1(Definitions.PACKET_VAR_LEN,
                              Definitions.PACKET_DC_WHITE,
                              Definitions.PACKET_CRC_ON,
                              Definitions.PACKET_CRC_AUTOCLEAR_ON,
                              Definitions.PACKET_ADDR_FLTR_NONE,
                              Definitions.PACKET_CRC_CCITT)

        self.setPacketConfig2(Definitions.PACKET_DATA_MODE_PACK,
                              Definitions.PACKET_IOHOME_OFF,
                              Definitions.PACKET_BEACON_OFF,
                              255)

        self.setFifoTresh(Definitions.START_COND_FIFO_EMPTY, 30)

        self.setPaConfig(Definitions.PA_SELECT_BOOST, 0, 23)

        self.setRxBw(0b10 << 3, 2)

        self.setRxConfig(0b0 << 7, 0b0 << 6, 0b0 << 5, 0b1 << 4, 0b1 << 3, 0b110)

        self.setPreambleDetector(0b1 << 7, 0b10 << 5, 0b1010)

        # CRC Enable
        self.enable_crc = True
        
        
        self.thresTime = None

    def setDIOMapping(self, dio0: int, dio1: int, dio2: int, dio3: int, dio4: int, dio5: int):
        assert (True if dio0 in [
            0b00000000,
            0b01000000,
            0b10000000,
            0b11000000]
            else False)
        assert (True if dio1 in [
            0b000000,
            0b010000,
            0b100000,
            0b110000]
            else False)
        assert (True if dio2 in [
            0b0000,
            0b0100,
            0b1000,
            0b1100]
            else False)
        assert (True if dio3 in [
            0b00, 0b01,
            0b01, 0b11]
            else False)
        assert (True if dio4 in [
            0b00000000,
            0b01000000,
            0b10000000,
            0b11000000]
            else False)
        assert (True if dio5 in [
            0b000000,
            0b010000,
            0b100000,
            0b110000]
            else False)

        regDio1 = dio0 | dio1 | dio2 | dio3
        regDio2 = self._spi_read(Definitions.REG_41_DIO_MAPPING2)
        # print("ORIG REGDIO2:", regDio2)
        regDio2 &= 0b00001111
        regDio2 |= dio4 | dio5

        print("REGDIO1", bin(regDio1), "DIO0", bin(dio0), "DIO1", bin(dio1),
              "DIO2", bin(dio2), "DIO3", bin(dio3))
        print("REGDIO2", bin(regDio2), "DIO4", bin(dio4), "DIO5", bin(dio5))

        self._spi_write(Definitions.REG_40_DIO_MAPPING1, [regDio1])
        self._spi_write(Definitions.REG_41_DIO_MAPPING2, [regDio2])

    def setOpParams(self, longRngMode: int, modtype: int, lowFreqMode: int):
        assert (True if longRngMode in [
            Definitions.LORA_MODE,
            Definitions.FSK_OOK_MODE]
            else False)

        assert (True if modtype in [
            Definitions.FSK_MOD,
            Definitions.OOK_MOD]
            else False)

        assert (True if lowFreqMode in [
            Definitions.LOW_FREQ_MODE,
            Definitions.HIGH_FREQ_MODE]
            else False)

        currentOpMode = self._spi_read(Definitions.REG_01_OP_MODE)
        currentOpMode &= 0b00010111
        currentOpMode |= longRngMode | modtype | lowFreqMode
        # O shifts podem estar guardados nas constantes para diminuir a chance de meme

        print(bin(currentOpMode))

        self._spi_write(Definitions.REG_01_OP_MODE, [currentOpMode])

    def setRfFrequency(self, rfFrequency: int):
        rfFreq = int(rfFrequency / Definitions.FSTEP)
        rfFreqMSB = (rfFreq & 0xFF0000) >> 16
        rfFreqMID = (rfFreq & 0xFF00) >> 8
        rfFreqLSB = rfFreq & 0xFF

        print("rfFreq", hex(rfFreq), "MSB", hex(rfFreqMSB), "MID", hex(rfFreqMID), "LSB", hex(rfFreqLSB))

        self._spi_write(Definitions.REG_06_FRF_MSB, [rfFreqMSB])
        self._spi_write(Definitions.REG_07_FRF_MID, [rfFreqMID])
        self._spi_write(Definitions.REG_08_FRF_LSB, [rfFreqLSB])

    def setFDev(self, freqDev: int):
        fdev = int(freqDev / Definitions.FSTEP)
        fdevMSB = ((fdev & 0xFF00) >> 8) & 0b00111111
        fdevLSB = fdev & 0xFF
        # print("FDEV", hex(fdev), "FDEV MSB", hex(fdevMSB), "FDEV LSB", hex(fdevLSB))

        currentFdevMSB = self._spi_read(Definitions.REG_04_FDEV_MSB)
        currentFdevMSB &= 0b11000000  # Reset non reserved fdev bits to 0
        currentFdevMSB |= fdevMSB

        print("FDEV MSB", bin(currentFdevMSB))
        print("FDEV LSB", bin(fdevLSB))

        self._spi_write(Definitions.REG_04_FDEV_MSB, [currentFdevMSB])
        self._spi_write(Definitions.REG_05_FDEV_LSB, [fdevLSB])

    def setBitRate(self, bitRate: int):
        br = int(Definitions.FXOSC / (bitRate))
        brMSB = (br & 0xFF00) >> 8
        brLSB = br & 0xFF
        print("BR MSB", hex(brMSB), "BR LSB", hex(brLSB))
        self._spi_write(Definitions.REG_02_BR_MSB, [brMSB])
        self._spi_write(Definitions.REG_03_BR_LSB, [brLSB])

    def setPaRamp(self, modShaping: int, rampUp: int):
        assert (True if modShaping in [
            Definitions.PA_MOD_NONE,
            Definitions.PA_MOD_BT_1,
            Definitions.PA_MOD_BT_03,
            Definitions.PA_MOD_BT_05]
            else False)

        rampUp &= 0b1111
        PaRamp = self._spi_read(Definitions.REG_0A_PARAMP)
        PaRamp &= 10010000
        PaRamp = modShaping | rampUp
        print("PARAMP", bin(PaRamp), "MODSHAP", bin(modShaping), "RAMPUP", bin(rampUp))
        self._spi_write(Definitions.REG_0A_PARAMP, [PaRamp])

    def setPreambleSize(self, preambleSize: int):
        preambleSize &= 0xFFFF
        preambleMSB = (preambleSize & 0xFF00) >> 8
        preambleLSB = (preambleSize & 0xFF)

        print("PREAMBLE MSB", bin(preambleMSB))
        print("PREAMBLE LSB", bin(preambleLSB))
        self._spi_write(Definitions.REG_25_FSK_PREAMBLE_MSB, [preambleMSB])
        self._spi_write(Definitions.REG_26_FSK_PREAMBLE_LSB, [preambleLSB])

    def setSyncWord(self, autoRestartMode: int, preamblePolarity: int,
                    syncOn: int, fifoFillCondition: int):
        
        # TODO - SYNCWORD IS HARDCODED TO 1ACFFC1D
        assert (True if autoRestartMode in [
            0b00 << 6, 0b01 << 6, 0b10 << 6]
            else False)
        assert (True if preamblePolarity in [
            0b0 << 5, 0b1 << 5] else False)
        assert (True if syncOn in [
            0b0 << 4, 0b1 << 4] else False)
        assert (True if fifoFillCondition in [
            0b0 << 3, 0b1 << 3] else False)
    
        syncSize = 3  # Must be set to actual size - 1 bytes
        regSyncConfig = autoRestartMode | preamblePolarity | syncOn |\
            fifoFillCondition | syncSize

        syncWord1 = 0x1A
        syncWord2 = 0xCF
        syncWord3 = 0xFC
        syncWord4 = 0x1D

        print("SYNC CONFIG", bin(regSyncConfig))

        self._spi_write(Definitions.REG_27_SYNC_CONFIG, [regSyncConfig])
        self._spi_write(Definitions.REG_28_SYNC_VALUE1, [syncWord1])
        self._spi_write(Definitions.REG_29_SYNC_VALUE2, [syncWord2])
        self._spi_write(Definitions.REG_2A_SYNC_VALUE3, [syncWord3])
        self._spi_write(Definitions.REG_2B_SYNC_VALUE4, [syncWord4])

    def setPacketConfig1(self, packetFormat: int, dcFree: int, 
                         crcOn: int, crcAutoClear: int,
                         addressFiltering: int, crcType: int):
    
        assert (True if packetFormat in [
            Definitions.PACKET_FIX_LEN,
            Definitions.PACKET_VAR_LEN]
            else False)

        assert (True if dcFree in [
            Definitions.PACKET_DC_NONE,
            Definitions.PACKET_DC_MANCHESTER,
            Definitions.PACKET_DC_WHITE]
            else False)

        assert (True if crcOn in [
            Definitions.PACKET_CRC_OFF,
            Definitions.PACKET_CRC_ON]
            else False)

        assert (True if crcAutoClear in [
            Definitions.PACKET_CRC_AUTOCLEAR_ON,
            Definitions.PACKET_CRC_AUTOCLEAR_OFF]
            else False)

        assert (True if addressFiltering in [
            Definitions.PACKET_ADDR_FLTR_NONE,
            Definitions.PACKET_ADDR_FLTR_NODE,
            Definitions.PACKET_ADDR_FLTR_NODE_BROAD]
            else False)

        assert (True if crcType in [
            Definitions.PACKET_CRC_CCITT,
            Definitions.PACKET_CRC_IBM]
            else False)

        PacketConfig = packetFormat | dcFree | crcOn | crcAutoClear | \
            addressFiltering | crcType

        self._spi_write(Definitions.REG_30_PACKET_CONFIG1, [PacketConfig])

        print("PCKT CONF", bin(PacketConfig), "FORMAT", bin(packetFormat),
              "DC", bin(dcFree), "CRCOn", bin(crcOn), "AUTOCLEAR", bin(crcAutoClear),
              "ADDR FLTR", bin(addressFiltering), "CRCTYPE", bin(crcType))

    def setPacketConfig2(self, dataMode: int, ioHome: int,
                         beaconOn: int, payloadLength: int):
        
        assert (True if dataMode in [
            Definitions.PACKET_DATA_MODE_CONT,
            Definitions.PACKET_DATA_MODE_PACK]
            else False)

        assert (True if ioHome in [
            Definitions.PACKET_IOHOME_OFF]
            else False)

        assert (True if beaconOn in [
            Definitions.PACKET_BEACON_OFF]
            else False)

        payloadLength &= 0b11111111111
        payloadLengthLSB = payloadLength & 0xFF
        payloadLengthMSB = (payloadLength >> 8) & 0b111

        PacketConfig = dataMode | ioHome | (0b0 << 4) | beaconOn | payloadLengthMSB
        self._spi_write(Definitions.REG_31_PACKET_CONFIG2, [PacketConfig])
        self._spi_write(Definitions.REG_32_PAYLOAD_LENGHT, [payloadLengthLSB])

        print("PCKT CFG", bin(PacketConfig), "DATA MODE", bin(dataMode),
              "IOHOME", bin(ioHome), "BEACON", bin(beaconOn),
              "PLD LEN", bin(payloadLengthMSB))

        print("PLD LEN", bin(payloadLengthLSB))

    def setFifoTresh(self, txStartCond: int, fifoThreshold: int):
        assert (True if txStartCond in [
            Definitions.START_COND_FIFO_LEVEL,
            Definitions.START_COND_FIFO_EMPTY]
            else False)

        fifoThreshold &= 0b111111
        FifoTresh = txStartCond | fifoThreshold

        # print("FIFO THRESH", bin(FifoTresh))
        self._spi_write(Definitions.REG_35_FIFO_THRESH, [FifoTresh])

    def setPaConfig(self, paSelect: int, maxPower: int, outputPower: int):
        assert (True if paSelect in [
            Definitions.PA_SELECT_RFO,
            Definitions.PA_SELECT_BOOST]
            else False)

        maxPower &= 0b111
        outputPower &= 0b1111

        paConfig = paSelect | maxPower << 4 | outputPower
        self._spi_write(Definitions.REG_09_PA_CONFIG, [paConfig])
        # print("PACONFIG", bin(paConfig), "SELECT", bin(paSelect), "POWER", bin(maxPower), "OUT", bin(outputPower))

    def setRxBw(self, rxBwMant: int, rxBwExp: int):
        assert (True if rxBwMant in [
            0b00 << 3,
            0b01 << 3,
            0b10 << 3]
            else False)
        rxBwExp &= 0b111

        rxBw = self._spi_read(Definitions.REG_12_RXBW)
        rxBw &= 0b11100000  # Keep reserved bits

        rxBw |= rxBwMant | rxBwExp
        print("RXBW", hex(Definitions.REG_12_RXBW), bin(rxBw))
        self._spi_write(Definitions.REG_12_RXBW, [rxBw])

    def setRxConfig(self, restartCollision: int, restartNoPll: int,
                    restartWithPll: int, afcAutoOn: int, agcAutoOn: int, 
                    rxTrigger: int):
        
        assert (True if restartCollision in [
                0b0, 
                0b10000000]
                else False)

        assert (True if restartNoPll in [
                0b0,
                0b01000000]
                else False)

        assert (True if restartWithPll in [
                0b0,
                0b00100000]
                else False)

        assert (True if afcAutoOn in [
                0b0,
                0b00010000]
                else False)

        assert (True if agcAutoOn in [
                0b0,
                0b00001000]
                else False)

        assert (True if rxTrigger in [
                0b000,
                0b001,
                0b110,
                0b111]
                else False)

        rxConfig = restartCollision | restartNoPll | restartWithPll | afcAutoOn | agcAutoOn | rxTrigger
        print("RXCONFIG", hex(Definitions.REG_0D_RXCONFIG), bin(rxConfig))
        self._spi_write(Definitions.REG_0D_RXCONFIG, [rxConfig])
        time.sleep(0.5)
        print(bin(self._spi_read(Definitions.REG_0D_RXCONFIG)))

    def setPreambleDetector(self, preambleDetectorOn: int, preambleDetectorSize: int, 
                            preambleDetectorTol: int):
        assert (True if preambleDetectorOn in [
            0b0 << 7,
            0b1 << 7]
            else False)
        assert (True if preambleDetectorSize in [
            0b00 << 5,
            0b01 << 5,
            0b10 << 5]
            else False)
        preambleDetectorTol &= 0b11111

        preambleDetector = preambleDetectorOn | preambleDetectorSize |\
            preambleDetectorTol

        print("PREAMBLE DET", hex(Definitions.REG_1F_PREAMBLEDETECTOR), preambleDetector)

        self._spi_write(Definitions.REG_1F_PREAMBLEDETECTOR, [preambleDetector])

    def setOpMode(self, opMode: int):
        assert (True if opMode in [
            Definitions.MODE_SLEEP,
            Definitions.MODE_STDBY,
            Definitions.MODE_FSTX,
            Definitions.MODE_TX,
            Definitions.MODE_FSRX,
            Definitions.MODE_RX]
            else False)

        currentOpMode = self._spi_read(Definitions.REG_01_OP_MODE)
        currentOpMode &= 0b11111000  # Reset mode bits to 0
        currentOpMode |= opMode  # Set mode bits

        print("SET OP MODE", bin(currentOpMode))

        self._spi_write(Definitions.REG_01_OP_MODE, [currentOpMode])

    def on_recv(self, payload):
        # This should be overridden by the user
        self.receive_success = True
        self.last_payload = payload

    def sleep(self):
        if self._mode != Definitions.MODE_SLEEP:
            self.setOpMode(Definitions.MODE_SLEEP)
            self._mode = Definitions.MODE_SLEEP

    def set_mode_tx(self):
        if self._mode != Definitions.MODE_TX:
            self.setOpMode(Definitions.MODE_TX)
            while not self.dioModeReady.is_pressed:
                pass
            self._mode = Definitions.MODE_TX

            self.dioTRxState.when_pressed = self._txDone
            self.dioFifoEmpty.when_released = None
            self.dioFifoEmpty.when_pressed = None
            self.dioFifoThresh.when_pressed = None
            self.dioFifoFull.when_pressed = None
            
            

# PRECISO DESTA

    def set_mode_rx(self):
        print("OLA")
        
        self._rx_state = 0
        self._partial_data = []
        
        # lets clear flags before going to rx
        self._spi_write(Definitions.REG_3F_IRQ_FLAGS2, 0b1<<4)
        
        if self._mode != Definitions.MODE_RX:
            print("ENTREI")
            self.dioFifoEmpty.when_released = self._rxStart
            self.dioFifoEmpty.when_pressed = self._rxError
            self.dioFifoThresh.when_pressed = self._rxFifoLevel            
            self.dioTRxState.when_pressed = self._rxEnd
            self.dioFifoFull.when_pressed = self._debugStuff

            self.dioFifoThresh.when_released = None
            
            self.setOpMode(Definitions.MODE_FSRX)
            while not self.dioModeReady.is_pressed:
                pass
            print("FSRX")
            self.setOpMode(Definitions.MODE_RX)
            self._mode = Definitions.MODE_RX
            self.reset_lna_gain()   # the idea is to reset the gain to force it to be at max gain when waiting for a new message
        
        print("Done set_mode_rx")

    def wait_packet_sent(self):
        # wait for `_handle_interrupt` to switch the mode back
        start = time.time()
        while time.time() - start < self.wait_packet_sent_timeout:
            if self._mode != Definitions.MODE_TX:
                return True

        return False

    def set_mode_idle(self):
        if self._mode != Definitions.MODE_STDBY:
            self.setOpMode(Definitions.MODE_STDBY)
            while not self.dioModeReady.is_pressed:
                pass
            self._mode = Definitions.MODE_STDBY
            self.dioFifoEmpty.when_released = None
            self.dioFifoEmpty.when_pressed = None
            self.dioFifoThresh.when_pressed = None
            self.dioTRxState.when_pressed = None
            self.dioFifoFull.when_pressed = None
            
# PRECISO DESTA

    def send(self, data, header_to=None, header_id=0, header_flags=0):
        print("CONA TX")
        self.wait_packet_sent()
        #self.set_mode_idle()
        self.set_mode_tx()

        print("CONA TX 2")

        if isinstance(data, int):
            data = [data]
        elif isinstance(data, bytes):
            data = [p for p in data]
        elif isinstance(data, str):
            data = [ord(s) for s in data]

        packLength = len(data)
        print("LEN", packLength)    
        self._tx_payload = [packLength] + data

        while not self.dioFifoFull.is_pressed and len(self._tx_payload) != 0:
            self._spi_write(Definitions.REG_00_FIFO, self._tx_payload[0])
            self._tx_payload = self._tx_payload[1:]

        #time.sleep(2)

        if packLength > 63:
            self.dioFifoThresh.when_released = self._txFifoLevel

        return True

    def _spi_write(self, register, payload):
        if isinstance(payload, int):
            payload = [payload]
        elif isinstance(payload, bytes):
            payload = [p for p in payload]
        elif isinstance(payload, str):
            payload = [ord(s) for s in payload]

        self.spi.xfer([register | 0x80] + payload)

    def _spi_read(self, register, length=1):
        if length == 1:
            return self.spi.xfer([register] + [0] * length)[1]
        else:
            return self.spi.xfer([register] + [0] * length)[1:]

    def _decrypt(self, message):
        decrypted_msg = self.crypto.decrypt(message)
        msg_length = decrypted_msg[0]
        return decrypted_msg[1: msg_length + 1]

    def _encrypt(self, message):
        msg_length = len(message)
        padding = bytes(
            ((math.ceil((msg_length + 1) / 16) * 16) - (msg_length + 1)) * [0]
        )
        msg_bytes = bytes([msg_length]) + message + padding
        encrypted_msg = self.crypto.encrypt(msg_bytes)
        return encrypted_msg

    def _rxStart(self):
        print("_RXSTART")
        print(bin((self._spi_read(Definitions.REG_0C_LNACONFIG) & 0b1110_0000)>>5))
        self.data_rssi = -1*int(self._spi_read(0x11)/2)
        print(self.data_rssi)
        # printState()
        if self._rx_state == 0:
            print("START")
            self._rx_state = 1
        else:
            print("ELSE")

    def _rxError(self):
        print("_RXERROR")
        
        # print register flags
        print("IRQ FLAGS", bin(self._spi_read(Definitions.REG_3F_IRQ_FLAGS2)))
        
        if self._rx_state == 1:
            print("  CRC ERROR")
            self._rx_state = -1
            self._partial_data = []
        elif self._rx_state == 2:
            print("  ENDED")
            self._rx_state = 0
            print(self._last_payload)
        else:
            print("RXSTATE", self._rx_state)
            print("ELSE")
            
    def _debugStuff(self):
        print("\nFIFO FULL \n")
        print("  IRQ FLAGS", bin(self._spi_read(Definitions.REG_3F_IRQ_FLAGS2)))
        print(" OUT FIFO FULL")

    def _rxFifoLevel(self):
        # available = self._spi_read(Definitions.REG_00_FIFO)
        # print("APP - out", available)
        
        # set threshold to 5 to maximize how many bytes are being read
        # but still leave some bytes to not empty the fifo
        self.setFifoTresh(Definitions.START_COND_FIFO_EMPTY, 5)

        # # printState()
        counter = 0
        while self.dioFifoThresh.is_pressed:
        # while not self.dioFifoEmpty.is_pressed:
            available = self._spi_read(Definitions.REG_00_FIFO)
            self._partial_data.append(available)
            counter += 1
            
            # # if fifo thresh is low, lets try and wait 2 byte time to see if more data comes in
            # if not self.dioFifoThresh.is_pressed:
            #     time.sleep(0.0008)
            
        # print(self.dioFifoThresh.is_pressed)
        
        # set threshold to 40 to maximize how many bytes are available to read next time
        self.setFifoTresh(Definitions.START_COND_FIFO_EMPTY, 30)
        
    def reset_lna_gain(self):
        lna_gain = self._spi_read(Definitions.REG_0C_LNACONFIG)
        lna_gain &= 0b00011111
        lna_gain |= 0b00100000
        self._spi_write(Definitions.REG_0C_LNACONFIG, lna_gain)
        time.sleep(0.3)
        print(bin((self._spi_read(Definitions.REG_0C_LNACONFIG) & 0b1110_0000)>>5))
        

    def _rxEnd(self):
        print("_RXEND")
        # printState()
        while not self.dioFifoEmpty.is_pressed:
            available = self._spi_read(Definitions.REG_00_FIFO)
            self._partial_data.append(available)
        print("  out of while")
        self._rx_state = 2
        self.noise_rssi = -1*int(self._spi_read(0x11)/2)
        self._last_payload = namedtuple(
                    "Payload",
                    [
                        "message",
                        "rssi",
                        "snr",
                    ],
               )(bytes(self._partial_data[1:]), self.data_rssi, self.data_rssi-self.noise_rssi)
        self.on_recv(self._last_payload)
        self._partial_data = []

    def _txDone(self):
        print("TX DONE")
        self.set_mode_rx()

    def _txFifoLevel(self):
        print("TX FIFO LEVEL")
        while len(self._tx_payload) != 0 and not self.dioFifoFull.is_pressed:
            self._spi_write(Definitions.REG_00_FIFO, self._tx_payload[0])
            self._tx_payload = self._tx_payload[1:]

    def _handle_interrupt(self, channel):
        irq_flags = self._spi_read(Definitions.REG_12_IRQ_FLAGS)

        if (
            self._mode == Definitions.MODE_RXCONTINUOUS
            and (irq_flags & Definitions.RX_DONE)
            and (self.crc_error() == 0)
        ):
            packet_len = self._spi_read(Definitions.REG_13_RX_NB_BYTES)
            self._spi_write(
                Definitions.REG_0D_FIFO_ADDR_PTR,
                self._spi_read(Definitions.REG_10_FIFO_RX_CURRENT_ADDR),
            )

            packet = self._spi_read(Definitions.REG_00_FIFO, packet_len)
            self._spi_write(Definitions.REG_12_IRQ_FLAGS, 0xFF)  # Clear all IRQ flags

            snr = self._spi_read(Definitions.REG_19_PKT_SNR_VALUE) / 4
            rssi = self._spi_read(Definitions.REG_1A_PKT_RSSI_VALUE)

            if snr < 0:
                rssi = snr + rssi
            else:
                rssi = rssi * 16 / 15

            if self._freq >= 779:
                rssi = round(rssi - 157, 2)
            else:
                rssi = round(rssi - 164, 2)

            if packet_len > 0:
                message = bytes(packet)

                if self.crypto and len(message) % 16 == 0:
                    message = self._decrypt(message)

                self.set_mode_rx()

                self._last_payload = namedtuple(
                    "Payload",
                    [
                        "message",
                        "rssi",
                        "snr",
                    ],
                )(message, rssi, snr)

                self.on_recv(self._last_payload)

        elif self._mode == Definitions.MODE_TX and (irq_flags & Definitions.TX_DONE):
            self.set_mode_idle()

        elif self._mode == Definitions.MODE_CAD and (irq_flags & Definitions.CAD_DONE):
            self._cad = irq_flags & Definitions.CAD_DETECTED
            self.set_mode_idle()

        self._spi_write(Definitions.REG_12_IRQ_FLAGS, 0xFF)

    @property
    def enable_crc(self):
        """Set to True to enable hardware CRC checking of incoming packets.
        Incoming packets that fail the CRC check are not processed.  Set to
        False to disable CRC checking and process all incoming packets.
        Taken from PyCubed Repo by Max Holliday"""
        return (self._spi_read(Definitions.REG_1E_MODEM_CONFIG2) & 0x04) == 0x04

    @enable_crc.setter
    def enable_crc(self, val):
        # Optionally enable CRC checking on incoming packets.
        # Taken from PyCubed Repo by Max Holliday
        if val:
            self._spi_write(
                Definitions.REG_1E_MODEM_CONFIG2,
                self._spi_read(Definitions.REG_1E_MODEM_CONFIG2) | 0x04,
            )
        else:
            self._spi_write(
                Definitions.REG_1E_MODEM_CONFIG2,
                self._spi_read(Definitions.REG_1E_MODEM_CONFIG2) & 0xFB,
            )

    def crc_error(self):
        """crc status. Taken from PyCubed Repo by Max Holliday"""
        error = (self._spi_read(Definitions.REG_12_IRQ_FLAGS) & 0x20) >> 5

        if error == 1:
            print("CRC Error!")
            self.crc_error_count += 1
        return error

    def close(self):
        # GPIO.cleanup()
        self.spi.close()
