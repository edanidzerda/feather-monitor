from adafruit_bme280 import basic as adafruit_bme280
from time import time
import microcontroller
from adafruit_lc709203f import LC709203F
import json


# https://docs.influxdata.com/influxdb/cloud/write-data/developer-tools/line-protocol/
# https://docs.influxdata.com/influxdb/cloud/reference/syntax/line-protocol/#timestamp

# How much area to preserve at the beginning of sleep_memory
# Use this to store other fields like timestamp of last NTP sync
saved_data_starting_index = 50


def c_to_f(temp_c):
    return temp_c * (9 / 5) + 32


def format_line(measurement: str, field: str, value, location: str = "crawlspace_center", timestamp: int = time()):
    return '{measurement},location="{location}" {field}={value} {timestamp}\n'.format(measurement=measurement,
                                                                                      location=location,
                                                                                      field=field, value=value,
                                                                                      timestamp=timestamp)


class DeviceData:
    temperature: float
    humidity: float
    pressure: float
    battery_voltage: float
    cpu_temperature: float
    duration: int
    start_time: int

    def __init__(self, bme280: adafruit_bme280.Adafruit_BME280_I2C = None, battery_monitor: LC709203F = None,
                 duration: int = 0):
        self.duration = duration
        self.time = time()
        self.start_time = time()
        if bme280 is not None:
            self.temperature = bme280.temperature
            self.humidity = bme280.relative_humidity
            self.pressure = bme280.pressure
        # else:
        #     self.temperature = 0.0
        #     self.humidity = 0.0
        #     self.pressure = 0.0

        if battery_monitor is not None:
            self.battery_voltage = battery_monitor.cell_voltage
            self.battery_percent = battery_monitor.cell_percent
        # else:
        #     self.battery_percent = 0.0
        #     self.battery_voltage = 0.0

        try:
            self.cpu_temperature_f = c_to_f(microcontroller.cpu.temperature)
        except AttributeError:
            self.cpu_temperature_f = None

    # def print(self):
    #     # Collect the sensor data values and format the data
    #     temperature = "{:.2f}".format(bme280.temperature)
    #     temperature_f = "{:.2f}".format((bme280.temperature * (9 / 5) + 32))  # Convert C to F
    #     humidity = "{:.2f}".format(bme280.relative_humidity)
    #     pressure = "{:.2f}".format(bme280.pressure)
    #     battery_voltage = "{:.2f}".format(battery_monitor.cell_voltage)
    #     battery_percent = "{:.1f}".format(battery_monitor.cell_percent)
    #
    #     cpu_temperature_f = microcontroller.cpu.temperature * (9 / 5) + 32

    def influx_data(self):
        print("get_influx_data: self=", self.__dict__)
        data = format_line(measurement="sensor", field="humidity", value=self.humidity, timestamp=self.start_time)
        data += format_line(measurement="sensor", field="temperature", value=c_to_f(self.temperature),
                            timestamp=self.start_time)
        data += format_line(measurement="sensor", field="pressure", value=self.pressure, timestamp=self.start_time)
        data += format_line(measurement="battery", field="percent", value=self.battery_percent,
                            timestamp=self.start_time)
        data += format_line(measurement="battery", field="voltage", value=self.battery_voltage,
                            timestamp=self.start_time)
        data += format_line(measurement="device", field="measurementTime", value=self.battery_voltage,
                            timestamp=self.start_time)
        data += format_line(measurement="device", field="cpu_temperature", value=self.cpu_temperature_f,
                            timestamp=self.start_time)
        #
        #
        # data = "sensor,location=\"{0}\" humidity={1}\n".format(secrets['location'], self.humidity)
        # data += "sensor,location=\"{0}\" temperature={1}\n".format(secrets['location'], c_to_f(self.temperature))
        # data += "sensor,location=\"{0}\" pressure={1}\n".format(secrets['location'], self.pressure)
        #
        # data += "battery,location=\"{0}\" voltage={1}\n".format(secrets['location'], self.battery_voltage)
        # data += "battery,location=\"{0}\" percent={1}\n".format(secrets['location'], self.battery_percent)
        # data += "device,location=\"{0}\" measurementTime={1}\n".format(secrets['location'], self.duration)
        # data += "device,location=\"{0}\" cpu_temperature={1}\n".format(secrets['location'], self.cpu_temperature_f)
        return data


def json_decoder(dct):
    data = DeviceData()
    if "time" in dct:
        data.time = dct['time']
    if "pressure" in dct:
        data.pressure = dct['pressure']
    if "humidity" in dct:
        data.humidity = dct['humidity']
    if "temperature" in dct:
        data.temperature = dct['humidity']
    if "battery_percent" in dct:
        data.battery_percent = dct['battery_percent']
    if "battery_voltage" in dct:
        data.battery_voltage = dct['battery_voltage']
    if "cpu_temperature_f" in dct:
        data.cpu_temperature_f = dct['cpu_temperature_f']
    if "time" in dct:
        data.time = dct['time']
    if "start_time" in dct:
        data.start_time = dct['start_time']
    return data

##
### # https://learn.adafruit.com/deep-sleep-with-circuitpython/sleep-memory
##
def get_saved_data(memory: bytearray) -> list[DeviceData]:
    saved_data = []
    idx = saved_data_starting_index
    obj_len = memory[idx]
    while obj_len != 0:
        idx += 1
        data = json_decoder(json.loads(memory[idx:idx + obj_len].decode()))

        saved_data.append(data)
        idx += obj_len
        obj_len = memory[idx]
    return saved_data


def add_saved_data(memory: bytearray, data: DeviceData):
    idx = saved_data_starting_index
    obj_len = memory[idx]
    print("obj_len = {}".format(obj_len))
    while obj_len != 0:
        idx += 1 + obj_len
        obj_len = memory[idx]
    print("idx {0}".format(idx))
    data_encoded = json.dumps(data.__dict__, separators=(',', ':')).encode()
    memory[idx] = len(data_encoded)
    idx += 1
    memory[idx:idx + len(data_encoded)] = data_encoded


def clear_saved_data(memory: bytearray):
    idx = saved_data_starting_index
    while idx < len(memory):
        memory[idx] = 0
        idx += 1
