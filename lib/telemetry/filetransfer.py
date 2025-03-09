from lib.gs_constants import MSG_ID
from lib.telemetry.unpacking import RECEIVE

import lib.config as config

if config.MODE == "DB":
    from lib.database.db_command_queue import get_latest_command, remove_latest_command, commands_available
    from lib.database.db_rx_data import add_downlink_data, add_File_Packet
elif config.MODE == "DBG":
    from lib.database.debug_queue import get_latest_command, remove_latest_command, commands_available



class FILETRANSFER: 
    """
    Contains code for the multi packet file transfer mechanisms
    """

    # File metadata parameters
    file_id = 0x0A  # IMG
    file_time = 1738351687
    file_size = 0x00
    file_target_sq = 0x00  # maximum sq count (240 bytes) --> error checking
    flag_rq_file = False  # testing in the lab - once the image is received
    filename = ""

    # File TX parameters
    gs_msg_sq = 0  # if file is multiple packets - number of packets received
    file_array = []


    @classmethod
    def receiving_multipkt(self): 
        if self.gs_msg_sq != RECEIVE.rx_msg_sq: 
            print ("ERROR: Sequence count mismatch")
        else: 
            self.file_array.append(RECEIVE.rx_message[9 : RECEIVE.rx_msg_size + 9])
            self.gs_msg_sq += 1
        
        if self.gs_msg_sq == self.file_target_sq: 
            # TODO: change the extension based on what we receive
            self.filename = "test_image.jpg"
            write_bytes = open(self.filename, "wb")

            for i in range(self.file_target_sq):
                write_bytes.write(self.file_array[i])
            
            write_bytes.close()

            self.flag_rq_file = False

    @classmethod 
    def initiate_file_transfer_sq(self): 
        print("SAT_FILE_METADATA requested. Initiating file transfers")
            # TODO: Better error checking
        if (
            FILETRANSFER.file_id == 0x00
            or FILETRANSFER.file_size == 0
            or FILETRANSFER.file_target_sq == 0
        ):
            # No file on satellite
            FILETRANSFER.flag_rq_file = False

            if config.MODE == "DB":
                if commands_available() == None: 
                    return {
                        "id": MSG_ID.GS_CMD_REQUEST_TM_HEARTBEAT,
                        "args": {},
                    }
                else:
                    return (
                        get_latest_command()
                    )  
        else:
            # Valid file on satellite
            self.flag_rq_file = True
            return MSG_ID.GS_CMD_FILE_PKT








