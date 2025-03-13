from collections import deque
from lib.gs_constants import MSG_ID
from lib.telemetry.unpacking import RECEIVE

import time 

# Global FIFO Queue
queue = deque()
db_queue = deque()

def add_new_command(item):
    queue.append(item)

def get_latest_command():
    if is_empty():
        return "Queue is empty"
    return queue[0]

def remove_latest_command():
    if not is_empty():
        queue.popleft()

def commands_available():
    return len(queue) if queue else None

def is_empty():
    return len(queue) == 0

def size():
    return len(queue)

# TODO: need to adjust debug queue to match the rq_cmd of the db
# # Sending Ack commands 
# add_new_command({"id":MSG_ID.GS_CMD_SWITCH_TO_STATE, "args" : {"time_in_state" : 10, "target_state_id" : 1}})
# add_new_command({"id": MSG_ID.GS_CMD_UPLINK_TIME_REFERENCE, "args" : {"time_reference": int(time.time())}})
# add_new_command({"id": MSG_ID.GS_CMD_FORCE_REBOOT, "args" : {}})
# add_new_command({"id":MSG_ID.GS_CMD_UPLINK_ORBIT_REFERENCE, "args" : {"time_reference": 1741539508, "position_x": 0, "position_y": 1, "position_z": 3, "velocity_x": 4, "velocity_y": 5, "velocity_z": 6}})

# Sending File commands
#add_new_command({"id": MSG_ID.GS_CMD_FILE_METADATA, "args" : {"file_id": 10, "file_time": int(time.time())}})

# Sending TM commands
add_new_command({"id": MSG_ID.GS_CMD_REQUEST_TM_STORAGE, "args" : {}})
#add_new_command({"id": MSG_ID.GS_CMD_REQUEST_TM_HAL, "args" : {}})


def add_File_Packet(msg_data, file_db_id):
    print ("Add file pkt ")


def add_downlink_data(msg_id, rx_message):
    
    unpacked_data = RECEIVE.unpack_frame(msg_id, rx_message)

    if msg_id == MSG_ID.SAT_FILE_METADATA:
        print(unpacked_data)
        RECEIVE.file_id = unpacked_data["METADATA"]["FILE_ID"]
        RECEIVE.file_time = unpacked_data["METADATA"]["FILE_TIME"]
        RECEIVE.file_size = unpacked_data["METADATA"]["FILE_SIZE"]
        RECEIVE.file_target_sq = unpacked_data["METADATA"]["FILE_TARGET_SQ"]

    print ("added to Mock DB")