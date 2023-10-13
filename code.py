# SPDX-FileCopyrightText: 2021 Kattni Rembor for Adafruit Industries
# SPDX-License-Identifier: Unlicense

"""
Humidity/Temperature sensor code to that saves to InfluxDB for storage
  * Can save sensor readings in sleep memory to save battery by only turning on Wifi when needed
  * Sends humidity/temperature from bme280, also sends CPU temperature, battery voltage and percentage

Was originally the example code from Adafruit:
CircuitPython Adafruit IO Example for BME280 and LC709203 Sensors
"""
import time
import os
import ssl
import alarm
import board
import digitalio
import wifi
import socketpool
import adafruit_requests
from adafruit_lc709203f import LC709203F, PackSize
from adafruit_bme280 import basic as adafruit_bme280
import adafruit_logging as logging
import adafruit_ntp
import rtc
from DeviceData import DeviceData, add_saved_data, get_saved_data, clear_saved_data
from struct import pack, unpack

# from usyslog import SyslogHandler

# Duration of sleep in seconds. Default is 600 seconds (10 minutes).
sleep_duration = os.getenv('sleep_period')
influxdbUrl = os.getenv('influxdb_url')
TZ_OFFSET = 0  # Use UTC to avoid determining DST
battery_pack_size = PackSize.MAH2200

start = time.monotonic_ns()

# Setup the little red LED
led = digitalio.DigitalInOut(board.LED)
led.switch_to_output()

# Set up the BME280 and LC709203 sensors
bme280 = adafruit_bme280.Adafruit_BME280_I2C(board.I2C())
battery_monitor = LC709203F(board.I2C())
battery_monitor.pack_size = battery_pack_size


def go_to_sleep(sleep_period):
    # Turn off I2C power by setting it to input
    i2c_power = digitalio.DigitalInOut(board.I2C_POWER)
    i2c_power.switch_to_input()
    neopixel_power = digitalio.DigitalInOut(board.NEOPIXEL_POWER)
    neopixel_power.switch_to_input()

    # Create an alarm that will trigger sleep_period number of seconds from now.
    time_alarm = alarm.time.TimeAlarm(
        monotonic_time=time.monotonic() + sleep_period)
    # Exit and deep sleep until the alarm wakes us.
    alarm.exit_and_deep_sleep_until_alarms(time_alarm)


##
## This helper class embeds the Wifi connection so it can be turned on only when needed
##
class WifiControl:
    wifi_enabled: bool
    pool: socketpool
    requests: adafruit_requests.Session

    def __init__(self):
        self.wifi_enabled = False

    def get_pool(self):
        if self.wifi_enabled is False:
            self.connect_wifi()
        return self.pool

    def get_requests(self):
        if self.wifi_enabled is False:
            self.connect_wifi()
        return self.requests

    def connect_wifi(self):
        try:
            # Connect to Wi-Fi
            wifi.radio.connect(os.getenv("ssid"), os.getenv("password"))
            print("Connected to {}!".format(os.getenv("ssid")))
            print("IP:", wifi.radio.ipv4_address)
            self.wifi_enabled = True
            self.pool = socketpool.SocketPool(wifi.radio)
            self.requests = adafruit_requests.Session(
                self.pool, ssl.create_default_context())
        # Wi-Fi connectivity fails with error messages, not specific errors, so this except is broad.
        except Exception as e:  # pylint: disable=broad-except
            print(e)
            go_to_sleep(60)


wifi_control = WifiControl()
if not alarm.wake_alarm:
    # Set system clock with NTP on first boot
    # TODO update clock once every month
    clear_saved_data(alarm.sleep_memory)
    # Get current time using NTP
    ntp = adafruit_ntp.NTP(wifi_control.get_pool(), tz_offset=TZ_OFFSET)
    rtc.RTC().datetime = ntp.datetime

    now = time.localtime()
    print("Set Real Time Clock via NTP: {:2}:{:02}".format(now.tm_hour, now.tm_min))

# Turn on the LED to indicate data is being sent.
led.value = True

duration = int((time.monotonic_ns() - start) / 1E6)  # not used currently

sensor_reading = DeviceData(bme280, battery_monitor, duration)
print(sensor_reading.__dict__)

add_saved_data(alarm.sleep_memory, sensor_reading)
saved_data = get_saved_data(alarm.sleep_memory)

if len(saved_data) > 1:
    # If more than one reading was saved in sleep_memory, let's write it to InfluxDB
    # TODO:  If this helps with battery life, perhaps sleep for 3 readings or 4
    print("Saved data size {}".format(len(saved_data)))
    data = ""
    for reading in saved_data:
        print("reading timestamp", time.localtime(reading.time))
        data += reading.influx_data()
    print("data: ", data)
    try:
        print("Writing data to %s" % influxdbUrl)
        response = wifi_control.get_requests().post(influxdbUrl, headers={'Content-Type': 'text/plain',
                                                                          'Authorization': "Token {0}".format(os.getenv("influxdb_api_token"))},
                                                    data=data)
        print("*" * 40)
        print("JSON Response: ", response.headers)
        print("-" * 40)
        response.close()
        clear_saved_data(alarm.sleep_memory)
        # Turn off the LED to indicate data sending is complete.
        led.value = False
    except Exception as e:  # pylint: disable=broad-except
        print(e)
go_to_sleep(sleep_duration)
