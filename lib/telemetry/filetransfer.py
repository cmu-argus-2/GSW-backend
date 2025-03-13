from lib.gs_constants import MSG_ID
from lib.telemetry.constants import file_tags_str
from lib.telemetry.unpacking import RECEIVE
import time

import lib.config as config

if config.MODE == "DB":
    from lib.database.db_command_queue import get_latest_command, remove_latest_command, commands_available
elif config.MODE == "DBG":
    from lib.database.debug_queue import get_latest_command, remove_latest_command, commands_available



class FILETRANSFER: 
    """
    Contains code for the multi packet file transfer mechanisms
    """

    @classmethod
    def receiving_multipkt(self): 
        print (f"Received PKT {RECEIVE.rx_msg_sq} out of {RECEIVE.file_target_sq - 1}")

        if RECEIVE.gs_msg_sq != RECEIVE.rx_msg_sq: 
            print ("ERROR: Sequence count mismatch")
        else: 
            RECEIVE.file_array.append(RECEIVE.rx_message[9 : RECEIVE.rx_msg_size + 9])
            RECEIVE.gs_msg_sq += 1
        
        if RECEIVE.gs_msg_sq == RECEIVE.file_target_sq: 
            # Filename and extension based on file type
            if RECEIVE.file_id == 0x0A:
                RECEIVE.filename = str(file_tags_str[RECEIVE.file_id]) + "_" + str(RECEIVE.file_time) + ".jpg"
            else:
                RECEIVE.filename = str(file_tags_str[RECEIVE.file_id]) + "_" + str(RECEIVE.file_time) + ".bin"

            write_bytes = open(RECEIVE.filename, "wb")

            for i in range(RECEIVE.file_target_sq):
                write_bytes.write(RECEIVE.file_array[i])
            
            write_bytes.close()

            RECEIVE.flag_rq_file = False

            RECEIVE.gs_msg_sq = 0
            RECEIVE.rx_msg_sq = 0
            RECEIVE.file_target_sq = 0
            RECEIVE.file_array = []

    @classmethod 
    def initiate_file_transfer_sq(self): 
        print("SAT_FILE_METADATA requested. Initiating file transfers")
            # TODO: Better error checking
        print(f"{RECEIVE.file_size}, {RECEIVE.file_target_sq}")
        if (
            RECEIVE.file_id == 0x00
            or RECEIVE.file_size == 0
            or RECEIVE.file_target_sq == 0
        ):
            # No file on satellite
            RECEIVE.flag_rq_file = False

            if commands_available() == None: 
                return {
                    "id": MSG_ID.GS_CMD_REQUEST_TM_NOMINAL,
                    "args": {},
                }
            else:
                latest = get_latest_command()
                remove_latest_command()
                return (
                    latest
                )  
        else:
            # Valid file on satellite
            RECEIVE.flag_rq_file = True
            return {"id": MSG_ID.GS_CMD_FILE_PKT, "args" : {"file_id": RECEIVE.file_id, "file_time": int(RECEIVE.file_time), "rq_sq_cnt": RECEIVE.gs_msg_sq}}
        






