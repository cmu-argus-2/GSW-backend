from micropython import const


class DB_QUERY_STATUS:
    EXECUTION_SUCCESSFUL = const(0x00)
    EXECUTION_FAILED = const(0x01)
