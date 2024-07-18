import datetime

from lib.argus_lora import LoRa, ModemConfig
from lib.constants import Message_IDS
from lib.radiohead import RadioHead


def unpack_header(msg):
    ack_req = (int.from_bytes((msg.message[0:1]), byteorder='big') & 0b10000000) >> 7
    message_ID = int.from_bytes((msg.message[0:1]), byteorder='big') & 0b01111111
    message_sequence_count = int.from_bytes(msg.message[1:3], byteorder='big')
    message_size = int.from_bytes(msg.message[3:4], byteorder='big')
    return ack_req, message_ID, message_sequence_count, message_size


def unpack_message(msg):
    # Get the current time
    current_time = datetime.datetime.now()
    # Format the current time
    formatted_time = current_time.strftime("%Y-%m-%d_%H-%M-%S\n")
    formatted_time = formatted_time.encode('utf-8')

    header_info = (f"Header To: {msg.header_to}," +
                   f"Header From: {msg.header_from}," +
                   f"Header ID: {msg.header_id}," +
                   f"Header Flags: {msg.header_flags}," +
                   f"RSSI: {msg.rssi}," +
                   f"SNR: {msg.snr}\n")
    header_info = header_info.encode('utf-8')
    payload = f"Payload: {msg.message}\n\n"
    payload = payload.encode('utf-8')
    (ack, msg_id, msg_seq_count, msg_size) = unpack_header(msg)
    system_status = f"{msg.message[5]}, {msg.message[6]}"
    data = list(msg.message[6:])
    print(f"header info: {header_info}")
    print(f"system status: {system_status}")
    if msg_id == Message_IDS.SAT_HEARTBEAT_BATT:
        print("battery heartbeat")
        """
        byte 0: batt_soc
        byte 1: current msb
        byte 2: current lsb
        byte 3: boot count
        byte 4: time high
        byte 5: time mid high
        byte 6: time mid low
        byte 7: time low
        """
        batt_soc: int = data[0]
        current: int = data[1] << 8 | data[2]
        boot_count: int = data[3]
        time: int = ((data[4] & 0xff) << 24 |
                     (data[5] & 0xff) << 16 |
                     (data[6] & 0xff) << 8 |
                     (data[7] & 0xff))
        print(f"battery soc: {batt_soc}")
        print(f"current: {current}")
        print(f"boot count: {boot_count}")
        print(f"time: {time}")
        return msg_id, time, (batt_soc, current, boot_count)
    elif msg_id == Message_IDS.SAT_HEARTBEAT_SUN:
        print("sun heartbeat")
        """
        byte 0-4: sun vector x
        byte 4-8: sun vector y
        byte 8-12: sun vector 1
        bytes 12-16: time
        """
        sun_vec_x = convert_floating_point_hp(data[0:4])
        sun_vec_y = convert_floating_point_hp(data[4:8])
        sun_vec_z = convert_floating_point_hp(data[8:12])

        time: int = ((data[12] & 0xff) << 24 |
                     (data[13] & 0xff) << 16 |
                     (data[14] & 0xff) << 8 |
                     (data[15] & 0xff))
        print(f"sun vector: ({sun_vec_x}, {sun_vec_y}, {sun_vec_z})")
        print(f"time: {time}")
        return msg_id, time, (sun_vec_x, sun_vec_y, sun_vec_z)
    elif msg_id == Message_IDS.SAT_HEARTBEAT_IMU:
        print("imu heartbeat")
        """
        byte 0-4: mag x
        byte 4-8: mag y
        byte 8-12: mag z
        byte 12-16: gyro x
        byte 16-20: gyro y
        byte 20-24: gyro z
        byte 24-28: time
        """
        mag_x = convert_floating_point(data[0:4])
        mag_y = convert_floating_point(data[4:8])
        mag_z = convert_floating_point(data[8:12])

        gyro_x = convert_floating_point(data[12:16])
        gyro_y = convert_floating_point(data[16:20])
        gyro_z = convert_floating_point(data[20:24])

        time: int = ((data[24] & 0xff) << 24 |
                     (data[25] & 0xff) << 16 |
                     (data[26] & 0xff) << 8 |
                     (data[27] & 0xff))

        print(f"mag: ({mag_x}, {mag_y}, {mag_z})")
        print(f"gyro: ({gyro_x}, {gyro_y}, {gyro_z})")
        print(f"time: {time}")
        return msg_id, time, (mag_x, mag_y, mag_z, gyro_x, gyro_y, gyro_z)


def convert_floating_point(message_list) -> float:
    """
    :param message_list: Byte list to convert to floating
    :return: value as floating point

    Convert FP value back to floating point
    Range: [-32767.9999], 32767.9999]
    """
    val = 0
    neg_bit_flag = 0

    # Check -ve, extract LSB bytes for val, combine
    if ((message_list[0] >> 7) == 1):
        message_list[0] &= 0x7F
        neg_bit_flag = 1

    # Extract bytes for val, combine
    val += (message_list[0] << 8) + message_list[1]
    val += ((message_list[2] << 8) + message_list[3]) / 65536
    if (neg_bit_flag == 1):
        val = -1 * val

    return val


def convert_floating_point_hp(message_list) -> float:
    """
    :param message_list: Byte list to convert to floating
    :return: value as floating point

    Convert HP FP value back to floating point
    Range: [-128.9999999, 128.9999999]
    """
    val = 0
    neg_bit_flag = 0

    # Check -ve, extract LSB bytes for val, combine
    if ((message_list[0] >> 7) == 1):
        message_list[0] &= 0x7F
        neg_bit_flag = 1

    # Extract bytes for val, combine
    val += message_list[0]
    val += ((message_list[1] << 16) + (message_list[2] << 8) + message_list[3] + 1) / 16777216
    if (neg_bit_flag == 1):
        val = -1 * val

    return val


def initialize_radio() -> RadioHead:
    CHANNEL = 0
    INTERRUPT = 19
    ADDRESS = 25
    FREQUENCY = 433
    TX_POWER = 14
    MODEM_CONFIG = ModemConfig.Bw125Cr45Sf128
    RECEIVE_ALL = False
    ACKS = False
    CRYTPO = None

    # initialize radio instance
    radio = LoRa(
        CHANNEL,
        INTERRUPT,
        ADDRESS,
        modem_config=MODEM_CONFIG,
        freq=FREQUENCY,
        tx_power=TX_POWER,
        receive_all=RECEIVE_ALL,
        acks=ACKS,
        crypto=CRYTPO)
    
    # RadioHead wrapper class that overwrites on_recv and adds a receive method
    radiohead = RadioHead(radio, 15)
    return radiohead
