import unittest
import json

from adafruit_bme280 import basic as adafruit_bme280
# import board

from DeviceData import DeviceData, saved_data_starting_index, clear_saved_data, add_saved_data, get_saved_data
from unittest.mock import MagicMock


class MyTestCase(unittest.TestCase):
    sleep_memory = bytearray(4096)

    def test_something(self):
        buffers = [b'\xc2{"time":1684434908,"pressure":996.116,"temperature":30.4389,"duration":6528,',
                   b'"humidity":30.0889,"battery_percent":99.9,"battery_voltage":3.978,',
                   b'"start_time":1684434908,"cpu_temperature_f":91.8795}\xc2{"time":1684434974,',
                   b'"pressure":996.108,"temperature":30.2617,"duration":6147,"humidity":30.6328,',
                   b'"battery_percent":99.9,"battery_voltage":3.855,"start_time":1684434974,',
                   b'"cpu_temperature_f":90.3005}\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00']
        index = saved_data_starting_index
        for buf in buffers:
            self.sleep_memory[index:index+len(buf)] = buf
            index += len(buf)
        # mockboard = board.I2C()

        # bme280 = MagicMock()
        # battery_monitor = MagicMock()
        # clear_saved_data(self.sleep_memory)
        datum = get_saved_data(self.sleep_memory)
        print("len", len(datum))
        for dat in datum:
            dat.influx_data()

        self.assertEqual(len(get_saved_data(self.sleep_memory)), 0)
        data1 = DeviceData()
        data1.__dict__ = {'time': 1684429258, 'pressure': 996.073, 'temperature': 28.7129, 'duration': 5242,
                          'humidity': 36.561, 'battery_percent': 0.2, 'battery_voltage': 3.761,
                          'start_time': 1684429258, 'cpu_temperature_f': 91.8795}
        add_saved_data(self.sleep_memory, data1)
        self.assertEqual(len(get_saved_data(self.sleep_memory)), 1)
        data2 = DeviceData()
        data2.__dict__ = {'time': 1684429324, 'pressure': 996.019, 'temperature': 29.1381, 'duration': 6146,
                          'humidity': 34.4351, 'battery_percent': 0.2, 'battery_voltage': 4.004,
                          'start_time': 1684429324, 'cpu_temperature_f': 87.1426}

        self.assertEqual(data2.humidity, 34.4351)
        add_saved_data(self.sleep_memory, data2)
        self.assertEqual(len(get_saved_data(self.sleep_memory)), 2)

        sleep_memory = self.sleep_memory
        clear_saved_data(self.sleep_memory)
        self.assertEqual(len(get_saved_data(self.sleep_memory)), 0)

        # adafruit_feather_esp32s2 seems to have 4k, alarm.sleep_memory[4000:4096] worked in REPL
        # sleep_memory[0:1] = b'ei'

        data1 = DeviceData()
        data1.battery_percent = 97.5
        data1.battery_voltage = 3.75
        data1.humidity = 55.5
        data1.temperature = 22.5
        data1.cpu_temperature = 30.5
        add_saved_data(sleep_memory, data1)
        add_saved_data(sleep_memory, data1)
        add_saved_data(sleep_memory, data1)

        # data1_json = json.dumps(data1.__dict__).encode()
        #
        # idx = 0
        # sleep_memory[idx] = len(data1_json)
        # sleep_memory[idx+1:len(data1_json)] = data1_json
        #
        # idx += 1 + len(data1_json)
        # sleep_memory[idx] = len(data1_json)
        # sleep_memory[idx+1:len(data1_json)] = data1_json
        #
        # idx += 1 + len(data1_json)
        # sleep_memory[idx] = len(data1_json)
        # sleep_memory[idx+1:len(data1_json)] = data1_json
        # idx = 0
        # obj_len = sleep_memory[idx]
        # print("length of json = ", obj_len)
        # idx += 1
        # data2 = DeviceData()
        # data2.__dict__ = json.loads(sleep_memory[idx:idx+obj_len].decode())
        # idx += obj_len
        #
        saved_data = get_saved_data(self.sleep_memory)
        self.assertEqual(len(saved_data), 3)
        # self.assertEqual(sleep_memory[idx+1], 0)

        for data in saved_data:
            self.assertEqual(data1.battery_voltage, data.battery_voltage)
            self.assertEqual(data1.humidity, data.humidity)

        clear_saved_data(sleep_memory)
        saved_data = get_saved_data(self.sleep_memory)
        self.assertEqual(len(saved_data), 0)

    # t1 = '{"time":1684360025,"pressure":984.674,"temperature":30.0187,"duration":6268,"humidity":28.4964,' \
    #     '"battery_percent":100.0,"battery_voltage":4.186,"start_time":1684360025,"cpu_temperature_f":94.2479} '
    #
    # t2 = '{"time":1684360025,"pressure":984.674,"temperature":30.0187,"duration":6268,"humidity":28.4964,"battery_percent":100.0,"battery_voltage":4.186,"start_time":1684360025,"cpu_temperature_f":94.2479}'
    # lst = [t1, t2]
    # print(json.dumps(lst))


if __name__ == '__main__':
    unittest.main()
