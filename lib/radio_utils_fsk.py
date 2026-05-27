from lib.argus_fsk import GFSK

from lib.config import ARGUS_FREQ, GS_INTERRUPT, GS_FIFOTHRESH, \
    GS_FIFOFULL, GS_FIFOEMPTY, GS_MODEREADY


def initialize_radio() -> GFSK:
    CHANNEL = 0
    TXRX_STATE = GS_INTERRUPT    # These are the interrupt pins
    FIFO_THRESH = GS_FIFOTHRESH
    FIFO_FULL = GS_FIFOFULL
    FIFO_EMPTY = GS_FIFOEMPTY
    MODE_READY = GS_MODEREADY
    ADDRESS = 255
    FREQUENCY = ARGUS_FREQ
    TX_POWER = 23
    PACKET_TYPE = None
    WHITENING = None
    CRC_ON = None
    CRC_TYPE = None
    CRC_AUTOCLEAR = None
    RECEIVE_ALL = False
    ACKS = False
    CRYTPO = None

    # initialize radio instance
    radio = GFSK(
        CHANNEL,
        TXRX_STATE,
        FIFO_THRESH,
        FIFO_FULL,
        FIFO_EMPTY,
        MODE_READY,
        ADDRESS,
        FREQUENCY,
        TX_POWER,
        PACKET_TYPE,
        WHITENING,
        CRC_ON,
        CRC_TYPE,
        CRC_AUTOCLEAR,
        RECEIVE_ALL,
        ACKS,
        CRYTPO,
    )
    
    return radio
