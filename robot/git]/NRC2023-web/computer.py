from flask import Flask, redirect, url_for, request, render_template
from flask_mqtt import Mqtt
import ssl
from turbo_flask import Turbo
import time
import threading

app = Flask(__name__)
turbo = Turbo(app)

app.config[
  'MQTT_BROKER_URL'] = 'f67aa56d63fe477796edc000d79019de.s2.eu.hivemq.cloud'
app.config['MQTT_BROKER_PORT'] = 8883
app.config['MQTT_USERNAME'] = 'ev3maker'
app.config['MQTT_PASSWORD'] = 'Test123-'
app.config['MQTT_TLS_ENABLED'] = True
app.config['MQTT_TLS_VERSION'] = ssl.PROTOCOL_TLS

mqtt = Mqtt(app)
list1 = []

@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
  if rc == 0:
    print("CONNACK received with code %s." % rc)
    mqtt.subscribe("ev3/test")
  else:
    print('Bad connection. Code:', rc)



@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
   global list1
   data = dict(
       topic=message.topic,
       payload=message.payload.decode()
  )
   msg = str(data['payload'])
   msg = msg.split(",")
   list1 = msg
   print('Received message on topic: {topic} with payload: {payload}'.format(**data))
   print("B motor is:", msg[0], "C motor is", msg[1])




@app.route('/success/<name>')
def success(name):
  return 'welcome %s' % name


@app.route("/")
def log():
  return render_template('index.html')

@app.context_processor
def inject_load():
  while True:
    try:
     return {"BM":list1[0], "CM":list1[1]}
    except:
      return {"BM":"NaN", "CM":"NaN", "Battery":"NaN"}
    finally:
      time.sleep(5)

def update_load():
    time.sleep(10)
    print("start")
    check = list1
    with app.app_context():
        while True:
          if check != list1:
            print("changing!!!")
            turbo.push(turbo.replace(render_template('load.html'), 'list1'))
            check = list1
            


if __name__ == '__main__':

  threading.Thread(target=update_load).start()
  # run() method of Flask class runs the application
 # on the local development server.
  app.run(host='0.0.0.0', port=80, debug=True)
