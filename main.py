from machine import Pin, SoftI2C, RTC
from time import sleep
import ujson, ntptime, framebuf, network

import ufirebase as firebase
from hcsr04 import HCSR04
from ssd1306 import SSD1306_I2C

with open("config.json") as f:
    config = ujson.load(f)
    
def hour(time):
    if time - 3 < 0:
        return 24 - time - 3
    return time - 3
    
MQTT_CLIENT_ID = "micropython-usonic"
MQTT_BROKER    = "test.mosquitto.org"
MQTT_USER      = ""
MQTT_PASSWORD  = ""

print("Connecting to WiFi", end="")
sta_if = network.WLAN(network.STA_IF)
sta_if.active(True)
sta_if.disconnect()
sta_if.connect('visitantes', '')
while not sta_if.isconnected():
  print(".", end="")
  sleep(0.1)
print(" Connected!")

firebase.setURL("https://esp32-iot-77acf-default-rtdb.firebaseio.com/")

ntptime.settime()

# Inicializa o sensor ultrasônico
usonic = HCSR04(trigger_pin=22, echo_pin=23, echo_timeout_us=30000)
led = Pin(2, Pin.OUT)

# Inicializa os pinos I2C
i2c = SoftI2C(scl=Pin(7), sda=Pin(6))
# Inicializa a saída OLED
oled_width = 128
oled_height = 64
oled = SSD1306_I2C(oled_width, oled_height, i2c)

N = 15
listOfDistances = [0]*N
trigger_distance = 50
distance_median = config["last_distance"]
print(distance_median)

while True:
  
  for i in range(N):
    listOfDistances[i] = usonic.distance_cm()
    sleep(0.2/N)
    
  listOfDistances.sort()
  prev_distance = distance_median
  distance_median = listOfDistances[N//2]
  difference = distance_median - prev_distance
  
  oled.fill(0)
  oled.text("Distance:", 0, 0)
  oled.text(str(distance_median) + " cm", 0, 15)
  oled.text("Difference:", 0, 30)
  oled.text(str(difference) + " cm", 0, 45)
  oled.show()
  
  datetime = RTC().datetime()
  timestamp = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
    datetime[0], datetime[1], datetime[2],
    hour(datetime[4]), datetime[5], datetime[6]
  )
  
  data = {
    "timestamp": timestamp,
    "difference": difference,
    "distance": distance_median,
  }
  
  if abs(difference) > 1 and distance_median < trigger_distance:
      led.value(1)
      firebase.addto("alarme", data)
      print(data)
      sleep(1)
  else:
      led.value(0)
      
  config["last_distance"] = distance_median
  with open("config.json", "w") as f:
        ujson.dump(config, f)

