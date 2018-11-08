#!python3

########
'''
Main logger to be used
usage :
python mqtt_logger <ACTION> <TIME in SECONDS>
'''
#######
import paho.mqtt.client as mqtt
import pandas as pd
import sys
import time

data_path="../../data/real_world_test/"
#data_path="../../data/"
# Don't forget to change the variables for the MQTT broker!
mqtt_username = "knee_brace"
mqtt_password = "knee_brace"
mqtt_topic = "knee_brace_nodemcu"
mqtt_broker_ip = "192.168.1.190"
list = []
dataset = []
client = mqtt.Client()
# Set the username and password for the MQTT client
client.username_pw_set(mqtt_username, mqtt_password)


def on_connect(client, userdata, rc, test):
    # rc is the error code returned when connecting to the broker
    print("Connected!", str(client), str(userdata), str(rc), str(test))
    print("Topic: ", mqtt_topic + ": ")

    # Once the client has connected to the broker, subscribe to the topic
    client.subscribe(mqtt_topic)

def on_disconnect(client, userdata, rc):
    pass


def on_message(client, userdata, msg):
    msg=str(msg.payload.decode("utf-8", "ignore"))
    list.append(msg)
    print(msg)

client.on_connect = on_connect  # attach function to callback
client.on_message = on_message  # attach function to callback
client.on_disconnect = on_disconnect
client.connect(mqtt_broker_ip, 1883)

df=pd.read_csv(data_path+"test.csv")
df = df.drop([ 'Unnamed: 0', 'action'], axis=1)
df=df.values



# In[1]
for row in df:
    for col in row:
        client.publish(mqtt_topic, col)
    client.publish(mqtt_topic, "***")
    print("publishing")
    time.sleep(0.050)

