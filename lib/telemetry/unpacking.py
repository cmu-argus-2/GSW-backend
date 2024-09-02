"""
GS Telemetry Unpacker
"""

from lib.telemetry.constants import *
from lib.telemetry.helpers import * 

MOCK_FRAME = bytearray(b'\x01\x00\x01\xf5f\xc8\xea\x1c\x01\x00\x00\x00\x00\x0c\x00\x00\x00\x1d\xb0\x00d\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x04\x00\x00\x00\x03\x00\x00\x00\x01\x00\x00\x00\x00\x80|\xf0\x93\x00\xdd?Y\x00\x1f<$\x00\x00Z\x12\xc0!4\x00\x14\x00\x00\x00\x00\x00\x00\x00\x00\x04\xb0\x00\x00\x00\x00\x00\x00\x00\xf1\x0c{\x80\x12\xfdC\x00\x1f"\xdf\x00N\x1c\x97\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01p\xadz\xfc"\x8c;\x01L\xca\x1c\x03\xf5\t\xfe\x01y|J\xfb\x9b\xa8@\x07\xd0\x0e8\x00\x00\x00\x00\x00\x00\x00\x00\x00')

CDH_NUM  = 7
EPS_NUM  = 42
ADCS_NUM = 37
GPS_NUM  = 21
THERMAL_NUM = 4

class TelemetryUnpacker:
    _msg_id  = 0
    _seq_cnt = 0
    _size = 0
    
    _data_CDH  = [0] * CDH_NUM
    _data_EPS  = [0] * EPS_NUM
    _data_ADCS = [0] * ADCS_NUM
    _data_GPS  = [0] * GPS_NUM
    _data_THERMAL = [0] * THERMAL_NUM

    @classmethod
    def unpack_tm_frame(self, msg):
        """
        Unpack TM frame received from satellite and put data 
        in vectors for each onboard subsystem.
        """

        msg = list(msg)

        ############ TM Metadata ############
        self._msg_id  = msg[0]
        self._seq_cnt = unpack_unsigned_short_int(msg[1:3])
        self._size = msg[3]

        # Sanity checks for message type and length
        if(self._msg_id != 0x01):
            raise RuntimeError("Message is not TM frame")
        if(self._seq_cnt != 1):
            raise RuntimeError("Message seq. count incorrect")
        if(self._size != 245):
            raise RuntimeError("Message length incorrect")

        ############ CDH Fields ############
        self._data_CDH[CDH_IDX.TIME] = unpack_unsigned_long_int(msg[4:8])
        self._data_CDH[CDH_IDX.SC_STATE] = msg[8]
        self._data_CDH[CDH_IDX.SD_USAGE] = unpack_unsigned_long_int(msg[9:13])
        self._data_CDH[CDH_IDX.CURRENT_RAM_USAGE] = msg[13]
        self._data_CDH[CDH_IDX.REBOOT_COUNT] = msg[14]
        self._data_CDH[CDH_IDX.WATCHDOG_TIMER] = msg[15]
        self._data_CDH[CDH_IDX.HAL_BITFLAGS] = msg[16]

        # CDH time for all data vectors 
        self._data_EPS[EPS_IDX.TIME_EPS] = self._data_CDH[CDH_IDX.TIME]
        self._data_ADCS[ADCS_IDX.TIME_ADCS] = self._data_CDH[CDH_IDX.TIME]
        self._data_GPS[GPS_IDX.TIME_GPS] = self._data_CDH[CDH_IDX.TIME]
        self._data_THERMAL[THERMAL_IDX.TIME_THERMAL] = self._data_CDH[CDH_IDX.TIME]

        ############ EPS Fields ############
        self._data_EPS[EPS_IDX.MAINBOARD_VOLTAGE] = unpack_signed_short_int(msg[17:19])
        self._data_EPS[EPS_IDX.MAINBOARD_CURRENT] = unpack_signed_short_int(msg[19:21])

        self._data_EPS[EPS_IDX.BATTERY_PACK_REPORTED_CAPACITY] = msg[21]
        self._data_EPS[EPS_IDX.BATTERY_PACK_CURRENT] = unpack_signed_short_int(msg[22:24])
        self._data_EPS[EPS_IDX.BATTERY_PACK_VOLTAGE] = unpack_signed_short_int(msg[26:28])
        self._data_EPS[EPS_IDX.BATTERY_PACK_MIDPOINT_VOLTAGE] = unpack_signed_short_int(msg[28:30])
        self._data_EPS[EPS_IDX.BATTERY_CYCLES] = unpack_signed_short_int(msg[30:32])
        self._data_EPS[EPS_IDX.BATTERY_PACK_TTE] = unpack_signed_short_int(msg[32:34])
        self._data_EPS[EPS_IDX.BATTERY_PACK_TTF] = unpack_signed_short_int(msg[34:36])
        self._data_EPS[EPS_IDX.BATTERY_TIME_SINCE_POWER_UP] = unpack_signed_short_int(msg[36:38])

        self._data_EPS[EPS_IDX.XP_COIL_VOLTAGE] = unpack_signed_short_int(msg[38:40])
        self._data_EPS[EPS_IDX.XP_COIL_CURRENT] = unpack_signed_short_int(msg[40:42])
        self._data_EPS[EPS_IDX.XM_COIL_VOLTAGE] = unpack_signed_short_int(msg[42:44])
        self._data_EPS[EPS_IDX.XM_COIL_CURRENT] = unpack_signed_short_int(msg[44:46])

        self._data_EPS[EPS_IDX.YP_COIL_VOLTAGE] = unpack_signed_short_int(msg[46:48])
        self._data_EPS[EPS_IDX.YP_COIL_CURRENT] = unpack_signed_short_int(msg[48:50])
        self._data_EPS[EPS_IDX.YM_COIL_VOLTAGE] = unpack_signed_short_int(msg[50:52])
        self._data_EPS[EPS_IDX.YM_COIL_CURRENT] = unpack_signed_short_int(msg[52:54])

        self._data_EPS[EPS_IDX.ZP_COIL_VOLTAGE] = unpack_signed_short_int(msg[54:56])
        self._data_EPS[EPS_IDX.ZP_COIL_CURRENT] = unpack_signed_short_int(msg[56:58])
        self._data_EPS[EPS_IDX.ZM_COIL_VOLTAGE] = unpack_signed_short_int(msg[58:60])
        self._data_EPS[EPS_IDX.ZM_COIL_CURRENT] = unpack_signed_short_int(msg[60:62])

        self._data_EPS[EPS_IDX.JETSON_INPUT_VOLTAGE] = unpack_signed_short_int(msg[62:64])
        self._data_EPS[EPS_IDX.JETSON_INPUT_CURRENT] = unpack_signed_short_int(msg[64:66])

        self._data_EPS[EPS_IDX.RF_LDO_OUTPUT_VOLTAGE] = unpack_signed_short_int(msg[66:68])
        self._data_EPS[EPS_IDX.RF_LDO_OUTPUT_CURRENT] = unpack_signed_short_int(msg[68:70])

        self._data_EPS[EPS_IDX.GPS_VOLTAGE] = unpack_signed_short_int(msg[70:72])
        self._data_EPS[EPS_IDX.GPS_CURRENT] = unpack_signed_short_int(msg[72:74])

        self._data_EPS[EPS_IDX.XP_SOLAR_CHARGE_VOLTAGE] = unpack_signed_short_int(msg[74:76])
        self._data_EPS[EPS_IDX.XP_SOLAR_CHARGE_CURRENT] = unpack_signed_short_int(msg[76:78])
        self._data_EPS[EPS_IDX.XM_SOLAR_CHARGE_VOLTAGE] = unpack_signed_short_int(msg[78:80])
        self._data_EPS[EPS_IDX.XM_SOLAR_CHARGE_CURRENT] = unpack_signed_short_int(msg[80:82])

        self._data_EPS[EPS_IDX.YP_SOLAR_CHARGE_VOLTAGE] = unpack_signed_short_int(msg[82:84])
        self._data_EPS[EPS_IDX.YP_SOLAR_CHARGE_CURRENT] = unpack_signed_short_int(msg[84:86])
        self._data_EPS[EPS_IDX.YM_SOLAR_CHARGE_VOLTAGE] = unpack_signed_short_int(msg[86:88])
        self._data_EPS[EPS_IDX.YM_SOLAR_CHARGE_CURRENT] = unpack_signed_short_int(msg[88:90])

        self._data_EPS[EPS_IDX.ZP_SOLAR_CHARGE_VOLTAGE] = unpack_signed_short_int(msg[90:92])
        self._data_EPS[EPS_IDX.ZP_SOLAR_CHARGE_CURRENT] = unpack_signed_short_int(msg[92:94])
        self._data_EPS[EPS_IDX.ZM_SOLAR_CHARGE_VOLTAGE] = unpack_signed_short_int(msg[94:96])
        self._data_EPS[EPS_IDX.ZM_SOLAR_CHARGE_CURRENT] = unpack_signed_short_int(msg[96:98])

        ############ ADCS Fields ############
        self._data_ADCS[ADCS_IDX.ADCS_STATE] = msg[98]

        self._data_ADCS[ADCS_IDX.GYRO_X] = convert_fixed_point_to_float_hp(msg[99:103])
        self._data_ADCS[ADCS_IDX.GYRO_Y] = convert_fixed_point_to_float_hp(msg[103:107])
        self._data_ADCS[ADCS_IDX.GYRO_Z] = convert_fixed_point_to_float_hp(msg[107:111])

        self._data_ADCS[ADCS_IDX.MAG_X] = convert_fixed_point_to_float_hp(msg[111:115])
        self._data_ADCS[ADCS_IDX.MAG_Y] = convert_fixed_point_to_float_hp(msg[115:119])
        self._data_ADCS[ADCS_IDX.MAG_Z] = convert_fixed_point_to_float_hp(msg[119:123])

        self._data_ADCS[ADCS_IDX.SUN_STATUS] = msg[123]

        self._data_ADCS[ADCS_IDX.SUN_VEC_X] = convert_fixed_point_to_float_hp(msg[124:128])
        self._data_ADCS[ADCS_IDX.SUN_VEC_Y] = convert_fixed_point_to_float_hp(msg[128:132])
        self._data_ADCS[ADCS_IDX.SUN_VEC_Z] = convert_fixed_point_to_float_hp(msg[132:136])

        self._data_ADCS[ADCS_IDX.ECLIPSE] = msg[136]

        self._data_ADCS[ADCS_IDX.LIGHT_SENSOR_XP] = unpack_signed_short_int(msg[137:139])
        self._data_ADCS[ADCS_IDX.LIGHT_SENSOR_XM] = unpack_signed_short_int(msg[139:141])
        self._data_ADCS[ADCS_IDX.LIGHT_SENSOR_YP] = unpack_signed_short_int(msg[141:143])
        self._data_ADCS[ADCS_IDX.LIGHT_SENSOR_YM] = unpack_signed_short_int(msg[143:145])
        self._data_ADCS[ADCS_IDX.LIGHT_SENSOR_ZP1] = unpack_signed_short_int(msg[145:147])
        self._data_ADCS[ADCS_IDX.LIGHT_SENSOR_ZP2] = unpack_signed_short_int(msg[147:149])
        self._data_ADCS[ADCS_IDX.LIGHT_SENSOR_ZP3] = unpack_signed_short_int(msg[149:151])
        self._data_ADCS[ADCS_IDX.LIGHT_SENSOR_ZP4] = unpack_signed_short_int(msg[151:153])
        self._data_ADCS[ADCS_IDX.LIGHT_SENSOR_ZM] = unpack_signed_short_int(msg[153:155])

        self._data_ADCS[ADCS_IDX.XP_COIL_STATUS] = msg[155]
        self._data_ADCS[ADCS_IDX.XM_COIL_STATUS] = msg[156]
        self._data_ADCS[ADCS_IDX.YP_COIL_STATUS] = msg[157]
        self._data_ADCS[ADCS_IDX.YM_COIL_STATUS] = msg[158]
        self._data_ADCS[ADCS_IDX.ZP_COIL_STATUS] = msg[159]
        self._data_ADCS[ADCS_IDX.ZM_COIL_STATUS] = msg[160]

        self._data_ADCS[ADCS_IDX.COARSE_ATTITUDE_QW] = convert_fixed_point_to_float_hp(msg[161:165])
        self._data_ADCS[ADCS_IDX.COARSE_ATTITUDE_QX] = convert_fixed_point_to_float_hp(msg[165:169])
        self._data_ADCS[ADCS_IDX.COARSE_ATTITUDE_QY] = convert_fixed_point_to_float_hp(msg[169:173])
        self._data_ADCS[ADCS_IDX.COARSE_ATTITUDE_QZ] = convert_fixed_point_to_float_hp(msg[173:177])

        self._data_ADCS[ADCS_IDX.STAR_TRACKER_STATUS] = msg[177]

        self._data_ADCS[ADCS_IDX.STAR_TRACKER_ATTITUDE_QW] = convert_fixed_point_to_float_hp(msg[178:182])
        self._data_ADCS[ADCS_IDX.STAR_TRACKER_ATTITUDE_QX] = convert_fixed_point_to_float_hp(msg[182:186])
        self._data_ADCS[ADCS_IDX.STAR_TRACKER_ATTITUDE_QY] = convert_fixed_point_to_float_hp(msg[186:190])
        self._data_ADCS[ADCS_IDX.STAR_TRACKER_ATTITUDE_QZ] = convert_fixed_point_to_float_hp(msg[190:194])

        ############ GPS Fields ############
        self._data_GPS[GPS_IDX.GPS_MESSAGE_ID] = msg[194]
        self._data_GPS[GPS_IDX.GPS_FIX_MODE] = msg[195]
        self._data_GPS[GPS_IDX.GPS_NUMBER_OF_SV] = msg[196]

        self._data_GPS[GPS_IDX.GPS_GNSS_WEEK] = unpack_unsigned_short_int(msg[197:199])
        self._data_GPS[GPS_IDX.GPS_GNSS_TOW] = unpack_unsigned_long_int(msg[199:203])

        self._data_GPS[GPS_IDX.GPS_LATITUDE] = unpack_signed_long_int(msg[203:207])
        self._data_GPS[GPS_IDX.GPS_LONGITUDE] = unpack_signed_long_int(msg[207:211])
        self._data_GPS[GPS_IDX.GPS_ELLIPSOID_ALT] = unpack_signed_long_int(msg[211:215])
        self._data_GPS[GPS_IDX.GPS_MEAN_SEA_LVL_ALT] = unpack_signed_long_int(msg[215:219])
        
        self._data_GPS[GPS_IDX.GPS_ECEF_X] = unpack_signed_long_int(msg[219:223])
        self._data_GPS[GPS_IDX.GPS_ECEF_Y] = unpack_signed_long_int(msg[223:227])
        self._data_GPS[GPS_IDX.GPS_ECEF_Z] = unpack_signed_long_int(msg[227:231])
        self._data_GPS[GPS_IDX.GPS_ECEF_VX] = unpack_signed_long_int(msg[231:235])
        self._data_GPS[GPS_IDX.GPS_ECEF_VY] = unpack_signed_long_int(msg[235:239])
        self._data_GPS[GPS_IDX.GPS_ECEF_VZ] = unpack_signed_long_int(msg[239:243])

        ############ Thermal Fields ############
        self._data_THERMAL[THERMAL_IDX.IMU_TEMPERATURE] = unpack_unsigned_short_int(msg[243:245]) / 100
        self._data_THERMAL[THERMAL_IDX.CPU_TEMPERATURE] = unpack_unsigned_short_int(msg[245:247]) / 100
        self._data_THERMAL[THERMAL_IDX.BATTERY_PACK_TEMPERATURE] = unpack_unsigned_short_int(msg[247:249])

        # TODO: Remove temp debugging
        print()
        print("Metadata (ID, SQ_CNT, LEN):", self._msg_id, self._seq_cnt, self._size)
        print("CDH Data:", self._data_CDH)
        print("EPS Data:", self._data_EPS)
        print("ADCS Data:", self._data_ADCS)
        print("GPS Data:", self._data_GPS)
        print("THERMAL Data:", self._data_THERMAL)
        print()

