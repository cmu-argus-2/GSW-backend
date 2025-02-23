from gs_constants import MSG_ID
# Index constants for accessing data in the Data Handler


def const(val):
    # Mock for uPy mock
    return val


class CDH_IDX:
    TIME = const(0)
    SC_STATE = const(1)
    SD_USAGE = const(2)
    CURRENT_RAM_USAGE = const(3)
    REBOOT_COUNT = const(4)
    WATCHDOG_TIMER = const(5)
    HAL_BITFLAGS = const(6)
    DETUMBLING_ERROR_FLAG = const(7)

TM_METADATA_FORMAT = {
    "METADATA": [
        ("MSG_ID", "I"),
        ("SEQ_CNT", "H"), # Unsigned Short (2 Bytes)
        ("SIZE", "I"),
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
        ("DETUMBLING_ERROR_FLAG", "B"),
    ],
    "EPS": [
        ("EPS_POWER_FLAG", "B"),
        ("MAINBOARD_TEMPERATURE", "h"),
        ("MAINBOARD_VOLTAGE", "h"),
        ("MAINBOARD_CURRENT", "h"),
        ("BATTERY_PACK_TEMPERATURE", "h"),
        ("BATTERY_PACK_REPORTED_SOC", "B"),
        ("BATTERY_PACK_REPORTED_CAPACITY", "h"),
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
    ]
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

        # THERMAL Storage
        ("THERMAL_NUM_FILES", "I"),
        ("THERMAL_DIR_SIZE", "I"),

        # COMMAND Storage
        ("COMMAND_NUM_FILES", "I"),
        ("COMMAND_DIR_SIZE", "I"),

        # IMG Storage
        ("IMG_NUM_FILES", "I"),
        ("IMG_DIR_SIZE", "I"),
    ]
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

# TODO: Need to do it for payload once that is defined

DATA_FORMATS = {
    MSG_ID.SAT_TM_NOMINAL : HEARTBEAT_NOMINAL_FORMAT, 
    MSG_ID.SAT_HEARTBEAT : HEARTBEAT_NOMINAL_FORMAT, 
    MSG_ID.SAT_TM_STORAGE : TM_STORAGE_FORMAT, 
    MSG_ID.SAT_TM_HAL : TM_HAL_FORMAT
}

class EPS_IDX:
    TIME_EPS = const(0)
    EPS_POWER_FLAG = const(1)
    MAINBOARD_TEMPERATURE = const(2)
    MAINBOARD_VOLTAGE = const(3)
    MAINBOARD_CURRENT = const(4)
    BATTERY_PACK_TEMPERATURE = const(5)
    BATTERY_PACK_REPORTED_SOC = const(6)
    BATTERY_PACK_REPORTED_CAPACITY = const(7)
    BATTERY_PACK_CURRENT = const(8)
    BATTERY_PACK_VOLTAGE = const(9)
    BATTERY_PACK_MIDPOINT_VOLTAGE = const(10)
    BATTERY_PACK_TTE = const(11)
    BATTERY_PACK_TTF = const(12)
    XP_COIL_VOLTAGE = const(13)
    XP_COIL_CURRENT = const(14)
    XM_COIL_VOLTAGE = const(15)
    XM_COIL_CURRENT = const(16)
    YP_COIL_VOLTAGE = const(17)
    YP_COIL_CURRENT = const(18)
    YM_COIL_VOLTAGE = const(19)
    YM_COIL_CURRENT = const(20)
    ZP_COIL_VOLTAGE = const(21)
    ZP_COIL_CURRENT = const(22)
    ZM_COIL_VOLTAGE = const(23)
    ZM_COIL_CURRENT = const(24)
    JETSON_INPUT_VOLTAGE = const(25)
    JETSON_INPUT_CURRENT = const(26)
    RF_LDO_OUTPUT_VOLTAGE = const(27)
    RF_LDO_OUTPUT_CURRENT = const(28)
    GPS_VOLTAGE = const(29)
    GPS_CURRENT = const(30)
    XP_SOLAR_CHARGE_VOLTAGE = const(31)
    XP_SOLAR_CHARGE_CURRENT = const(32)
    XM_SOLAR_CHARGE_VOLTAGE = const(33)
    XM_SOLAR_CHARGE_CURRENT = const(34)
    YP_SOLAR_CHARGE_VOLTAGE = const(35)
    YP_SOLAR_CHARGE_CURRENT = const(36)
    YM_SOLAR_CHARGE_VOLTAGE = const(37)
    YM_SOLAR_CHARGE_CURRENT = const(38)
    ZP_SOLAR_CHARGE_VOLTAGE = const(39)
    ZP_SOLAR_CHARGE_CURRENT = const(40)
    ZM_SOLAR_CHARGE_VOLTAGE = const(41)
    ZM_SOLAR_CHARGE_CURRENT = const(42)


class ADCS_IDX:
    TIME_ADCS = const(0)
    MODE = const(1)
    GYRO_X = const(2)
    GYRO_Y = const(3)
    GYRO_Z = const(4)
    MAG_X = const(5)
    MAG_Y = const(6)
    MAG_Z = const(7)
    SUN_STATUS = const(8)
    SUN_VEC_X = const(9)
    SUN_VEC_Y = const(10)
    SUN_VEC_Z = const(11)
    LIGHT_SENSOR_XP = const(12)
    LIGHT_SENSOR_XM = const(13)
    LIGHT_SENSOR_YP = const(14)
    LIGHT_SENSOR_YM = const(15)
    LIGHT_SENSOR_ZP1 = const(16)
    LIGHT_SENSOR_ZP2 = const(17)
    LIGHT_SENSOR_ZP3 = const(18)
    LIGHT_SENSOR_ZP4 = const(19)
    LIGHT_SENSOR_ZM = const(20)
    XP_COIL_STATUS = const(21)
    XM_COIL_STATUS = const(22)
    YP_COIL_STATUS = const(23)
    YM_COIL_STATUS = const(24)
    ZP_COIL_STATUS = const(25)
    ZM_COIL_STATUS = const(26)
    ATTITUDE_QW = const(27)
    ATTITUDE_QX = const(28)
    ATTITUDE_QY = const(29)
    ATTITUDE_QZ = const(30)


class IMU_IDX:
    TIME_IMU = const(0)
    ACCEL_X = const(1)
    ACCEL_Y = const(2)
    ACCEL_Z = const(3)
    MAGNETOMETER_X = const(4)
    MAGNETOMETER_Y = const(5)
    MAGNETOMETER_Z = const(6)
    GYROSCOPE_X = const(7)
    GYROSCOPE_Y = const(8)
    GYROSCOPE_Z = const(9)


class GPS_IDX:
    TIME_GPS = const(0)
    GPS_MESSAGE_ID = const(1)
    GPS_FIX_MODE = const(2)
    GPS_NUMBER_OF_SV = const(3)
    GPS_GNSS_WEEK = const(4)
    GPS_GNSS_TOW = const(5)
    GPS_LATITUDE = const(6)
    GPS_LONGITUDE = const(7)
    GPS_ELLIPSOID_ALT = const(8)
    GPS_MEAN_SEA_LVL_ALT = const(9)
    GPS_GDOP = const(10)
    GPS_PDOP = const(11)
    GPS_HDOP = const(12)
    GPS_VDOP = const(13)
    GPS_TDOP = const(14)
    GPS_ECEF_X = const(15)
    GPS_ECEF_Y = const(16)
    GPS_ECEF_Z = const(17)
    GPS_ECEF_VX = const(18)
    GPS_ECEF_VY = const(19)
    GPS_ECEF_VZ = const(20)


class PAYLOAD_IDX:
    pass

class STORAGE_IDX:
    TOTAL = const(0)
    CDH_NUM_FILES = const(1)
    CDH_DIR_SIZE = const(2)
    EPS_NUM_FILES = const(3)
    EPS_DIR_SIZE = const(4)
    ADCS_NUM_FILES = const(5)
    ADCS_DIR_SIZE = const(6)
    COMMS_NUM_FILES = const(7)
    COMMS_DIR_SIZE = const(8)
    GPS_NUM_FILES = const(9)
    GPS_DIR_SIZE = const(10)
    PAYLOAD_NUM_FILES = const(11)
    PAYLOAD_DIR_SIZE = const(12)
    THERMAL_NUM_FILES = const(13)
    THERMAL_DIR_SIZE = const(14)
    COMMAND_NUM_FILES = const(15)
    COMMAND_DIR_SIZE = const(16)
    IMG_NUM_FILES = const(17)
    IMG_DIR_SIZE = const(18)
