from lib.database.db_server import query
"""
    Handles all the interactions with the command queue from the database
"""

def get_latest_command():
    """Retrieve the latest command on the command queue (TX table)"""
    result = query(
        """ 
        SELECT * FROM public.txcommands_tb
        ORDER BY created_at ASC
        LIMIT 1;
    """
    )
    print("Result:", result)
    # TODO: format that so that it returns the arguments as well
    if (result is not None) and result[1] != []:
        # turn values into ints
        args = {k: int(val) for k, val in result[1][0][3].items()}
        return {"id": result[1][0][1], "args": args}
    else:
        return {"id": 70, "args": {}}


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
