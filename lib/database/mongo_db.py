from pymongo.mongo_client import MongoClient

from lib.constants import Message_IDS
from lib.passwords import MONGO_CONNECTION_STRING


class Database:
    def __init__(self) -> None:
        self.client = MongoClient(MONGO_CONNECTION_STRING)

    def upload_data(self, type, time, data):
        if type == Message_IDS.SAT_HEARTBEAT_SUN:
            self.upload_sun(time, data)
        elif type == Message_IDS.SAT_HEARTBEAT_IMU:
            self.upload_imu(time, data)
        elif type == Message_IDS.SAT_HEARTBEAT_BATT:
            self.upload_batt(time, data)

    def upload_sun(self, time, data):
        (sun_x, sun_y, sun_z) = data
        upload = {
            "time": time,
            "x": sun_x,
            "y": sun_y,
            "z": sun_z,
        }
        try:
            database = self.client["heartbeats"]
            collection = database["sun"]
            collection.insert_one(upload)
        except Exception as e:
            print(f"Could not upload sun heartbeat: {e}")

    def upload_batt(self, time, data):
        (batt_soc, current, boot_count) = data
        upload = {
            "time": time,
            "battery_soc": batt_soc,
            "current": current,
            "boot_counter": boot_count,
        }
        try:
            database = self.client["heartbeats"]
            collection = database["battery"]
            collection.insert_one(upload)
        except Exception as e:
            print(f"Could not upload battery heartbeat: {e}")

    def upload_imu(self, time, data):
        (mag_x, mag_y, mag_z, gyro_x, gyro_y, gyro_z) = data
        upload = {
            "time": time,
            "mag_x": mag_x,
            "mag_y": mag_y,
            "mag_z": mag_z,
            "gyro_x": gyro_x,
            "gyro_y": gyro_y,
            "gyro_z": gyro_z,
        }
        try:
            database = self.client["heartbeats"]
            collection = database["imu"]
            collection.insert_one(upload)
        except Exception as e:
            print(f"Could not upload imu heartbeat: {e}")
