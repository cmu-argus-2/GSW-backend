import time

# Extract the arguments and return the payload
from lib.gs_constants import MSG_ID
from lib.telemetry.unpacking import RECEIVE
from lib.telemetry.helpers import *

MSG_LENGTHS = {
    MSG_ID.GS_CMD_SWITCH_TO_STATE: 5,
    MSG_ID.GS_CMD_UPLINK_TIME_REFERENCE: 4,
    MSG_ID.GS_CMD_UPLINK_ORBIT_REFERENCE: 28,
    MSG_ID.GS_CMD_FILE_METADATA: 5,
    MSG_ID.GS_CMD_FILE_PKT: 7,
}


class TRANSMIT:
    # RQ message parameters for commanding SC
    # Request command
    rq_cmd = {"id": 0x01, "args": {}}
    rq_sq = 0  # sequence command - matters for file
    rq_len = 0  # error checking
    tx_message = []

    # Destination ID for GS TX
    tx_dst_id = 0x00

    # TODO: fix comments
    @classmethod
    def pack_SWITCH_TO_STATE(self):
        """
        This will back the command arguments for switch to state
        """
        cmd_args = self.rq_cmd["args"]

        metadata = (
            MSG_ID.GS_CMD_SWITCH_TO_STATE.to_bytes(1, "big") # message id
            + (0).to_bytes(2, "big")  # sequence count
            + MSG_LENGTHS[MSG_ID.GS_CMD_SWITCH_TO_STATE].to_bytes(  
                1, "big"
            )  # packet length
        )

        time_in_state = pack_unsigned_long_int(cmd_args, "time_in_state")

        return metadata + cmd_args["target_state_id"].to_bytes(1, "big") + time_in_state

    @classmethod
    def pack_UPLINK_TIME_REFERENCE(self):
        """
        This will pack the command arguments for uplink time reference
        """
        cmd_args = self.rq_cmd["args"]

        metadata = (
            MSG_ID.GS_CMD_UPLINK_TIME_REFERENCE.to_bytes(1, "big") # message id
            + (0).to_bytes(2, "big")  # sequence count
            + MSG_LENGTHS[
                MSG_ID.GS_CMD_UPLINK_TIME_REFERENCE
            ].to_bytes(
                1, "big"
            )  # packet length
        )

        # Instead of passing the parameter, calculate time.time() right before TX
        time_reference = pack_unsigned_long_int([int(time.time())], 0)

        return metadata + time_reference

    @classmethod
    def pack_UPLINK_ORBIT_REFERENCE(self):
        """
        This will pack the command arguments for uplink orbit reference
        """
        cmd_args = self.rq_cmd["args"]

        metadata = (
            MSG_ID.GS_CMD_UPLINK_ORBIT_REFERENCE.to_bytes(1, "big")
            + (0).to_bytes(2, "big")  # message id
            + MSG_LENGTHS[  # sequence count
                MSG_ID.GS_CMD_UPLINK_ORBIT_REFERENCE
            ].to_bytes(
                1, "big"
            )  # packet length
        )

        time_reference = pack_unsigned_long_int(cmd_args, "time_reference")
        pos_x = pack_signed_long_int(cmd_args, "position_x")
        pos_y = pack_signed_long_int(cmd_args, "position_y")
        pos_z = pack_signed_long_int(cmd_args, "position_z")
        vel_x = pack_signed_long_int(cmd_args, "velocity_x")
        vel_y = pack_signed_long_int(cmd_args, "velocity_y")
        vel_z = pack_signed_long_int(cmd_args, "velocity_z")

        return metadata + time_reference + pos_x + pos_y + pos_z + vel_x + vel_y + vel_z

    @classmethod
    def pack_REQUEST_FILE_METADATA(self):
        cmd_args = self.rq_cmd["args"]

        metadata = (
            MSG_ID.GS_CMD_FILE_METADATA.to_bytes(1, "big") # message id
            + (0).to_bytes(2, "big")  # sequence count
            + MSG_LENGTHS[MSG_ID.GS_CMD_FILE_METADATA].to_bytes( 
                1, "big"
            )  # packet length
        )

        file_time = pack_unsigned_long_int(cmd_args, "file_time")

        return metadata + cmd_args["file_id"].to_bytes(1, "big") + file_time

    @classmethod
    def pack_REQUEST_FILE_PKT(self):
        cmd_args = self.rq_cmd["args"]

        file_time = pack_unsigned_long_int([RECEIVE.file_time], 0)
        rq_sq_cnt = pack_unsigned_short_int([RECEIVE.gs_msg_sq], 0)

        metadata = (
            MSG_ID.GS_CMD_FILE_PKT.to_bytes(1, "big")
            + rq_sq_cnt  # message id
            + MSG_LENGTHS[MSG_ID.GS_CMD_FILE_PKT].to_bytes(  # sequence count
                1, "big"
            )  # packet length
        )

        return metadata + cmd_args["file_id"].to_bytes(1, "big") + file_time + rq_sq_cnt

    @classmethod
    def pack_DOWNLINK_ALL_FILES(self):
        cmd_args = self.rq_cmd["args"]

        # DOWNLINK_ALL_FILES has the same structure as REQUEST_FILE_METADATA
        metadata = (
            MSG_ID.GS_CMD_DOWNLINK_ALL_FILES.to_bytes(1, "big") # message id
            + (0).to_bytes(2, "big")  # sequence count
            + MSG_LENGTHS[MSG_ID.GS_CMD_FILE_METADATA].to_bytes( 
                1, "big"
            )  # packet length
        )

        file_time = pack_unsigned_long_int(cmd_args, "file_time")

        return metadata + cmd_args["file_id"].to_bytes(1, "big") + file_time
    
    @classmethod
    def pack(self):
        """
        This will pack and return the tx_message
        """
        # Source and destination IDs for the message
        src_dst_header = bytes([MSG_ID.GS_ID, self.tx_dst_id])

        # pack the metadata + payload
        md_payload = ()

        if self.rq_cmd["id"] == MSG_ID.GS_CMD_SWITCH_TO_STATE:
            # payload = target_state_id (uint8) + time_in_state (uint32)
            md_payload = self.pack_SWITCH_TO_STATE()
            print("Successfully packed GS_CMD_SWITCH_TO_STATE")

        elif self.rq_cmd["id"] == MSG_ID.GS_CMD_UPLINK_TIME_REFERENCE:
            # payload = time_reference (uint32)
            md_payload = self.pack_UPLINK_TIME_REFERENCE()
            print("Successfully packed GS_CMD_UPLINK_TIME_REFERENCE")

        elif self.rq_cmd["id"] == MSG_ID.GS_CMD_UPLINK_ORBIT_REFERENCE:
            # payload = time_reference (uint32) + pos_x (int32) + pos_y (int32) + pos_z (int32)
            # + vel_x (int32) + vel_y (int32) + vel_z (int32)
            md_payload = self.pack_UPLINK_ORBIT_REFERENCE()
            print("Successfully packed GS_CMD_UPLINK_ORBIT_REFERENCE")

        elif self.rq_cmd["id"] == MSG_ID.GS_CMD_FILE_METADATA:
            # payload = file_id (uint8) + file_time (uint32)
            md_payload = self.pack_REQUEST_FILE_METADATA()
            print("Successfully packed GS_CMD_FILE_METADATA")

        elif self.rq_cmd["id"] == MSG_ID.GS_CMD_FILE_PKT:
            # payload = file_id (uint8) + file_time (uint32) + rq_sq_cnt (uint16)
            md_payload = self.pack_REQUEST_FILE_PKT()
            print("Successfully packed GS_CMD_FILE_PKT")

        elif self.rq_cmd["id"] == MSG_ID.GS_CMD_DOWNLINK_ALL_FILES:
            # payload = file_id (uint8) + file_time (uint32)
            md_payload = self.pack_DOWNLINK_ALL_FILES()
            print("Successfully packed GS_CMD_DOWNLINK_ALL_FILES")

        else:
            # For all other commands that do not have arguments, just pack the command id
            md_payload = (
                self.rq_cmd["id"].to_bytes(1, "big")
                + (0).to_bytes(2, "big")
                + (0).to_bytes(1, "big")
                + bytearray()
            )
            print("Successfully packed ", self.rq_cmd)

        self.tx_message = src_dst_header + md_payload
