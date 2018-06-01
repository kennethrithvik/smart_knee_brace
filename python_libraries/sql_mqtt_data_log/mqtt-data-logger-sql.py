#!python3


import paho.mqtt.client as mqtt
import json
import os
import time
import sys, getopt,random
import logging
from sql_logger import SQL_data_logger
import threading
from queue import Queue

q=Queue()

##### User configurable data section
username="knee_brace"
password="knee_brace"
logging.basicConfig(format='%(asctime)-15s [%(name)s-%(process)d] %(levelname)s: %(message)s', level=logging.INFO) #error logging
####

options=dict()
##EDIT HERE ###############
brokers=["192.168.1.24","192.168.1.3","192.168.1.5","192.168.1.190","192.168.1.4"]
options["broker"]=brokers[4]
options["port"]=1883
options["cname"]=""
options["topics"]=[("knee_brace_nodemcu/#",0)]
options["action"] = "Standing"

cname=""
######

def command_input(options={}):
    topics_in=[]
    qos_in=[]

    valid_options=" -b <broker> -p <port>-t <topic> -q QOS -h <help>\
     -n Client ID or Name\
    -u Username -P Password -a Action\
    "
    try:
      opts, args = getopt.getopt(sys.argv[1:],"hb:p:t:q:l:n:u:P:a:")
    except getopt.GetoptError:
      print (sys.argv[0],valid_options)
      sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print (sys.argv[0],valid_options)
            sys.exit()
        elif opt == "-b":
             options["broker"] = str(arg)
        elif opt =="-p":
            options["port"] = int(arg)
        elif opt =="-t":
            topics_in.append(arg)
        elif opt =="-q":
             qos_in.append(int(arg))
        elif opt =="-n":
             options["cname"]=arg
        elif opt == "-P":
             options["password"] = str(arg)
        elif opt == "-u":
             options["username"] = str(arg)        
        elif opt == "-a":
             options["action"] = str(arg)
      

    lqos=len(qos_in)
    for i in range(len(topics_in)):
        if lqos >i: 
            topics_in[i]=(topics_in[i],int(qos_in[i]))
        else:
            topics_in[i]=(topics_in[i],0)         
        
    if topics_in:
        options["topics"]=topics_in #array with qos

####

#callbacks -all others define in functions module
def on_connect(client, userdata, flags, rc):
    logging.debug("Connected flags"+str(flags)+"result code "\
    +str(rc)+"client1_id")
    if rc==0:
        client.connected_flag=True
    else:
        client.bad_connection_flag=True

def on_disconnect(client, userdata, rc):
    logging.debug("disconnecting reason  " + str(rc))
    client.connected_flag=False
    client.disconnect_flag=True
    client.subscribe_flag=False
    
def on_message(client,userdata, msg):
    topic=msg.topic
    m_decode=str(msg.payload.decode("utf-8","ignore"))
    message_handler(client,m_decode,topic)

def on_subscribe(client,userdata,mid,granted_qos):
    m="in on subscribe callback result "+str(mid)
    logging.debug(m)
    client.subscribed_flag=True

def message_handler(client,msg,topic):
    #data=dict()
    #data["topic"]=topic
    #data["message"]=msg
    q.put(msg) #put messages on queue
    #print(msg)

def log_worker():
    """runs in own thread to log data"""
    #create logger
    logger=SQL_data_logger(db_file)
    logger.drop_table(Table_name)
    logger.create_table(Table_name,table_fields)
    readings=[]
    while Log_worker_flag:
        while not q.empty():
            logging.info("logging data")
            cont=False
            data = q.get()
            if data is None:
                continue
            if data == "***":
                readings=[]
                for i in range(35):
                    data = q.get()
                    if data == "***":
                        cont=True
                        break
                    readings.append(float(data))
                readings.append(options["action"])
                if cont:
                    print('error in receiving')
                    continue
                
            try:
                data_out=readings
                data_query="INSERT INTO "+ \
                Table_name +"(timestamp,top_accel_x,top_accel_y,top_accel_z,top_mag_x,\
                top_mag_y,top_mag_z,top_gy_x,top_gy_y,top_gy_z,top_q0,top_qx,top_qy,top_qz,\
                top_yaw,top_pitch,top_roll,top_temperature,bottom_accel_x,bottom_accel_y,\
                bottom_accel_z,bottom_mag_x,bottom_mag_y,bottom_mag_z,bottom_gy_x,bottom_gy_y,\
                bottom_gy_z,bottom_q0,bottom_qx,bottom_qy,bottom_qz,bottom_yaw,bottom_pitch,\
                bottom_roll,bottom_temperature,action)\
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"   
                logger.Log_sensor(data_query,data_out)
            except Exception as e:
                print("problem with logging ",e)
    logger.conn.close()



########################
####

    
def Initialise_clients(cname,cleansession=True):
    #flags set
    client= mqtt.Client(cname)
    client.on_connect= on_connect        #attach function to callback
    client.on_message=on_message        #attach function to callback
    client.on_disconnect=on_disconnect
    client.on_subscribe=on_subscribe
    return client
###


########################  main program
if __name__ == "__main__" and len(sys.argv)>=2:
    command_input(options)
    pass
    print()

if not options["cname"]:
    r=random.randrange(1,10000)
    cname="logger-"+str(r)
else:
    cname="logger-"+str(options["cname"])

#sql
db_file="sensor.db"
Table_name=options["action"]
table_fields={
    "id":"integer primary key autoincrement",
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
    "action":"text"
    }
###

#Initialise_client_object() # add extra flags
logging.info("creating client"+cname)
client=Initialise_clients(cname,False)#create and initialise client object
if username and password !="":
    client.username_pw_set(username, password)
topics=options["topics"]
broker=options["broker"]
port=options["port"]
print("starting")


client.connected_flag=False # flag for connection
client.bad_connection_flag=False
client.subscribed_flag=False
client.loop_start()
client.connect(broker,port)
while not client.connected_flag: #wait for connection
    time.sleep(1)
client.subscribe(topics)
while not client.subscribed_flag: #wait for connection
    time.sleep(1)
    print("waiting for subscribe")
print("subscribed ",topics)
##
Log_worker_flag=True
t = threading.Thread(target=log_worker) #start logger
t.start() #start logging thread
###
#loop and wait until interrupted
try:
    while True:
        pass
except KeyboardInterrupt:
    print("interrrupted by keyboard")


client.loop_stop()  #final check for messages
time.sleep(5)
while not q.empty():
    pass
Log_worker_flag=False #stop logging thread
print("ending ")

