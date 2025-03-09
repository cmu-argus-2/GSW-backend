"""
GS Telemetry Unpacker
"""
import struct
import datetime
import time

from lib.telemetry.constants import *
from lib.telemetry.helpers import *

# Const IDX numbers
CDH_NUM = 8
EPS_NUM = 43
ADCS_NUM = 31
GPS_NUM = 21
STORAGE_NUM = 19


class RECEIVE:
    _msg_id = 0
    _seq_cnt = 0
    _size = 0

    _data_CDH = [0] * CDH_NUM
    _data_EPS = [0] * EPS_NUM
    _data_ADCS = [0] * ADCS_NUM
    _data_GPS = [0] * GPS_NUM
    _data_STORAGE = [0] * STORAGE_NUM

    # Source header parameters
    rx_src_id = 0x00
    rx_dst_id = 0x00

    # RX message parameters
    # received msg parameters
    rx_msg_id = 0x00
    rx_msg_sq = 0
    rx_msg_size = 0
    rx_message = []

    @classmethod
    def unpack_tm_frame_nominal(self, msg):
        """
        Unpack TM frame received from satellite and put data
        in vectors for each onboard subsystem.
        """

        msg = list(msg)

        ############ TM Metadata ############
        self._msg_id = msg[0]
        self._seq_cnt = unpack_unsigned_short_int(msg[1:3])
        self._size = msg[3]

        # TODO: Good sanity checks for message type and length
        if self._msg_id != 0x01:
            raise RuntimeError("Message is not TM frame")
        if self._seq_cnt != 0:
            raise RuntimeError("Message seq. count incorrect")
        if self._size != 227:
            raise RuntimeError("Message length incorrect")

        ############ CDH Fields ############
        self._data_CDH[CDH_IDX.TIME] = unpack_unsigned_long_int(msg[4:8])
        self._data_CDH[CDH_IDX.SC_STATE] = msg[8]
        self._data_CDH[CDH_IDX.SD_USAGE] = unpack_unsigned_long_int(msg[9:13])
        self._data_CDH[CDH_IDX.CURRENT_RAM_USAGE] = msg[13]
        self._data_CDH[CDH_IDX.REBOOT_COUNT] = msg[14]
        self._data_CDH[CDH_IDX.WATCHDOG_TIMER] = msg[15]
        self._data_CDH[CDH_IDX.HAL_BITFLAGS] = msg[16]
        self._data_CDH[CDH_IDX.DETUMBLING_ERROR_FLAG] = msg[17]

        # CDH time for all data vectors
        self._data_EPS[EPS_IDX.TIME_EPS] = self._data_CDH[CDH_IDX.TIME]
        self._data_ADCS[ADCS_IDX.TIME_ADCS] = self._data_CDH[CDH_IDX.TIME]
        self._data_GPS[GPS_IDX.TIME_GPS] = self._data_CDH[CDH_IDX.TIME]

        ############ EPS Fields ############
        self._data_EPS[EPS_IDX.EPS_POWER_FLAG] = msg[18]
        self._data_EPS[EPS_IDX.MAINBOARD_TEMPERATURE] = unpack_signed_short_int(
            msg[19:21]
        )
        self._data_EPS[EPS_IDX.MAINBOARD_VOLTAGE] = unpack_signed_short_int(msg[21:23])
        self._data_EPS[EPS_IDX.MAINBOARD_CURRENT] = unpack_signed_short_int(msg[23:25])

        self._data_EPS[EPS_IDX.BATTERY_PACK_TEMPERATURE] = unpack_signed_short_int(
            msg[25:27]
        )
        self._data_EPS[EPS_IDX.BATTERY_PACK_REPORTED_SOC] = msg[27]
        self._data_EPS[
            EPS_IDX.BATTERY_PACK_REPORTED_CAPACITY
        ] = unpack_signed_short_int(msg[28:30])
        self._data_EPS[EPS_IDX.BATTERY_PACK_CURRENT] = unpack_signed_short_int(
            msg[30:32]
        )
        self._data_EPS[EPS_IDX.BATTERY_PACK_VOLTAGE] = unpack_signed_short_int(
            msg[32:34]
        )
        self._data_EPS[EPS_IDX.BATTERY_PACK_MIDPOINT_VOLTAGE] = unpack_signed_short_int(
            msg[34:36]
        )
        self._data_EPS[EPS_IDX.BATTERY_PACK_TTE] = unpack_unsigned_long_int(msg[36:40])
        self._data_EPS[EPS_IDX.BATTERY_PACK_TTF] = unpack_unsigned_long_int(msg[40:44])

        self._data_EPS[EPS_IDX.XP_COIL_VOLTAGE] = unpack_signed_short_int(msg[44:46])
        self._data_EPS[EPS_IDX.XP_COIL_CURRENT] = unpack_signed_short_int(msg[46:48])
        self._data_EPS[EPS_IDX.XM_COIL_VOLTAGE] = unpack_signed_short_int(msg[48:50])
        self._data_EPS[EPS_IDX.XM_COIL_CURRENT] = unpack_signed_short_int(msg[50:52])

        self._data_EPS[EPS_IDX.YP_COIL_VOLTAGE] = unpack_signed_short_int(msg[52:54])
        self._data_EPS[EPS_IDX.YP_COIL_CURRENT] = unpack_signed_short_int(msg[54:56])
        self._data_EPS[EPS_IDX.YM_COIL_VOLTAGE] = unpack_signed_short_int(msg[56:58])
        self._data_EPS[EPS_IDX.YM_COIL_CURRENT] = unpack_signed_short_int(msg[58:60])

        self._data_EPS[EPS_IDX.ZP_COIL_VOLTAGE] = unpack_signed_short_int(msg[60:62])
        self._data_EPS[EPS_IDX.ZP_COIL_CURRENT] = unpack_signed_short_int(msg[62:64])
        self._data_EPS[EPS_IDX.ZM_COIL_VOLTAGE] = unpack_signed_short_int(msg[64:66])
        self._data_EPS[EPS_IDX.ZM_COIL_CURRENT] = unpack_signed_short_int(msg[66:68])

        self._data_EPS[EPS_IDX.JETSON_INPUT_VOLTAGE] = unpack_signed_short_int(
            msg[68:70]
        )
        self._data_EPS[EPS_IDX.JETSON_INPUT_CURRENT] = unpack_signed_short_int(
            msg[70:72]
        )

        self._data_EPS[EPS_IDX.RF_LDO_OUTPUT_VOLTAGE] = unpack_signed_short_int(
            msg[72:74]
        )
        self._data_EPS[EPS_IDX.RF_LDO_OUTPUT_CURRENT] = unpack_signed_short_int(
            msg[74:76]
        )

        self._data_EPS[EPS_IDX.GPS_VOLTAGE] = unpack_signed_short_int(msg[76:78])
        self._data_EPS[EPS_IDX.GPS_CURRENT] = unpack_signed_short_int(msg[78:80])

        self._data_EPS[EPS_IDX.XP_SOLAR_CHARGE_VOLTAGE] = unpack_signed_short_int(
            msg[80:82]
        )
        self._data_EPS[EPS_IDX.XP_SOLAR_CHARGE_CURRENT] = unpack_signed_short_int(
            msg[82:84]
        )
        self._data_EPS[EPS_IDX.XM_SOLAR_CHARGE_VOLTAGE] = unpack_signed_short_int(
            msg[84:86]
        )
        self._data_EPS[EPS_IDX.XM_SOLAR_CHARGE_CURRENT] = unpack_signed_short_int(
            msg[86:88]
        )

        self._data_EPS[EPS_IDX.YP_SOLAR_CHARGE_VOLTAGE] = unpack_signed_short_int(
            msg[88:90]
        )
        self._data_EPS[EPS_IDX.YP_SOLAR_CHARGE_CURRENT] = unpack_signed_short_int(
            msg[90:92]
        )
        self._data_EPS[EPS_IDX.YM_SOLAR_CHARGE_VOLTAGE] = unpack_signed_short_int(
            msg[92:94]
        )
        self._data_EPS[EPS_IDX.YM_SOLAR_CHARGE_CURRENT] = unpack_signed_short_int(
            msg[94:96]
        )

        self._data_EPS[EPS_IDX.ZP_SOLAR_CHARGE_VOLTAGE] = unpack_signed_short_int(
            msg[96:98]
        )
        self._data_EPS[EPS_IDX.ZP_SOLAR_CHARGE_CURRENT] = unpack_signed_short_int(
            msg[98:100]
        )
        self._data_EPS[EPS_IDX.ZM_SOLAR_CHARGE_VOLTAGE] = unpack_signed_short_int(
            msg[100:102]
        )
        self._data_EPS[EPS_IDX.ZM_SOLAR_CHARGE_CURRENT] = unpack_signed_short_int(
            msg[102:104]
        )

        ############ ADCS Fields ############
        self._data_ADCS[ADCS_IDX.MODE] = msg[104]

        self._data_ADCS[ADCS_IDX.GYRO_X] = convert_fixed_point_to_float_hp(msg[105:109])
        self._data_ADCS[ADCS_IDX.GYRO_Y] = convert_fixed_point_to_float_hp(msg[109:113])
        self._data_ADCS[ADCS_IDX.GYRO_Z] = convert_fixed_point_to_float_hp(msg[113:117])

        self._data_ADCS[ADCS_IDX.MAG_X] = convert_fixed_point_to_float_hp(msg[117:121])
        self._data_ADCS[ADCS_IDX.MAG_Y] = convert_fixed_point_to_float_hp(msg[121:125])
        self._data_ADCS[ADCS_IDX.MAG_Z] = convert_fixed_point_to_float_hp(msg[125:129])

        self._data_ADCS[ADCS_IDX.SUN_STATUS] = msg[129]

        self._data_ADCS[ADCS_IDX.SUN_VEC_X] = convert_fixed_point_to_float_hp(
            msg[130:134]
        )
        self._data_ADCS[ADCS_IDX.SUN_VEC_Y] = convert_fixed_point_to_float_hp(
            msg[134:138]
        )
        self._data_ADCS[ADCS_IDX.SUN_VEC_Z] = convert_fixed_point_to_float_hp(
            msg[138:142]
        )

        self._data_ADCS[ADCS_IDX.LIGHT_SENSOR_XP] = unpack_signed_short_int(
            msg[142:144]
        )
        self._data_ADCS[ADCS_IDX.LIGHT_SENSOR_XM] = unpack_signed_short_int(
            msg[144:146]
        )
        self._data_ADCS[ADCS_IDX.LIGHT_SENSOR_YP] = unpack_signed_short_int(
            msg[146:148]
        )
        self._data_ADCS[ADCS_IDX.LIGHT_SENSOR_YM] = unpack_signed_short_int(
            msg[148:150]
        )
        self._data_ADCS[ADCS_IDX.LIGHT_SENSOR_ZP1] = unpack_signed_short_int(
            msg[150:152]
        )
        self._data_ADCS[ADCS_IDX.LIGHT_SENSOR_ZP2] = unpack_signed_short_int(
            msg[152:154]
        )
        self._data_ADCS[ADCS_IDX.LIGHT_SENSOR_ZP3] = unpack_signed_short_int(
            msg[154:156]
        )
        self._data_ADCS[ADCS_IDX.LIGHT_SENSOR_ZP4] = unpack_signed_short_int(
            msg[156:158]
        )
        self._data_ADCS[ADCS_IDX.LIGHT_SENSOR_ZM] = unpack_signed_short_int(
            msg[158:160]
        )

        self._data_ADCS[ADCS_IDX.XP_COIL_STATUS] = msg[160]
        self._data_ADCS[ADCS_IDX.XM_COIL_STATUS] = msg[161]
        self._data_ADCS[ADCS_IDX.YP_COIL_STATUS] = msg[162]
        self._data_ADCS[ADCS_IDX.YM_COIL_STATUS] = msg[163]
        self._data_ADCS[ADCS_IDX.ZP_COIL_STATUS] = msg[164]
        self._data_ADCS[ADCS_IDX.ZM_COIL_STATUS] = msg[165]

        self._data_ADCS[ADCS_IDX.ATTITUDE_QW] = convert_fixed_point_to_float_hp(
            msg[166:170]
        )
        self._data_ADCS[ADCS_IDX.ATTITUDE_QX] = convert_fixed_point_to_float_hp(
            msg[170:174]
        )
        self._data_ADCS[ADCS_IDX.ATTITUDE_QY] = convert_fixed_point_to_float_hp(
            msg[174:178]
        )
        self._data_ADCS[ADCS_IDX.ATTITUDE_QZ] = convert_fixed_point_to_float_hp(
            msg[178:182]
        )

        ############ GPS Fields ############
        self._data_GPS[GPS_IDX.GPS_MESSAGE_ID] = msg[182]
        self._data_GPS[GPS_IDX.GPS_FIX_MODE] = msg[183]
        self._data_GPS[GPS_IDX.GPS_NUMBER_OF_SV] = msg[184]

        self._data_GPS[GPS_IDX.GPS_GNSS_WEEK] = unpack_unsigned_short_int(msg[185:187])
        self._data_GPS[GPS_IDX.GPS_GNSS_TOW] = unpack_unsigned_long_int(msg[187:191])

        self._data_GPS[GPS_IDX.GPS_LATITUDE] = unpack_signed_long_int(msg[191:195])
        self._data_GPS[GPS_IDX.GPS_LONGITUDE] = unpack_signed_long_int(msg[195:199])
        self._data_GPS[GPS_IDX.GPS_ELLIPSOID_ALT] = unpack_signed_long_int(msg[199:203])
        self._data_GPS[GPS_IDX.GPS_MEAN_SEA_LVL_ALT] = unpack_signed_long_int(
            msg[203:207]
        )

        self._data_GPS[GPS_IDX.GPS_ECEF_X] = unpack_signed_long_int(msg[207:211])
        self._data_GPS[GPS_IDX.GPS_ECEF_Y] = unpack_signed_long_int(msg[211:215])
        self._data_GPS[GPS_IDX.GPS_ECEF_Z] = unpack_signed_long_int(msg[215:219])
        self._data_GPS[GPS_IDX.GPS_ECEF_VX] = unpack_signed_long_int(msg[219:223])
        self._data_GPS[GPS_IDX.GPS_ECEF_VY] = unpack_signed_long_int(msg[223:227])
        self._data_GPS[GPS_IDX.GPS_ECEF_VZ] = unpack_signed_long_int(msg[227:231])

        # TODO: Remove temp debugging
        print()
        print("Metadata (ID, SQ_CNT, LEN):", self._msg_id, self._seq_cnt, self._size)
        print("CDH Data:", self._data_CDH)
        print("EPS Data:", self._data_EPS)
        print("ADCS Data:", self._data_ADCS)
        print("GPS Data:", self._data_GPS)
        print()

        heartbeat = {
            "msg_id": self._msg_id,
            "seq_cnt": self._seq_cnt,
            "size": self._size,
            "CDH": self._data_CDH,
            "EPS": self._data_EPS,
            "ADCS": self._data_ADCS,
            "GPS": self._data_GPS,
        }

        return heartbeat

    @classmethod
    def unpack_tm_frame_storage(self, msg):
        """
        Unpack TM frame storage received from satellite and put data
        in vectors for each onboard subsystem.
        """

        # TODO: may need to modify if we don't want 4 bytes of storage information (will 2 bytes be enough?)

        msg = list(msg)

        ############ TM Metadata ############
        self._msg_id = msg[0]
        self._seq_cnt = unpack_unsigned_short_int(msg[1:3])
        self._size = msg[3]

        # Sanity checks for message type and length
        if self._msg_id != 0x03:
            raise RuntimeError("Message is not TM storage frame")
        if self._seq_cnt != 0:
            raise RuntimeError("Message seq. count incorrect")
        # if self._size != 229: # TODO!
        #     raise RuntimeError("Message length incorrect")

        ############ CDH Fields ############
        self._data_CDH[CDH_IDX.TIME] = unpack_unsigned_long_int(msg[4:8])
        self._data_CDH[CDH_IDX.SC_STATE] = msg[8]
        self._data_CDH[CDH_IDX.SD_USAGE] = unpack_unsigned_long_int(msg[9:13])
        self._data_CDH[CDH_IDX.CURRENT_RAM_USAGE] = msg[13]
        self._data_CDH[CDH_IDX.REBOOT_COUNT] = msg[14]
        self._data_CDH[CDH_IDX.WATCHDOG_TIMER] = msg[15]
        self._data_CDH[CDH_IDX.HAL_BITFLAGS] = msg[16]
        self._data_CDH[CDH_IDX.DETUMBLING_ERROR_FLAG] = msg[17]

        ############ Total Storage Field ############
        self._data_STORAGE[STORAGE_IDX.TOTAL] = msg[18:22]

        ############ CDH Storage Field ############
        self._data_STORAGE[STORAGE_IDX.CDH_NUM_FILES] = msg[22:26]
        self._data_STORAGE[STORAGE_IDX.CDH_DIR_SIZE] = msg[26:30]

        ############ EPS Storage Field ############
        self._data_STORAGE[STORAGE_IDX.EPS_DIR_SIZE] = msg[30:34]
        self._data_STORAGE[STORAGE_IDX.EPS_DIR_SIZE] = msg[34:38]

        ############ ADCS Storage Field ############
        self._data_STORAGE[STORAGE_IDX.ADCS_DIR_SIZE] = msg[38:42]
        self._data_STORAGE[STORAGE_IDX.ADCS_DIR_SIZE] = msg[42:46]

        ############ COMMS Storage Field ############
        self._data_STORAGE[STORAGE_IDX.COMMS_DIR_SIZE] = msg[46:50]
        self._data_STORAGE[STORAGE_IDX.COMMS_DIR_SIZE] = msg[50:54]

        ############ GPS Storage Field ############
        self._data_STORAGE[STORAGE_IDX.GPS_DIR_SIZE] = msg[54:58]
        self._data_STORAGE[STORAGE_IDX.GPS_DIR_SIZE] = msg[58:62]

        ############ PAYLOAD Storage Field ############
        self._data_STORAGE[STORAGE_IDX.PAYLOAD_DIR_SIZE] = msg[62:66]
        self._data_STORAGE[STORAGE_IDX.PAYLOAD_DIR_SIZE] = msg[66:70]

        ############ THERMAL Storage Field ############
        self._data_STORAGE[STORAGE_IDX.THERMAL_DIR_SIZE] = msg[70:74]
        self._data_STORAGE[STORAGE_IDX.THERMAL_DIR_SIZE] = msg[74:78]

        ############ COMMAND Storage Field ############
        self._data_STORAGE[STORAGE_IDX.COMMAND_DIR_SIZE] = msg[78:82]
        self._data_STORAGE[STORAGE_IDX.COMMAND_DIR_SIZE] = msg[82:86]

        ############ IMG Storage Field ############
        self._data_STORAGE[STORAGE_IDX.IMG_DIR_SIZE] = msg[86:90]
        self._data_STORAGE[STORAGE_IDX.IMG_DIR_SIZE] = msg[90:94]

        tm_storage = {
            "msg_id": self._msg_id,
            "seq_cnt": self._seq_cnt,
            "size": self._size,
            "CDH": self._data_CDH,
            "total_usage": self._data_STORAGE[STORAGE_IDX.TOTAL],
            "CDH_storage": {
                "CDH_num_files": self._data_STORAGE[STORAGE_IDX.CDH_NUM_FILES],
                "CDH_dir_size": self._data_STORAGE[STORAGE_IDX.CDH_DIR_SIZE],
            },
            "EPS_storage": {
                "EPS_num_files": self._data_STORAGE[STORAGE_IDX.EPS_NUM_FILES],
                "EPS_dir_size": self._data_STORAGE[STORAGE_IDX.EPS_DIR_SIZE],
            },
            "ADCS_storage": {
                "ADCS_num_files": self._data_STORAGE[STORAGE_IDX.ADCS_NUM_FILES],
                "ADCS_dir_size": self._data_STORAGE[STORAGE_IDX.ADCS_DIR_SIZE],
            },
            "COMMS_storage": {
                "COMMS_num_files": self._data_STORAGE[STORAGE_IDX.COMMS_NUM_FILES],
                "COMMS_dir_size": self._data_STORAGE[STORAGE_IDX.COMMS_DIR_SIZE],
            },
            "GPS_storage": {
                "GPS_num_files": self._data_STORAGE[STORAGE_IDX.GPS_NUM_FILES],
                "GPS_dir_size": self._data_STORAGE[STORAGE_IDX.GPS_DIR_SIZE],
            },
            "PAYLOAD_storage": {
                "PAYLOAD_num_files": self._data_STORAGE[STORAGE_IDX.PAYLOAD_NUM_FILES],
                "PAYLOAD_dir_size": self._data_STORAGE[STORAGE_IDX.PAYLOAD_DIR_SIZE],
            },
            "THERMAL_storage": {
                "THERMAL_num_files": self._data_STORAGE[STORAGE_IDX.THERMAL_NUM_FILES],
                "THERMAL_dir_size": self._data_STORAGE[STORAGE_IDX.THERMAL_DIR_SIZE],
            },
            "COMMAND_storage": {
                "COMMAND_num_files": self._data_STORAGE[STORAGE_IDX.COMMAND_NUM_FILES],
                "COMMAND_dir_size": self._data_STORAGE[STORAGE_IDX.COMMAND_DIR_SIZE],
            },
            "IMG_storage": {
                "IMG_num_files": self._data_STORAGE[STORAGE_IDX.IMG_NUM_FILES],
                "IMG_dir_size": self._data_STORAGE[STORAGE_IDX.IMG_DIR_SIZE],
            },
        }

        return tm_storage

    @classmethod
    def unpack_tm_frame_HAL(self, msg):
        """
        Unpack TM frame HAL received from satellite and put data
        in vectors for each onboard subsystem.
        """

        msg = list(msg)

        ############ TM Metadata ############
        self._msg_id = msg[0]
        self._seq_cnt = unpack_unsigned_short_int(msg[1:3])
        self._size = msg[3]

        if self._msg_id != 0x03:
            raise RuntimeError("Message is not TM HAL frame")
        if self._seq_cnt != 0:
            raise RuntimeError("Message seq. count incorrect")

        ############ CDH Fields ############
        self._data_CDH[CDH_IDX.TIME] = unpack_unsigned_long_int(msg[4:8])
        self._data_CDH[CDH_IDX.SC_STATE] = msg[8]
        self._data_CDH[CDH_IDX.SD_USAGE] = unpack_unsigned_long_int(msg[9:13])
        self._data_CDH[CDH_IDX.CURRENT_RAM_USAGE] = msg[13]
        self._data_CDH[CDH_IDX.REBOOT_COUNT] = msg[14]
        self._data_CDH[CDH_IDX.WATCHDOG_TIMER] = msg[15]
        self._data_CDH[CDH_IDX.HAL_BITFLAGS] = msg[16]
        self._data_CDH[CDH_IDX.DETUMBLING_ERROR_FLAG] = msg[17]

        # TODO: Remove temp debugging
        print()
        print("Metadata (ID, SQ_CNT, LEN):", self._msg_id, self._seq_cnt, self._size)
        print("CDH Data:", self._data_CDH)

        tm_HAL = {
            "msg_id": self._msg_id,
            "seq_cnt": self._seq_cnt,
            "size": self._size,
            "CDH": self._data_CDH,
        }

        return tm_HAL

    @classmethod
    def unpack_frame(self, msg_id, msg):
        """
        Parses messages received from SC and dynamically unpacks it into a JSON format
        to store into database.

        Arguments:
            msg_id: the id of the message
            msg: the list of bits received

        Returns:
        Parsed data in the form of a dictionary (JSON)
        """

        # get the format and data types for that message
        data_format = DATA_FORMATS[msg_id]
        print(f"MSG_ID = {msg_id}")
        msg = msg[4:]

        parsed_data = {}
        offset = 0  # This is where we start reading from the first byte
        print(f"MSG Size = {self.rx_msg_size}")

        for subsystem, fields in data_format.items():
            parsed_data[subsystem] = {}

            # Create struct format string dynamically by computing size and getting the format strings
            format_string = "="+"".join([field[1] for field in fields])
            print(f"{format_string}")
            size = struct.calcsize(format_string)
            print(f"Offset[{offset}:{offset+size}], SIZE = {size}")
            unpacked_values = struct.unpack(format_string, msg[offset : offset + size])

            # Map unpacked values to field names for each subsystem
            for i, (field_name, _) in enumerate(fields):
                parsed_data[subsystem][field_name] = unpacked_values[i]

            offset += size  # Move offset forward

        print(parsed_data)
        return parsed_data


    @classmethod
    def unpack_message_header(self):
        # Get the current time
        current_time = datetime.datetime.now()
        # Format the current time
        formatted_time = current_time.strftime("%Y-%m-%d_%H-%M-%S\n")
        formatted_time = formatted_time.encode("utf-8")

        # Unpack RX message header
        self.rx_src_id = int.from_bytes((self.rx_message[0:1]), byteorder="big")
        self.rx_dst_id = int.from_bytes((self.rx_message[1:2]), byteorder="big")
        self.rx_message = self.rx_message[2:]

        # TODO: Error checking based on source header
        print("Source Header:", self.rx_src_id, self.rx_dst_id)
        
        # Unpack message header
        self.rx_msg_id = int.from_bytes((self.rx_message[0:1]), byteorder="big")
        self.rx_msg_sq = int.from_bytes(self.rx_message[1:3], byteorder="big")
        self.rx_msg_size = int.from_bytes(self.rx_message[3:4], byteorder="big")