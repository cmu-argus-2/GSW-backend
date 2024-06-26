CREATE DATABASE heartbeats;
use heartbeats;
CREATE TABLE sun (time INT, x FLOAT, y FLOAT, z FLOAT);
CREATE TABLE battery (time INT, batt_soc INT, current INT, boot_count INT);
CREATE TABLE imu (time INT, mag_x FLOAT, mag_y FLOAT, mag_z FLOAT, gyro_x FLOAT, gyro_y FLOAT, gyro_z FLOAT);