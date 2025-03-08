import RPi.GPIO as GPIO
from lib.database import db_services

from lib.radio_utils import initialize_radio
from lib.telemetry.unpacking import TelemetryUnpacker
from lib.gs_constants import MSG_ID


class RECEIVED: 
   # ------------------------ Received Information ------------------------- #
    @classmethod
    def received_Heartbeat(self, rx_message):
        # Message is a heartbeat with TM frame, unpack
        tm_data = TelemetryUnpacker.unpack_tm_frame_nominal(rx_message)
        print("**** Received HB ****")

        if (config.MODE == "DB"):
            db_services.add_Telemetry(MSG_ID.SAT_TM_NOMINAL, tm_data)
        elif (config.MODE == "DBG"):
            db_queue.enqueue(f"TEL:{rx_message}")


    @classmethod
    def received_Metadata(self):
        # Message is file metadata
        print("**** Received file metadata ****")
        print(f"META:[{GS.file_id}, {GS.file_time}, {GS.file_size}, {GS.file_target_sq}]")

        # Unpack file parameters
        GS.file_id = int.from_bytes((GS.rx_message[4:5]), byteorder="big")
        GS.file_time = int.from_bytes((GS.rx_message[5:9]), byteorder="big")
        GS.file_size = int.from_bytes((GS.rx_message[9:13]), byteorder="big")
        GS.file_target_sq = int.from_bytes((GS.rx_message[13:15]), byteorder="big")

        if (config.MODE == "DB"):
                db_services.add_File_Meta_Data([GS.file_id, GS.file_time, GS.file_size, GS.file_target_sq])
        elif (config.MODE == "DBG"):
            db_queue.enqueue(f"META:[{GS.file_id}, {GS.file_time}, {GS.file_size}, {GS.file_target_sq}]")

    @classmethod
    def received_Filepkt(self):
        # TODO: Check for file ID and file time
        # Message is file packet
        print(f"Received PKT {self.rx_msg_sq} out of {self.file_target_sq}")
        print(f"File data {self.rx_message}")
        # print(self.rx_message[9:self.rx_msg_size + 9])

        # Check internal gs_msg_sq against rx_msg_sq
        if self.gs_msg_sq != self.rx_msg_sq:
            # Sequence count mismatch
            print("ERROR: Sequence count mismatch")

        else:
            # Append packet to file_array
            self.file_array.append(self.rx_message[9 : self.rx_msg_size + 9])
            # Increment sequence counter
            self.gs_msg_sq += 1

        # Compare gs_msg_sq to file_target_sq
        if self.gs_msg_sq == self.file_target_sq:
            # Write file to memory
            self.filename = "test_image.jpg"
            write_bytes = open(self.filename, "wb")

            # Write all bytes to the file
            for i in range(self.file_target_sq):
                write_bytes.write(self.file_array[i])

            # Close file
            write_bytes.close()

            # Set flag
            self.flag_rq_file = False

        # Transition based on flag
        if self.flag_rq_file is True:
            print("**** Received PKT. RX --> TX ****")
            self.state = GS_COMMS_STATE.TX
        else:
            print("**** Received all packets. RX --> DB_RW ****")

            if (config.MODE == "DB"):
                 db_services.add_File_Packet(self.file_array, self.file_id, self.filename)
            elif (config.MODE == "DBG"):
                db_queue.enqueue(f"PKT:{self.file_array},{self.file_id}, {self.filename}")
        
 
            self.state = GS_COMMS_STATE.DB_RW
            self.database_readwrite()

    @classmethod
    def received_Ack(self):
        print(f"**** Received an ACK {self.rx_message} ****")

        if (config.MODE == "DB"):
            db_services.add_Ack()
        elif (config.MODE == "DBG"):
            db_queue.enqueue(f"ACK:{self.rx_message}")

        self.state = GS_COMMS_STATE.DB_RW
        self.database_readwrite()

    @classmethod
    def received_TM_Storage(self):
        print(f"**** Received an TM_Storage {self.rx_message} ****")
        tm_data = TelemetryUnpacker.unpack_tm_frame_storage(self.rx_message)
        if (config.MODE == "DB"):
            db_services.add_Telemetry(MSG_ID.SAT_TM_STORAGE, tm_data)
        elif (config.MODE == "DBG"):
            db_queue.enqueue(f"TM_Storage:{self.rx_message}")

        self.state = GS_COMMS_STATE.DB_RW
        self.database_readwrite()

    @classmethod
    def received_TM_HAL(self):
        print(f"**** Received an TM_Storage {self.rx_message} ****")
        tm_data = TelemetryUnpacker.unpack_tm_frame_HAL(self.rx_message)
        if (config.MODE == "DB"):
            db_services.add_Telemetry(MSG_ID.SAT_TM_HAL, tm_data)
        elif (config.MODE == "DBG"):
            db_queue.enqueue(f"TM_HAL:{self.rx_message}")

        self.state = GS_COMMS_STATE.DB_RW
        self.database_readwrite()