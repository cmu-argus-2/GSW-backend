import json

from lib.database.db_server import query
from lib.gs_constants import MSG_ID
from lib.telemetry.unpacking import RECEIVE


def handle_command_ACK(ack):
    """If SC sends an ack for a command, we need to handle successful and failed executions of commands.
    If successful, remove from the command queue (TX table).
    """
    if ack == 0x0F:
        # TODO: handle the logic for this for GS rework
        # remove_latest_command()
        pass
    else:
        # TODO: Think about what to do if failed, resend command?
        pass


def add_Telemetry(msg_id, tm_data):
    """A query to insert a new Heartbeat packet into the database (RX table)"""
    # Ensure that this is a telemetry frame
    if msg_id not in MSG_ID.TM_FRAME_TYPES:
        # TODO: error handling
        return

    msg_name = ""
    if msg_id == MSG_ID.SAT_TM_NOMINAL:
        msg_name = "SAT_TM_NOMINAL"
    elif msg_id == MSG_ID.SAT_TM_HAL:
        msg_name = "SAT_TM_HAL"
    elif msg_id == MSG_ID.SAT_TM_STORAGE:
        msg_name = "SAT_TM_STORAGE"
    elif msg_id == MSG_ID.SAT_TM_PAYLOAD:
        msg_name = "SAT_PAYLOAD"

    msg_data = json.dumps(tm_data)
    print(msg_data)
    print(tm_data)

    result = query(
        """
        INSERT INTO rxData_tb (rx_name, rx_id, rx_type, rx_data)
        VALUES (%s, %s, %s, %s::json);
        """,
        (msg_name, msg_id, "telemetry", msg_data),
    )


def add_Ack(msg_data=None):
    # TODO: More specific ACK ?
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
        ("SAT_ACK", MSG_ID.SAT_ACK, "ack"),
    )


def add_File_Meta_Data(msg_data):
    msg_obj = {
        "file_id": msg_data[0],
        "file_time": msg_data[1],
        "file_size": msg_data[2],
        "file_rq_sq": msg_data[3],
    }
    file_MD = json.dumps(msg_obj)
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
        ("SAT_FILE_METADATA", MSG_ID.SAT_FILE_METADATA, "file", file_MD),
    )


def add_File_Packet(msg_data, file_db_id):
    # TODO: need to further integrate this
    encoded_list = [data.hex() for data in msg_data]
    file_pkt = json.dumps(encoded_list)
    print(file_pkt)
    result = query(
        """
        UPDATE rxData_tb
        SET rx_data = jsonb_set(
            rx_data, 
            '{file_packets}', 
            %s
        )
        WHERE rx_data->>'file_id' = %s;
        """,
        (file_pkt, str(file_db_id)),
    )


def add_downlink_data(msg_id, rx_message):
    """Handle adding data that was downlinked to the database (RX table)"""
    # TODO: error handling for unpack frame
    # TODO: add print statements to each received message
    unpacked_data = RECEIVE.unpack_frame(msg_id, rx_message)

    # Insert TM frames into db
    if msg_id in MSG_ID.TM_FRAME_TYPES:
        add_Telemetry(msg_id, unpacked_data)

    # Insert file metadata into db
    elif msg_id == MSG_ID.SAT_FILE_METADATA:
        add_File_Meta_Data(unpacked_data)

    #Insert ACK into db
    elif msg_id == MSG_ID.SAT_ACK:
        add_Ack()

