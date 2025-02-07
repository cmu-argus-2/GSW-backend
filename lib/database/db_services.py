from lib.database.db_server import query
# from groundstation import MSG_ID
from lib.telemetry.unpacking import TelemetryUnpacker
import json


def get_latest_command():
    """Retrieve the latest command on the command queue (TX table)"""
    result = query(
        """ 
        SELECT * FROM public.txcommands_tb
        ORDER BY created_at ASC
        LIMIT 1;
    """
    )
    print ("Reult:", result)
    if result[1] != []: 
        return result[1][0][1]
    else:
        return 70


def remove_latest_command():
    """Retrieve the latest command on the command queue (TX table)"""
    result = query(
        """
        DELETE FROM txCommands_tb
        WHERE id = (
            SELECT id FROM txCommands_tb
            ORDER BY created_at ASC
            LIMIT 1 
        )
        RETURNING *;
    """
    )
    return result[0] if result else None

def commands_available():
    """Determine if there are commands available and queued up"""
    result = query(
        """
        SELECT EXISTS (SELECT 1 FROM txCommands_tb LIMIT 1);
        """
    )
    return result

def handle_command_ACK(ack):
    """If SC sends an ack for a command, we need to handle successful and failed executions of commands.
    If successful, remove from the command queue (TX table).
    """
    if ack == 0x0F:
        remove_latest_command()
    else:
        # TODO: Think about what to do if failed, resend command?
        pass


def add_Telemetry():
    """A query to insert a new Heartbeat packet into the database (RX table)"""
    msg_data = json.dumps(TelemetryUnpacker.get_heartbeat())

    # TODO: do for other types of telemetry
    result = query(
        """
        INSERT INTO rxData_tb (rx_name, rx_id, rx_type, rx_data)
        VALUES (%s, %s, %s, %s::jsonb);
        """,
        ('SAT_HEARTBEAT', 0x01, 'telemetry', msg_data) 
    )

    
def add_Ack(msg_data=None):
    result = query(
        """
        INSERT INTO rxData_tb (rx_name, rx_id, rx_type, rx_data)
        VALUES (
            %s,
            %s, 
            %s,
            '{
                "status": "Successful Execution"
            }'::jsonb
        );
        """,
        ('SAT_ACK', 0x0F, 'ack') 
    )
    
def add_File_Meta_Data(msg_data):
    file_MD = json.dumps(msg_data)
    result = query(
        """
        INSERT INTO rxData_tb (rx_name, rx_id, rx_type, rx_data)
        VALUES (
            %s,
            %s, 
            %s,
            %s::jsonb
        );
        """,
        ('SAT_FILE_METADATA', 0x10, 'file', file_MD)
    )

def add_File_Packet(msg_data, file_id):
    file_pkt = json.dumps(msg_data)
    result = query(
        """"
        UPDATE rxData_tb
        SET rx_data = jsonb_set(
            rx_data, 
            '{file_packets}', 
            %s::jsonb
        )
        WHERE rx_data->>'file_id' = %s;
        """,
        (file_pkt, file_id)
    )

# def add_downlink_data(data_type, args_list=None):
#     """Handle adding data that was downlinked to the database (RX table)"""

#     # Insert TM frames into db
#     if data_type == MSG_ID.SAT_HEARTBEAT or data_type == MSG_ID.SAT_TM_HAL or data_type == MSG_ID.SAT_TM_PAYLOAD or MSG_ID.SAT_TM_STORAGE:
#         add_Telemetry(args_list)

#     # Insert file metadata into db
#     elif data_type == MSG_ID.SAT_FILE_METADATA:
#         add_File_Meta_Data()
    
#     #Insert ACK into db
#     elif data_type == MSG_ID.SAT_ACK:
#         add_Ack()
