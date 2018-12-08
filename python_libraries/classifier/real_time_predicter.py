import numpy as np
import pandas as pd
import glob
from sklearn.externals import joblib
from keras.models import load_model
import paho.mqtt.client as mqtt
import matplotlib.animation as animation
import matplotlib.pyplot as plt
import datetime as dt
import time

# In[1]
mqtt_username = "knee_brace"
mqtt_password = "knee_brace"
mqtt_topic = "knee_brace_nodemcu/#"
mqtt_broker_ip = "192.168.1.190"
list = []
dataset = []
client = mqtt.Client()
client.username_pw_set(mqtt_username, mqtt_password)

# In[1]

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
print("starting")
client.loop_start()
time.sleep(2)

# In[1]

output_model_dir="./output_models/"
scale_file_name=output_model_dir+"scaler.dat"
label_encoder_filename=output_model_dir+"label_en.dat"
window_size=18
num_sensors=32
classifier = load_model(output_model_dir+'Model41_1.00.h5')
scaler = joblib.load(scale_file_name)
le=joblib.load(label_encoder_filename)


# In[1]

# Create figure for plotting
fig = plt.figure()
ax = fig.add_subplot(1, 1, 1)
xs = []
ys = []
# This function is called periodically from FuncAnimation
def animate(i, list ,dataset, xs, ys):
    readings = []
    list=list[-700:]
    dataset=[]
    for data in list:
        if data is None:
            readings = []
            continue
        if data == "***":
            readings = []
            continue
        readings.append(data)
        if (len(readings) == 35):
            x = float(readings[1])
            y = float(readings[2])
            z = float(readings[3])
            del readings[0],readings[16],readings[32]
            dataset.append(readings)
            readings = []

    # make windows
    dataset_np=np.array(dataset)
    window_depth_limit = len(dataset_np) % window_size
    if window_depth_limit != 0:
        dataset_np = dataset_np[:-window_depth_limit, :]
    dataset_np = dataset_np.reshape(len(dataset_np) // window_size, window_size,
                                        dataset_np.shape[1])
    num_time_periods, num_sensors = dataset_np.shape[1], dataset_np.shape[2]
    X_test = dataset_np

    #NORMALIZE
    flatten_2d = X_test.reshape(X_test.shape[0] * X_test.shape[1], X_test.shape[2])
    orig_shape = X_test.shape
    # normalize the dataset
    flatten_2d = scaler.transform(flatten_2d)
    X_test = flatten_2d.reshape(orig_shape)
    input_shape = (num_time_periods * num_sensors)
    X_test = X_test.reshape(X_test.shape[0], input_shape)

    #CLASSIFY
    y_pred_test = classifier.predict(X_test)
    max_y_pred_test = np.argmax(y_pred_test, axis=1)
    y_pred = le.inverse_transform(max_y_pred_test)
    #if y_pred[0]=="chair_situp":
    #    y_pred[0]="Walking"
    ax.clear()

    #display result
    time = str(dt.datetime.now().strftime('%M:%S'))
    plt.title("Second: "+time +"--> "+y_pred[0])
    print("Second: " , time , "--> " , y_pred[0])
    # Add x and y to lists
    xs.append(dt.datetime.now().strftime('%M:%S'))
    ys.append([x, y, z])
    # Limit x and y lists to 20 items
    xs = xs[-20:]
    ys = ys[-20:]
    ax.plot(xs, ys)

    # Format plot
    plt.xticks(rotation=45, ha='right')
    plt.subplots_adjust(bottom=0.30)
    plt.ylabel('top-accel')


# Set up plot to call animate() function periodically
ani = animation.FuncAnimation(fig, animate, fargs=(list ,dataset, xs, ys), interval=500)
plt.show()
