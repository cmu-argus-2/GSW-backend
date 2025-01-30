import os
import time

import influxdb_client
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

from lib.constants import Message_IDS
from lib.passwords import INFLUXDB_IP, INFLUXDB_ORGANIZATION, INFLUXDB_TOKEN


class Database:
    def __init__(self, bucket, point) -> None:
        self.client = influxdb_client.InfluxDBClient(
            url=INFLUXDB_IP, token=INFLUXDB_TOKEN, org=INFLUXDB_ORGANIZATION
        )
        self.bucket = bucket
        self.point = point
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)

    def upload_data(self, type, t, data):
        if type == Message_IDS.SAT_HEARTBEAT_SUN:
            self.upload_sun(t, data)
        elif type == Message_IDS.SAT_HEARTBEAT_IMU:
            self.upload_imu(t, data)
        elif type == Message_IDS.SAT_HEARTBEAT_BATT:
            self.upload_batt(t, data)

    def upload_sun(self, t, data):
        (sun_x, sun_y, sun_z) = data
        upload = {
            "sat_time": t,
            "x": sun_x,
            "y": sun_y,
            "z": sun_z,
        }
        point = Point(self.point).tag("heartbeat", "sun")
        for key in upload:
            point.field(key, upload[key])
        try:
            self.write_api.write(
                bucket=self.bucket, org=INFLUXDB_ORGANIZATION, record=point
            )
        except Exception as e:
            print(f"could not upload sun heartbeat: {e}")

    def upload_batt(self, time, data):
        (batt_soc, current, boot_count) = data
        upload = {
            "sat_time": time,
            "battery_soc": batt_soc,
            "current": current,
            "boot_counter": boot_count,
        }
        point = Point(self.point).tag("heartbeat", "battery")
        for key in upload:
            point.field(key, upload[key])
        try:
            self.write_api.write(
                bucket=self.bucket, org=INFLUXDB_ORGANIZATION, record=point
            )
        except Exception as e:
            print(f"Could not upload battery heartbeat: {e}")

    def upload_imu(self, time, data):
        (mag_x, mag_y, mag_z, gyro_x, gyro_y, gyro_z) = data
        upload = {
            "sat_time": time,
            "mag_x": mag_x,
            "mag_y": mag_y,
            "mag_z": mag_z,
            "gyro_x": gyro_x,
            "gyro_y": gyro_y,
            "gyro_z": gyro_z,
        }
        point = Point(self.point).tag("heartbeat", "imu")
        for key in upload:
            point.field(key, upload[key])
        try:
            self.write_api.write(
                bucket=self.bucket, org=INFLUXDB_ORGANIZATION, record=point
            )
        except Exception as e:
            print(f"Could not upload imu heartbeat: {e}")
