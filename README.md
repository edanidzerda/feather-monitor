

# Feather ESP32-S2 based humidity/temperature sensor

This project is what I am using at home to monitor the humidity in my crawlspace.  The code sends humidity/temperature from the BME280, battery voltage and "percentage", the CPU's temperature and a "duration" of how long the code ran to generate the reading.


What you need to reproduce
* [Adafruit ESP32-S2 Feather with BME280 Sensor](https://www.adafruit.com/product/5303)
* An instance of [Influx DB](https://www.influxdata.com/) -- I'm using 2.7 in Docker.  

## Implementation notes

You could use InfluxDB "in the Cloud," but then why not use Adafruit IO?  I used Adafruit's example code as a start, but I wanted to keep data for as long as I wanted locally.

Other devices would work with small modifications.  Personally my next device will not have a built-in temperature sensor. This board was *very* handy to get started, but the temperature readings are biased when you are charging, or if the device has been running for too long.

Copy `code.py` and `DeviceData.py` to your device.

Edit `settings.toml` to add the required variables, as shown below.

`settings.toml` example:
```
ssid="Wifi Network"
password="Wifi Password"
influxdb_api_token="[get from InfluxDB]"
# 60 * 30 for 1 hour
sleep_period=1800
location="text key for where your device is"
influxdb_url="http://[your InfluxDB IP]:8086/api/v2/write?org=home&bucket=humidity&precision=s"
```
