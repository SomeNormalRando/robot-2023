#!/usr/bin/env python3
print("ev3dev alive")
import ev3dev2.fonts as fonts
from ev3dev2.sound import Sound
from ev3dev2.display import Display

#region Constants
MEDIUM_MOTOR_OPENING_SPEED = 1560
MEDIUM_MOTOR_CLOSING_SPEED = -500
MIN_LARGE_MOTOR_SPEED = 100 # motor stops if speed is below this
MAX_LARGE_MOTOR_SPEED = 1050
# font list: https://ev3dev-lang.readthedocs.io/projects/python-ev3dev/en/ev3dev-stretch/display.html#bitmap-fonts
DISPLAY_FONT = fonts.load("charB08")
#endregion

display = Display()
spkr = Sound()
def speak(text):
    spkr.speak(text, volume = 100, play_type = 1)

def display_info(message: str, speak1 = False):
    print("[INFO] " + message)

    if (speak1 == True):
        speak(message)

    display.text_pixels(
        text = "[INFO] " + message,
        clear_screen = True,
        x = 0, y = 0,
        text_color = "OrangeRed",
        font = DISPLAY_FONT
    )
    display.update()

#import modules
import evdev
# import ev3dev.auto as ev3
import time
import ev3dev2
from ev3dev2 import motor
from ev3dev2.power import PowerSupply as power
# import paho.mqtt.client as paho
# from paho import mqtt
import threading
import time
'''
#mqtt stuff
def on_connect(client, userdata, flags, rc, properties=None):
  print("CONNACK received with code %s." % rc)

def on_message(client, userdata, msg):
  print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
  client.loop_stop()

def run_fl(name):
  client = paho.Client(client_id="", userdata=None, protocol=paho.MQTTv5)
  client.on_connect = on_connect


  client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)

  client.username_pw_set("ev3maker", "Test123-")
  client.connect("f67aa56d63fe477796edc000d79019de.s2.eu.hivemq.cloud", 8883)

  
  
  client.loop_start()
  client.publish("ev3/test", payload=name, qos=1)
  print("sent ", name)
  client.on_message = on_message
  client.loop_stop()



def on_message(client, userdata, msg):
  print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
  client.loop_stop()

'''
#region Helper functions
def clamp(n, minn, maxn):
    return max(min(maxn, n), minn)
def scale(val, src, dst):
    return (float(val - src[0]) / (src[1] - src[0])) * (dst[1] - dst[0]) + dst[0]

def scale_stick(value):
    return scale(value, (0, 255), (-MAX_LARGE_MOTOR_SPEED, MAX_LARGE_MOTOR_SPEED))
def dc_clamp(value: float):
    # set speed to 0 if it is below minimum
    if value > -MIN_LARGE_MOTOR_SPEED and value < MIN_LARGE_MOTOR_SPEED:
        return 0
    return clamp(value, -MAX_LARGE_MOTOR_SPEED, MAX_LARGE_MOTOR_SPEED)
#endregion
display_info("Constants and helper functions loaded.")
display_info("Loading modules...", True)

#region Initialisation
print("Finding PS4 controller...")
# controller ip D0:27:88:71:F8:2F

devices = [evdev.InputDevice(fn) for fn in evdev.list_devices()]
ps4dev = devices[0].fn
display_info("Found controller", True)
gamepad = evdev.InputDevice(ps4dev)

forward_speed = 0
side_speed = 0
grab_speed = 0
running = True

# #post class
# class post(threading.Thread):
#     def __init__(self):
#         print("posting")
#         self.rm = motor.LargeMotor(motor.OUTPUT_C)
#         self.lf = motor.LargeMotor(motor.OUTPUT_B)
        
#         threading.Thread.__init__(self)
    
    # def run(self):
    #         while running:
    #             Bm = self.lf.position
    #             Cm = self.rm.position
                
    #             mes = (Bm, Cm)
    #             mes = ','.join([str(x) for x in mes])

    #             # run_fl(mes)
    #             print(mes)
    #             time.sleep(10)
    
            

class MotorThread(threading.Thread):
    def __init__(self):
        #init motor
        self.left_motor = motor.LargeMotor(motor.OUTPUT_B)
        try:
            self.right_motor = motor.LargeMotor(motor.OUTPUT_C)
        except:
            print("No C motor found")
        
        
        #catch med motor
        try:
            self.medium = motor.MediumMotor(motor.OUTPUT_D)
        except(ev3dev2.DeviceNotFound):
            display_info("No motor found", True)
            print("no med motor")
            pass
        
        threading.Thread.__init__(self)

    
    #main func
    def run(self):
        print("MotorThread running!")
        display_info("Thread started")
        while running:
            
            try:
                self.right_motor.run_forever(speed_sp = dc_clamp(forward_speed + side_speed))
            except:
                print("No C motor found")
                pass
            self.left_motor.run_forever(speed_sp = dc_clamp(-forward_speed + side_speed))
            try:
                self.medium.run_forever(speed_sp = grab_speed)
            except:
                pass
            
        try:
            self.right_motor.stop()
        except:
            print("No C motor found")
        self.left_motor.stop()
        self.medium.stop()
        
    
    def medium_run(self, speed):
        try:
            self.medium.run_forever(speed_sp=speed)
        except:
            return
    def medium_stop(self):
        try:
            self.medium.stop()
        except:
            return


motor_thread = MotorThread()
motor_thread.setDaemon(True)
motor_thread.start()

# post1 = post()
# post1.setDaemon(True)
# post1.start()
#endregion

for event in gamepad.read_loop():   # this loops infinitely
    if event.type == 3:             # A stick is moved
        if event.code == 0:         # X axis on left stick
            forward_speed = -scale_stick(event.value)
        if event.code == 1:         # Y axis on left stick
            side_speed = -scale_stick(event.value)
        if side_speed < 100 and side_speed > -100:
            side_speed = 0
        if forward_speed < 100 and forward_speed > -100:
            forward_speed = 0

    #medium motor
    if event.type == 1:
        if event.code == 313 and event.value == 1:
            grab_speed = 1560
        elif event.code == 311 and event.value == 1:
            grab_speed = -1560
        else:
            grab_speed = 0
    
