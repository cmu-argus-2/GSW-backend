# Message ID database for communication protocol
class MSG_ID:
    """
    Comms message IDs that are downlinked during the mission
    """

    # Source header ID for Argus - THIS MUST BE UNIQUE FOR EACH SPACECRAFT
    ARGUS_1_ID = 0x01
    ARGUS_2_ID = 0x02

    # Source header ID for GS
    GS_ID = 0x04

    # SAT heartbeat, nominally downlinked in orbit
    SAT_HEARTBEAT = 0x01

    # SAT TM frames, requested by GS
    SAT_TM_NOMINAL = 0x05 # A requested nominal frame
    SAT_TM_HAL     = 0x02
    SAT_TM_STORAGE = 0x03
    SAT_TM_PAYLOAD = 0x04

    TM_FRAME_TYPES = [SAT_TM_NOMINAL, SAT_TM_HAL, SAT_TM_STORAGE, SAT_TM_PAYLOAD, SAT_HEARTBEAT]

    # SAT ACK, in response to GS commands
    SAT_ACK = 0x0F

    # SAT file metadata and file content messages
    SAT_FILE_METADATA = 0x10
    SAT_FILE_PKT = 0x20

    # SAT downlinking all data in its system 
    DOWNLINK_ALL_FILES = 0x50 # TODO: check number 

    """
    GS commands to be uplinked to Argus
    """

    # GS commands SC responds to with an ACK
    GS_CMD_FORCE_REBOOT = 0x40
    GS_CMD_SWITCH_TO_STATE = 0x41
    GS_CMD_UPLINK_TIME_REFERENCE = 0x42
    GS_CMD_UPLINK_ORBIT_REFERENCE = 0x43
    GS_CMD_TURN_OFF_PAYLOAD = 0x44
    GS_CMD_SCHEDULE_OD_EXPERIMENT = 0x45
    # GS commands SC responds with downlinking everything
    GS_CMD_DOWNLINK_ALL_FILES = 0x50 #TODO check what this is 

    # GS commands SC responds to with a frame
    GS_CMD_REQUEST_TM_NOMINAL = 0x46
    GS_CMD_REQUEST_TM_HAL = 0x47
    GS_CMD_REQUEST_TM_STORAGE = 0x48
    GS_CMD_REQUEST_TM_PAYLOAD = 0x49

    # GS commands SC responds to with file MD or packets
    GS_CMD_FILE_METADATA = 0x4A
    GS_CMD_FILE_PKT = 0x4B

    VALID_RX_MSG_IDS = [
        SAT_HEARTBEAT, 
        SAT_TM_NOMINAL, 
        SAT_TM_HAL, 
        SAT_TM_STORAGE, 
        SAT_TM_PAYLOAD, 
        SAT_ACK, 
        SAT_FILE_METADATA, 
        SAT_FILE_PKT,
        DOWNLINK_ALL_FILES
    ]

    VALID_TX_MSG_IDS = [
        GS_CMD_FORCE_REBOOT,
        GS_CMD_SWITCH_TO_STATE,
        GS_CMD_UPLINK_TIME_REFERENCE,
        GS_CMD_TURN_OFF_PAYLOAD,
        GS_CMD_SCHEDULE_OD_EXPERIMENT,
        GS_CMD_DOWNLINK_ALL_FILES,
        GS_CMD_REQUEST_TM_NOMINAL,
        GS_CMD_REQUEST_TM_HAL,
        GS_CMD_REQUEST_TM_STORAGE,
        GS_CMD_REQUEST_TM_PAYLOAD,
        GS_CMD_FILE_METADATA,
        GS_CMD_FILE_PKT, 
        GS_CMD_DOWNLINK_ALL_FILES
    ]
