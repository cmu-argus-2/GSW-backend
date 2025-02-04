from database_server import query
from groundstation import MSG_ID


def get_latest_command():
    """Retrieve the latest command on the command queue (TX table)"""
    result = query(
        """ 
        SELECT * FROM public.txcommands_tb
        ORDER BY created_at ASC
        LIMIT 1;
    """
    )
    return result[0] if result else None


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


def handle_command_ACK(ack):
    """If SC sends an ack for a command, we need to handle successful and failed executions of commands.
    If successful, remove from the command queue (TX table).
    """
    if ack == MSG_ID.SAT_ACK:
        remove_latest_command()
    else:
        # TODO: Think about what to do if failed, resend command?
        pass


def add_SAT_HEARTBEAT(arg_list):
    """A query to insert a new Heartbeat packet into the database (RX table)"""
    result = query(
        """

    """
    )


def add_downlink_data(data_type, args=None):
    """Handle adding data that was downlinked to the database (RX table)"""

    # Insert TM frames into db
    if data_type == MSG_ID.SAT_HEARTBEAT:
        pass

    # Insert files into db
    elif data_type == MSG_ID.SAT_FILE_PKT:
        pass
