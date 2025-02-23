# Extract the arguments and return the payload
from gs_constants import MSG_ID

from lib.telemetry.helpers import *

MSG_LENGTHS = {
    MSG_ID.GS_CMD_SWITCH_TO_STATE: 5,
    MSG_ID.GS_CMD_UPLINK_TIME_REFERENCE: 4,
    MSG_ID.GS_CMD_UPLINK_ORBIT_REFERENCE: 28,
    MSG_ID.GS_CMD_FILE_METADATA: 5,
    MSG_ID.GS_CMD_FILE_PKT: 7,
}


class CommandPacker:
    def pack_SWITCH_TO_STATE(self, rq_cmd):
        """
        This will back the command arguments for switch to state
        """
        cmd_args = rq_cmd["args"]

        metadata = (
            MSG_ID.GS_CMD_SWITCH_TO_STATE.to_bytes(1, "big")
            + (0).to_bytes(2, "big")  # message id
            + MSG_LENGTHS[MSG_ID.GS_CMD_SWITCH_TO_STATE].to_bytes(  # sequence count
                1, "big"
            )  # packet length
        )

        time_in_state = pack_unsigned_long_int(cmd_args, "time_in_state")

        return metadata + cmd_args["target_state_id"].to_bytes(1, "big") + time_in_state

    def pack_UPLINK_TIME_REFERENCE(self, rq_cmd):
        """
        This will pack the command arguments for uplink time reference
        """
        cmd_args = rq_cmd["args"]

        metadata = (
            MSG_ID.GS_CMD_UPLINK_TIME_REFERENCE.to_bytes(1, "big")
            + (0).to_bytes(2, "big")  # message id
            + MSG_LENGTHS[  # sequence count
                MSG_ID.GS_CMD_UPLINK_TIME_REFERENCE
            ].to_bytes(
                1, "big"
            )  # packet length
        )

        time_reference = pack_unsigned_long_int(cmd_args, "time_reference")

        return metadata + time_reference

    def pack_UPLINK_ORBIT_REFERENCE(self, rq_cmd):
        """
        This will pack the command arguments for uplink orbit reference
        """
        cmd_args = rq_cmd["args"]

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

    def pack_REQUEST_FILE_METADATA(self, rq_cmd):
        cmd_args = rq_cmd["args"]

        metadata = (
            MSG_ID.GS_CMD_FILE_METADATA.to_bytes(1, "big")
            + (0).to_bytes(2, "big")  # message id
            + MSG_LENGTHS[MSG_ID.GS_CMD_FILE_METADATA].to_bytes(  # sequence count
                1, "big"
            )  # packet length
        )

        file_time = pack_unsigned_long_int(cmd_args, "file_time")

        return metadata + cmd_args["file_id"].to_bytes(1, "big") + file_time

    def pack_REQUEST_FILE_PKT(self, rq_cmd):
        cmd_args = rq_cmd["args"]

        file_time = pack_unsigned_long_int(cmd_args, "file_time")
        rq_sq_cnt = pack_unsigned_short_int(cmd_args, "request_sequence_count")

        metadata = (
            MSG_ID.GS_CMD_FILE_PKT.to_bytes(1, "big")
            + rq_sq_cnt  # message id
            + MSG_LENGTHS[MSG_ID.GS_CMD_FILE_PKT].to_bytes(  # sequence count
                1, "big"
            )  # packet length
        )

        return metadata + cmd_args["file_id"].to_bytes(1, "big") + file_time

    def pack(self, rq_cmd):
        """
        This will pack and return the tx_message

        usage in groundstation.py

        import CommandPacker
        tx_message = CommandPacker.pack(rq_cmd)
        self.radiohead.send_message(tx_message, 255, 1)
        """

        # pack source and destination headers
        src_dst_header = bytes([MSG_ID.GS_ID, MSG_ID.ARGUS_1_ID])

        # pack the metadata + payload
        md_payload = ()

        if self.rq_cmd["id"] == MSG_ID.GS_CMD_SWITCH_TO_STATE:
            md_payload = self.pack_SWITCH_TO_STATE(rq_cmd)

        elif self.rq_cmd["id"] == MSG_ID.GS_CMD_UPLINK_TIME_REFERENCE:
            md_payload = self.pack_UPLINK_TIME_REFERENCE(rq_cmd)

        elif self.rq_cmd["id"] == MSG_ID.GS_CMD_UPLINK_ORBIT_REFERENCE:
            md_payload = self.pack_UPLINK_ORBIT_REFERENCE(rq_cmd)

        elif self.rq_cmd["id"] == MSG_ID.GS_CMD_FILE_METADATA:
            md_payload = self.pack_REQUEST_FILE_METADATA(rq_cmd)

        elif self.rq_cmd["id"] == MSG_ID.GS_CMD_FILE_PKT:
            md_payload = self.pack_REQUEST_FILE_PKT(rq_cmd)

        else:
            md_payload = (
                self.rq_cmd["id"].to_bytes(1, "big")
                + (0).to_bytes(2, "big")
                + (0).to_bytes(2, "big")
                + bytearray()
            )

        return src_dst_header + md_payload
