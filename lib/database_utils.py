from influxdb import Database


def initialize_database(bucket, point):
    return Database(bucket=bucket, point=point)
