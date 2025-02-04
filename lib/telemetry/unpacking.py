"""
GS Telemetry Unpacker
"""

from lib.telemetry.constants import *
from lib.telemetry.helpers import *

CDH_NUM = 8
EPS_NUM = 40
ADCS_NUM = 32
GPS_NUM = 21
THERMAL_NUM = 4


class TelemetryUnpacker:
    _msg_id = 0
    _seq_cnt = 0
    _size = 0

    _data_CDH = [0] * CDH_NUM
    _data_EPS = [0] * EPS_NUM
    _data_ADCS = [0] * ADCS_NUM
    _data_GPS = [0] * GPS_NUM
    _data_THERMAL = [0] * THERMAL_NUM

    @classmethod
    def unpack_tm_frame(self, msg):
        """
        Unpack TM frame received from satellite and put data
        in vectors for each onboard subsystem.
        """

        msg = list(msg)

        ############ TM Metadata ############
        self._msg_id = msg[0]
        self._seq_cnt = unpack_unsigned_short_int(msg[1:3])
        self._size = msg[3]

        # Sanity checks for message type and length
        if self._msg_id != 0x01:
            raise RuntimeError("Message is not TM frame")
        if self._seq_cnt != 0:
            raise RuntimeError("Message seq. count incorrect")
        if self._size != 229:
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
        self._data_THERMAL[THERMAL_IDX.TIME_THERMAL] = self._data_CDH[CDH_IDX.TIME]

        ############ EPS Fields ############
        self._data_EPS[EPS_IDX.MAINBOARD_VOLTAGE] = unpack_signed_short_int(msg[18:20])
        self._data_EPS[EPS_IDX.MAINBOARD_CURRENT] = unpack_signed_short_int(msg[20:22])

        self._data_EPS[EPS_IDX.BATTERY_PACK_REPORTED_CAPACITY] = msg[22]
        self._data_EPS[EPS_IDX.BATTERY_PACK_CURRENT] = unpack_signed_short_int(
            msg[23:25]
        )
        self._data_EPS[EPS_IDX.BATTERY_PACK_VOLTAGE] = unpack_signed_short_int(
            msg[27:29]
        )
        self._data_EPS[EPS_IDX.BATTERY_PACK_MIDPOINT_VOLTAGE] = unpack_signed_short_int(
            msg[29:31]
        )
        self._data_EPS[EPS_IDX.BATTERY_PACK_TTE] = unpack_unsigned_long_int(msg[31:35])
        self._data_EPS[EPS_IDX.BATTERY_PACK_TTF] = unpack_unsigned_long_int(msg[35:39])

        self._data_EPS[EPS_IDX.XP_COIL_VOLTAGE] = unpack_signed_short_int(msg[39:41])
        self._data_EPS[EPS_IDX.XP_COIL_CURRENT] = unpack_signed_short_int(msg[41:43])
        self._data_EPS[EPS_IDX.XM_COIL_VOLTAGE] = unpack_signed_short_int(msg[43:45])
        self._data_EPS[EPS_IDX.XM_COIL_CURRENT] = unpack_signed_short_int(msg[45:47])

        self._data_EPS[EPS_IDX.YP_COIL_VOLTAGE] = unpack_signed_short_int(msg[47:49])
        self._data_EPS[EPS_IDX.YP_COIL_CURRENT] = unpack_signed_short_int(msg[49:51])
        self._data_EPS[EPS_IDX.YM_COIL_VOLTAGE] = unpack_signed_short_int(msg[51:53])
        self._data_EPS[EPS_IDX.YM_COIL_CURRENT] = unpack_signed_short_int(msg[53:55])

        self._data_EPS[EPS_IDX.ZP_COIL_VOLTAGE] = unpack_signed_short_int(msg[55:57])
        self._data_EPS[EPS_IDX.ZP_COIL_CURRENT] = unpack_signed_short_int(msg[57:59])
        self._data_EPS[EPS_IDX.ZM_COIL_VOLTAGE] = unpack_signed_short_int(msg[59:61])
        self._data_EPS[EPS_IDX.ZM_COIL_CURRENT] = unpack_signed_short_int(msg[61:63])

        self._data_EPS[EPS_IDX.JETSON_INPUT_VOLTAGE] = unpack_signed_short_int(
            msg[63:65]
        )
        self._data_EPS[EPS_IDX.JETSON_INPUT_CURRENT] = unpack_signed_short_int(
            msg[65:67]
        )

        self._data_EPS[EPS_IDX.RF_LDO_OUTPUT_VOLTAGE] = unpack_signed_short_int(
            msg[67:69]
        )
        self._data_EPS[EPS_IDX.RF_LDO_OUTPUT_CURRENT] = unpack_signed_short_int(
            msg[69:71]
        )

        self._data_EPS[EPS_IDX.GPS_VOLTAGE] = unpack_signed_short_int(msg[71:73])
        self._data_EPS[EPS_IDX.GPS_CURRENT] = unpack_signed_short_int(msg[73:75])

        self._data_EPS[EPS_IDX.XP_SOLAR_CHARGE_VOLTAGE] = unpack_signed_short_int(
            msg[75:77]
        )
        self._data_EPS[EPS_IDX.XP_SOLAR_CHARGE_CURRENT] = unpack_signed_short_int(
            msg[77:79]
        )
        self._data_EPS[EPS_IDX.XM_SOLAR_CHARGE_VOLTAGE] = unpack_signed_short_int(
            msg[79:81]
        )
        self._data_EPS[EPS_IDX.XM_SOLAR_CHARGE_CURRENT] = unpack_signed_short_int(
            msg[81:83]
        )

        self._data_EPS[EPS_IDX.YP_SOLAR_CHARGE_VOLTAGE] = unpack_signed_short_int(
            msg[83:85]
        )
        self._data_EPS[EPS_IDX.YP_SOLAR_CHARGE_CURRENT] = unpack_signed_short_int(
            msg[85:87]
        )
        self._data_EPS[EPS_IDX.YM_SOLAR_CHARGE_VOLTAGE] = unpack_signed_short_int(
            msg[87:89]
        )
        self._data_EPS[EPS_IDX.YM_SOLAR_CHARGE_CURRENT] = unpack_signed_short_int(
            msg[89:91]
        )

        self._data_EPS[EPS_IDX.ZP_SOLAR_CHARGE_VOLTAGE] = unpack_signed_short_int(
            msg[91:93]
        )
        self._data_EPS[EPS_IDX.ZP_SOLAR_CHARGE_CURRENT] = unpack_signed_short_int(
            msg[93:95]
        )
        self._data_EPS[EPS_IDX.ZM_SOLAR_CHARGE_VOLTAGE] = unpack_signed_short_int(
            msg[95:97]
        )
        self._data_EPS[EPS_IDX.ZM_SOLAR_CHARGE_CURRENT] = unpack_signed_short_int(
            msg[97:99]
        )

        ############ ADCS Fields ############
        self._data_ADCS[ADCS_IDX.MODE] = msg[99]

        self._data_ADCS[ADCS_IDX.GYRO_X] = convert_fixed_point_to_float_hp(msg[100:104])
        self._data_ADCS[ADCS_IDX.GYRO_Y] = convert_fixed_point_to_float_hp(msg[104:108])
        self._data_ADCS[ADCS_IDX.GYRO_Z] = convert_fixed_point_to_float_hp(msg[108:112])

        self._data_ADCS[ADCS_IDX.MAG_X] = convert_fixed_point_to_float_hp(msg[112:116])
        self._data_ADCS[ADCS_IDX.MAG_Y] = convert_fixed_point_to_float_hp(msg[116:120])
        self._data_ADCS[ADCS_IDX.MAG_Z] = convert_fixed_point_to_float_hp(msg[120:124])

        self._data_ADCS[ADCS_IDX.SUN_STATUS] = msg[124]

        self._data_ADCS[ADCS_IDX.SUN_VEC_X] = convert_fixed_point_to_float_hp(
            msg[125:129]
        )
        self._data_ADCS[ADCS_IDX.SUN_VEC_Y] = convert_fixed_point_to_float_hp(
            msg[129:133]
        )
        self._data_ADCS[ADCS_IDX.SUN_VEC_Z] = convert_fixed_point_to_float_hp(
            msg[133:137]
        )

        self._data_ADCS[ADCS_IDX.ECLIPSE] = msg[137]

        self._data_ADCS[ADCS_IDX.LIGHT_SENSOR_XP] = unpack_signed_short_int(
            msg[138:140]
        )
        self._data_ADCS[ADCS_IDX.LIGHT_SENSOR_XM] = unpack_signed_short_int(
            msg[140:142]
        )
        self._data_ADCS[ADCS_IDX.LIGHT_SENSOR_YP] = unpack_signed_short_int(
            msg[142:144]
        )
        self._data_ADCS[ADCS_IDX.LIGHT_SENSOR_YM] = unpack_signed_short_int(
            msg[144:146]
        )
        self._data_ADCS[ADCS_IDX.LIGHT_SENSOR_ZP1] = unpack_signed_short_int(
            msg[146:148]
        )
        self._data_ADCS[ADCS_IDX.LIGHT_SENSOR_ZP2] = unpack_signed_short_int(
            msg[148:150]
        )
        self._data_ADCS[ADCS_IDX.LIGHT_SENSOR_ZP3] = unpack_signed_short_int(
            msg[150:152]
        )
        self._data_ADCS[ADCS_IDX.LIGHT_SENSOR_ZP4] = unpack_signed_short_int(
            msg[152:154]
        )
        self._data_ADCS[ADCS_IDX.LIGHT_SENSOR_ZM] = unpack_signed_short_int(
            msg[154:156]
        )

        self._data_ADCS[ADCS_IDX.XP_COIL_STATUS] = msg[156]
        self._data_ADCS[ADCS_IDX.XM_COIL_STATUS] = msg[157]
        self._data_ADCS[ADCS_IDX.YP_COIL_STATUS] = msg[158]
        self._data_ADCS[ADCS_IDX.YM_COIL_STATUS] = msg[159]
        self._data_ADCS[ADCS_IDX.ZP_COIL_STATUS] = msg[160]
        self._data_ADCS[ADCS_IDX.ZM_COIL_STATUS] = msg[161]

        self._data_ADCS[ADCS_IDX.COARSE_ATTITUDE_QW] = convert_fixed_point_to_float_hp(
            msg[162:166]
        )
        self._data_ADCS[ADCS_IDX.COARSE_ATTITUDE_QX] = convert_fixed_point_to_float_hp(
            msg[166:170]
        )
        self._data_ADCS[ADCS_IDX.COARSE_ATTITUDE_QY] = convert_fixed_point_to_float_hp(
            msg[170:174]
        )
        self._data_ADCS[ADCS_IDX.COARSE_ATTITUDE_QZ] = convert_fixed_point_to_float_hp(
            msg[174:178]
        )

        ############ GPS Fields ############
        self._data_GPS[GPS_IDX.GPS_MESSAGE_ID] = msg[178]
        self._data_GPS[GPS_IDX.GPS_FIX_MODE] = msg[179]
        self._data_GPS[GPS_IDX.GPS_NUMBER_OF_SV] = msg[180]

        self._data_GPS[GPS_IDX.GPS_GNSS_WEEK] = unpack_unsigned_short_int(msg[181:183])
        self._data_GPS[GPS_IDX.GPS_GNSS_TOW] = unpack_unsigned_long_int(msg[183:187])

        self._data_GPS[GPS_IDX.GPS_LATITUDE] = unpack_signed_long_int(msg[187:191])
        self._data_GPS[GPS_IDX.GPS_LONGITUDE] = unpack_signed_long_int(msg[191:195])
        self._data_GPS[GPS_IDX.GPS_ELLIPSOID_ALT] = unpack_signed_long_int(msg[195:199])
        self._data_GPS[GPS_IDX.GPS_MEAN_SEA_LVL_ALT] = unpack_signed_long_int(
            msg[199:203]
        )

        self._data_GPS[GPS_IDX.GPS_ECEF_X] = unpack_signed_long_int(msg[203:207])
        self._data_GPS[GPS_IDX.GPS_ECEF_Y] = unpack_signed_long_int(msg[207:211])
        self._data_GPS[GPS_IDX.GPS_ECEF_Z] = unpack_signed_long_int(msg[211:215])
        self._data_GPS[GPS_IDX.GPS_ECEF_VX] = unpack_signed_long_int(msg[215:219])
        self._data_GPS[GPS_IDX.GPS_ECEF_VY] = unpack_signed_long_int(msg[219:223])
        self._data_GPS[GPS_IDX.GPS_ECEF_VZ] = unpack_signed_long_int(msg[223:227])

        ############ Thermal Fields ############
        self._data_THERMAL[THERMAL_IDX.IMU_TEMPERATURE] = (
            unpack_unsigned_short_int(msg[227:229]) / 100
        )
        self._data_THERMAL[THERMAL_IDX.CPU_TEMPERATURE] = (
            unpack_unsigned_short_int(msg[229:231]) / 100
        )
        self._data_THERMAL[
            THERMAL_IDX.BATTERY_PACK_TEMPERATURE
        ] = unpack_unsigned_short_int(msg[231:233])

        # TODO: Remove temp debugging
        print()
        print("Metadata (ID, SQ_CNT, LEN):", self._msg_id, self._seq_cnt, self._size)
        print("CDH Data:", self._data_CDH)
        print("EPS Data:", self._data_EPS)
        print("ADCS Data:", self._data_ADCS)
        print("GPS Data:", self._data_GPS)
        print("THERMAL Data:", self._data_THERMAL)
        print()
