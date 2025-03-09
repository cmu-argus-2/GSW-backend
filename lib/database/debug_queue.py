from collections import deque
from lib.gs_constants import MSG_ID


class fifoQ:
    def __init__(self):
        self.queue = deque()

    def add_new_command(self, item):
        self.queue.append(item)

    def get_latest_command(self):
        if self.is_empty():
            return "Queue is empty"
        return self.queue[0]
    
    def remove_latest_command(self):
        if not self.is_empty():
            self.queue.popleft()

    def commands_available(self):
        if len(self.queue) != 0: 
            return len(self.queue)
        else:
            return None

    def size(self):
        return len(self.queue)

# Command Interface Instantiation
queue = fifoQ()

# TODO: need to adjust debug queue to match the rq_cmd of the db
# Sending Ack commands 
queue.add_new_command({"id":MSG_ID.GS_CMD_SWITCH_TO_STATE, "args" : {"time_in_state" : 10, "target_state_id" : 1}})
queue.add_new_command({"id": MSG_ID.GS_CMD_UPLINK_TIME_REFERENCE, "args" : {"time_reference": 1741539508}})
queue.add_new_command({"id": MSG_ID.GS_CMD_FORCE_REBOOT, "args" : {}})
queue.add_new_command({"id":MSG_ID.GS_CMD_UPLINK_ORBIT_REFERENCE, "args" : {"time_reference": 1741539508, "position_x": 0, "position_y": 1, "position_z": 3, "velocity_x": 4, "velocity_y": 5, "velocity_z": 6}})

# Sending File commands
queue.add_new_command({"id": MSG_ID.GS_CMD_FILE_METADATA, "args" : {}})

# Sending TM commands
queue.add_new_command({"id": MSG_ID.SAT_TM_STORAGE, "args" : {}})
queue.add_new_command({"id": MSG_ID.SAT_TM_HAL, "args" : {}})

# Database Queue Instantiation
db_queue = fifoQ()

# --------------------------------------------------------------------------- #
