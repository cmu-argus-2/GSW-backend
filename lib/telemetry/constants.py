from lib.gs_constants import MSG_ID


file_tags_str = {
    1: "cmd_logs",
    2: "watchdog",
    3: "eps",
    4: "cdh",
    5: "comms",
    6: "imu",
    7: "adcs",
    8: "thermal",
    9: "gps",
    10: "img",
}


METADATA_FORMAT = {
    "METADATA": [
        ("FILE_ID", "B"),  # Unsigned Byte (1 byte)
        ("FILE_TIME", "I"),  # Unsigned Long (4 bytes)
        ("FILE_SIZE", "I"), # Unsigned Long (4 bytes)
        ("FILE_TARGET_SQ", "H"),  # Unsigned Short (2 Bytes)
    ]
}

HEARTBEAT_NOMINAL_FORMAT = {
    "CDH": [
        ("TIME", "I"),  # Unsigned Long (4 bytes)
        ("SC_STATE", "B"),  # Unsigned Byte (1 byte)
        ("SD_USAGE", "I"),
        ("CURRENT_RAM_USAGE", "B"),
        ("REBOOT_COUNT", "B"),
        ("WATCHDOG_TIMER", "B"),
        ("HAL_BITFLAGS", "B"),
        ("DETUMBLING_ERROR_FLAG", "B")
    ],
    "EPS": [
        ("EPS_POWER_FLAG", "B"),
        ("MAINBOARD_TEMPERATURE", "h"),
        ("MAINBOARD_VOLTAGE", "h"),
        ("MAINBOARD_CURRENT", "h"),
        ("BATTERY_PACK_TEMPERATURE", "h"),
        ("BATTERY_PACK_REPORTED_SOC", "B"),
        ("BATTERY_PACK_REPORTED_CAPACITY", "H"),
        ("BATTERY_PACK_CURRENT", "h"),
        ("BATTERY_PACK_VOLTAGE", "h"),
        ("BATTERY_PACK_MIDPOINT_VOLTAGE", "h"),
        ("BATTERY_PACK_TTE", "I"),
        ("BATTERY_PACK_TTF", "I"),
        ("XP_COIL_VOLTAGE", "h"),
        ("XP_COIL_CURRENT", "h"),
        ("XM_COIL_VOLTAGE", "h"),
        ("XM_COIL_CURRENT", "h"),
        ("YP_COIL_VOLTAGE", "h"),
        ("YP_COIL_CURRENT", "h"),
        ("YM_COIL_VOLTAGE", "h"),
        ("YM_COIL_CURRENT", "h"),
        ("ZP_COIL_VOLTAGE", "h"),
        ("ZP_COIL_CURRENT", "h"),
        ("ZM_COIL_VOLTAGE", "h"),
        ("ZM_COIL_CURRENT", "h"),
        ("JETSON_INPUT_VOLTAGE", "h"),
        ("JETSON_INPUT_CURRENT", "h"),
        ("RF_LDO_OUTPUT_VOLTAGE", "h"),
        ("RF_LDO_OUTPUT_CURRENT", "h"),
        ("GPS_VOLTAGE", "h"),
        ("GPS_CURRENT", "h"),
        ("XP_SOLAR_CHARGE_VOLTAGE", "h"),
        ("XP_SOLAR_CHARGE_CURRENT", "h"),
        ("XM_SOLAR_CHARGE_VOLTAGE", "h"),
        ("XM_SOLAR_CHARGE_CURRENT", "h"),
        ("YP_SOLAR_CHARGE_VOLTAGE", "h"),
        ("YP_SOLAR_CHARGE_CURRENT", "h"),
        ("YM_SOLAR_CHARGE_VOLTAGE", "h"),
        ("YM_SOLAR_CHARGE_CURRENT", "h"),
        ("ZP_SOLAR_CHARGE_VOLTAGE", "h"),
        ("ZP_SOLAR_CHARGE_CURRENT", "h"),
        ("ZM_SOLAR_CHARGE_VOLTAGE", "h"),
        ("ZM_SOLAR_CHARGE_CURRENT", "h"),
    ],
    "ADCS": [
        ("MODE", "B"),
        ("GYRO_X", "f"),
        ("GYRO_Y", "f"),
        ("GYRO_Z", "f"),
        ("MAG_X", "f"),
        ("MAG_Y", "f"),
        ("MAG_Z", "f"),
        ("SUN_STATUS", "B"),
        ("SUN_VEC_X", "f"),
        ("SUN_VEC_Y", "f"),
        ("SUN_VEC_Z", "f"),
        ("LIGHT_SENSOR_XP", "h"),
        ("LIGHT_SENSOR_XM", "h"),
        ("LIGHT_SENSOR_YP", "h"),
        ("LIGHT_SENSOR_YM", "h"),
        ("LIGHT_SENSOR_ZP1", "h"),
        ("LIGHT_SENSOR_ZP2", "h"),
        ("LIGHT_SENSOR_ZP3", "h"),
        ("LIGHT_SENSOR_ZP4", "h"),
        ("LIGHT_SENSOR_ZM", "h"),
        ("XP_COIL_STATUS", "B"),
        ("XM_COIL_STATUS", "B"),
        ("YP_COIL_STATUS", "B"),
        ("YM_COIL_STATUS", "B"),
        ("ZP_COIL_STATUS", "B"),
        ("ZM_COIL_STATUS", "B"),
        ("ATTITUDE_QW", "f"),
        ("ATTITUDE_QX", "f"),
        ("ATTITUDE_QY", "f"),
        ("ATTITUDE_QZ", "f"),
    ],
    "GPS": [
        ("MESSAGE_ID", "B"),
        ("FIX_MODE", "B"),
        ("NUMBER_OF_SV", "B"),
        ("GNSS_WEEK", "H"),
        ("GNSS_TOW", "I"),
        ("LATITUDE", "i"),
        ("LONGITUDE", "i"),
        ("ELLIPSOID_ALT", "i"),
        ("MEAN_SEA_LVL_ALT", "i"),
        ("ECEF_X", "i"),
        ("ECEF_Y", "i"),
        ("ECEF_Z", "i"),
        ("ECEF_VX", "i"),
        ("ECEF_VY", "i"),
        ("ECEF_VZ", "i"),
    ],
}

TM_STORAGE_FORMAT = {
    "CDH": [
        ("TIME", "I"),  # Unsigned Long (4 bytes)
        ("SC_STATE", "B"),  # Unsigned Byte (1 byte)
        ("SD_USAGE", "I"),
        ("CURRENT_RAM_USAGE", "B"),
        ("REBOOT_COUNT", "B"),
        ("WATCHDOG_TIMER", "B"),
        ("HAL_BITFLAGS", "B"),
        ("DETUMBLING_ERROR_FLAG", "B"),
    ],
    "STORAGE": [
        ("TOTAL", "I"),  # Unsigned Long (4 bytes)
        # CDH Storage
        ("CDH_NUM_FILES", "I"),
        ("CDH_DIR_SIZE", "I"),
        # EPS Storage
        ("EPS_NUM_FILES", "I"),
        ("EPS_DIR_SIZE", "I"),
        # ADCS Storage
        ("ADCS_NUM_FILES", "I"),
        ("ADCS_DIR_SIZE", "I"),
        # COMMS Storage
        ("COMMS_NUM_FILES", "I"),
        ("COMMS_DIR_SIZE", "I"),
        # GPS Storage
        ("GPS_NUM_FILES", "I"),
        ("GPS_DIR_SIZE", "I"),
        # PAYLOAD Storage
        ("PAYLOAD_NUM_FILES", "I"),
        ("PAYLOAD_DIR_SIZE", "I"),
        # COMMAND Storage
        ("COMMAND_NUM_FILES", "I"),
        ("COMMAND_DIR_SIZE", "I"),
    ],
}

# TODO: finish once error codes are established
TM_HAL_FORMAT = {
    "CDH": [
        ("TIME", "I"),  # Unsigned Long (4 bytes)
        ("SC_STATE", "B"),  # Unsigned Byte (1 byte)
        ("SD_USAGE", "I"),
        ("CURRENT_RAM_USAGE", "B"),
        ("REBOOT_COUNT", "B"),
        ("WATCHDOG_TIMER", "B"),
        ("HAL_BITFLAGS", "B"),
        ("DETUMBLING_ERROR_FLAG", "B"),
    ],
}

ACK_FORMAT = {"ACK_TYPE": [("ACK", "B")]}  # Could be different types of acks


# TODO: Need to do it for payload once that is defined

DATA_FORMATS = {
    MSG_ID.SAT_TM_NOMINAL: HEARTBEAT_NOMINAL_FORMAT,
    MSG_ID.SAT_HEARTBEAT: HEARTBEAT_NOMINAL_FORMAT,
    MSG_ID.SAT_TM_STORAGE: TM_STORAGE_FORMAT,
    MSG_ID.SAT_TM_HAL: TM_HAL_FORMAT,
    MSG_ID.SAT_ACK: ACK_FORMAT,
    MSG_ID.SAT_FILE_METADATA: METADATA_FORMAT,
}