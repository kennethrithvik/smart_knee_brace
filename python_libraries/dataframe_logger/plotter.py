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
import datetime as dt
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# Don't forget to change the variables for the MQTT broker!
mqtt_username = "knee_brace"
mqtt_password = "knee_brace"
mqtt_topic = "knee_brace_nodemcu/#"
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
    #print(msg)

client.on_connect = on_connect  # attach function to callback
client.on_message = on_message  # attach function to callback
client.on_disconnect = on_disconnect
client.connect(mqtt_broker_ip, 1883)

table_fields = {
    # "id":"integer primary key autoincrement",
    "timestamp": "real",
    "top_accel_x": "real",
    "top_accel_y": "real",
    "top_accel_z": "real",
    "top_mag_x": "real",
    "top_mag_y": "real",
    "top_mag_z": "real",
    "top_gy_x": "real",
    "top_gy_y": "real",
    "top_gy_z": "real",
    "top_q0": "real",
    "top_qx": "real",
    "top_qy": "real",
    "top_qz": "real",
    "top_yaw": "real",
    "top_pitch": "real",
    "top_roll": "real",
    "top_temperature": "real",
    "bottom_accel_x": "real",
    "bottom_accel_y": "real",
    "bottom_accel_z": "real",
    "bottom_mag_x": "real",
    "bottom_mag_y": "real",
    "bottom_mag_z": "real",
    "bottom_gy_x": "real",
    "bottom_gy_y": "real",
    "bottom_gy_z": "real",
    "bottom_q0": "real",
    "bottom_qx": "real",
    "bottom_qy": "real",
    "bottom_qz": "real",
    "bottom_yaw": "real",
    "bottom_pitch": "real",
    "bottom_roll": "real",
    "bottom_temperature": "real",
    "action": "text"
}
action=sys.argv[1]

print("starting")
client.loop_start()


# Create figure for plotting
fig = plt.figure()
ax = fig.add_subplot(1, 1, 1)
xs = []
ys = []

# This function is called periodically from FuncAnimation
def animate(i, xs, ys):
    readings = []
    for data in list:
        if data is None:
            readings = []
            continue
        if data == "***":
            readings = []
            continue
        readings.append(data)
        if (len(readings) == 35):
            readings.append(action)
            test=float(readings[1])
            print(test)

            dataset.append(readings)
            readings = []

    # Add x and y to lists
    xs.append(dt.datetime.now().strftime('%M:%S.%f'))
    ys.append(test)
    # Limit x and y lists to 20 items
    xs = xs[-20:]
    ys = ys[-20:]

    # Draw x and y lists
    ax.clear()
    ax.plot(xs, ys)

    # Format plot
    plt.xticks(rotation=45, ha='right')
    plt.subplots_adjust(bottom=0.30)
    plt.title('top-accel x-axis')
    plt.ylabel('top-accel x')


# Set up plot to call animate() function periodically
ani = animation.FuncAnimation(fig, animate, fargs=(xs, ys), interval=50)
plt.show()

#client.disconnect()
print("ending ")