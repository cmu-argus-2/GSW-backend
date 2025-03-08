import datetime
import time
import lib.config as config
from collections import deque

from lib.telemetry.unpacking import TelemetryUnpacker
from lib.gs_constants import MSG_ID
 

class TRANSMITTED: 
 # ----------------------- Transmitted Information ----------------------- #
    
    def transmit_SwitchToState(self):
        # Set RQ message parameters to force a state change on SC
        rq_cmd = MSG_ID.GS_CMD_SWITCH_TO_STATE
        rq_sq = 0
        rq_len = 5

        # Temporary hardcoding for GS_CMD_SWITCH_TO_STATE
        payload = (0x01).to_bytes(1, "big") + (20).to_bytes(4, "big")
        print("Transmitting CMD: GS_CMD_SWITCH_TO_STATE")
        return rq_cmd, rq_sq, rq_len, payload

    
    def transmit_ForceReboot(self):
        # Set RQ message parameters
        rq_cmd = MSG_ID.GS_CMD_FORCE_REBOOT
        rq_sq = 0
        rq_len = 0

        # No payload for this command
        payload = bytearray()
        print("Transmitting CMD: GS_CMD_FORCE_REBOOT")
        return rq_cmd, rq_sq, rq_len, payload

    
    def transmit_Metadata(self, file_id, file_time):
        # Set RQ message parameters for MD request
        rq_cmd = MSG_ID.GS_CMD_FILE_METADATA
        rq_sq = 0
        rq_len = 5

        # Request specific file ID and time of creation
        payload = file_id.to_bytes(1, "big") + file_time.to_bytes(
            4, "big"
        )
        print("Transmitting CMD: GS_CMD_FILE_METADATA")
        return rq_cmd, rq_sq, rq_len, payload

    
    def transmit_Filepkt(self, gs_msg_sq, file_id, file_time, rq_sq):
        # Set RQ message parameters for PKT
        rq_cmd = MSG_ID.GS_CMD_FILE_PKT
        rq_sq = gs_msg_sq
        rq_len = 7

        # Request specific file ID and time of creation
        payload = (
            file_id.to_bytes(1, "big")
            + file_time.to_bytes(4, "big")
            + rq_sq.to_bytes(2, "big")
        )
        print("Transmitting CMD: GS_CMD_FILE_PKT")
        
        return rq_cmd, rq_sq, rq_len, payload

    
    def transmit_uplink_time_reference(self):
        # Set RQ message parameters for PKT
        rq_cmd = MSG_ID.GS_CMD_UPLINK_TIME_REFERENCE
        rq_sq = 0
        rq_len = 4

        # Temporary hardcoding for GS_CMD_UPLINK_TIME_REFERENCE
        payload = (1739727422).to_bytes(4, "big") #time reference param
        
        print("Transmitting CMD: GS_CMD_UPLINK_TIME_REFERENCE")
        return rq_cmd, rq_sq, rq_len, payload
    
    
    def transmit_uplink_orbit_reference(self):
        # Set RQ message parameters for PKT
        rq_cmd = MSG_ID.GS_CMD_UPLINK_ORBIT_REFERENCE
        rq_sq = 0
        rq_len = 28

        # Temporary hardcoding for GS_CMD_UPLINK_ORBIT_REFERENCE
        payload = (
            (1739727422).to_bytes(4, "big") + #time reference
            (0).to_bytes(4, "big") + #position
            (1).to_bytes(4, "big") +
            (2).to_bytes(4, "big") +
            (0).to_bytes(4, "big") + #velocity
            (1).to_bytes(4, "big") +
            (2).to_bytes(4, "big")
        )
        
        print("Transmitting CMD: GS_CMD_UPLINK_ORBIT_REFERENCE")
        return rq_cmd, rq_sq, rq_len, payload

