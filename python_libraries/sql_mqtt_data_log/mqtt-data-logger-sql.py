#!python3
###demo code provided by Steve Cope at www.steves-internet-guide.com
##email steve@steves-internet-guide.com
###Free to use for any purpose

"""
This will log messages to file.Los time,message and topic as JSON data
"""
import paho.mqtt.client as mqtt
import json
import os
import time
import sys, getopt,random
import logging
#import mlogger as mlogger
from sql_logger import SQL_data_logger
import threading
from queue import Queue
q=Queue()

##### User configurable data section
username="knee_brace"
password="knee_brace"
verbose=True #True to display all messages, False to display only changed messages
mqttclient_log=False #MQTT client logs showing messages
logging.basicConfig(level=logging.INFO) #error logging
#use DEBUG,INFO,WARNING
####
options=dict()
##EDIT HERE ###############
brokers=["192.168.1.24","192.168.1.3","192.168.1.5","192.168.1.190"]
options["broker"]=brokers[1]
options["port"]=1883
options["verbose"]=True
options["cname"]=""
options["topics"]=[("knee_brace_nodemcu/#",0)]

#sql
db_file="sensor.db"
Table_name="sensor"
table_fields={
    "id":"integer primary key autoincrement",
    "timestamp": "text",
    "top_accel_x": "text",
    "top_accel_y": "text",
    "top_accel_z": "text",
    "top_mag_x": "text",
    "top_mag_y": "text",
    "top_mag_z": "text",
    "top_gy_x": "text",
    "top_gy_y": "text",
    "top_gy_z": "text",
    "top_q0": "text",
    "top_qx": "text",
    "top_qy": "text",
    "top_qz": "text",
    "top_yaw": "text",
    "top_pitch": "text",
    "top_roll": "text",
    "top_temperature": "text",
    "bottom_accel_x": "text",
    "bottom_accel_y": "text",
    "bottom_accel_z": "text",
    "bottom_mag_x": "text",
    "bottom_mag_y": "text",
    "bottom_mag_z": "text",
    "bottom_gy_x": "text",
    "bottom_gy_y": "text",
    "bottom_gy_z": "text",
    "bottom_q0": "text",
    "bottom_qx": "text",
    "bottom_qy": "text",
    "bottom_qz": "text",
    "bottom_yaw": "text",
    "bottom_pitch": "text",
    "bottom_roll": "text",
    "bottom_temperature": "text",
    }
###
cname=""
sub_flag=""
timeout=60
messages=dict()
last_message=dict()
######
def command_input(options={}):
    topics_in=[]
    qos_in=[]

    valid_options=" -b <broker> -p <port>-t <topic> -q QOS -v <verbose> -h <help>\
    -c <loop Time secs -d logging debug  -n Client ID or Name\
    -i loop Interval -u Username -P Password\
    "
    print_options_flag=False
    try:
      opts, args = getopt.getopt(sys.argv[1:],"hb:i:dk:p:t:q:l:vn:u:P:")
    except getopt.GetoptError:
      print (sys.argv[0],valid_options)
      sys.exit(2)
    qos=0

    for opt, arg in opts:
        if opt == '-h':
            print (sys.argv[0],valid_options)
            sys.exit()
        elif opt == "-b":
             options["broker"] = str(arg)
        elif opt == "-i":
             options["interval"] = int(arg)
        elif opt == "-k":
             options["keepalive"] = int(arg)
        elif opt =="-p":
            options["port"] = int(arg)
        elif opt =="-t":
            topics_in.append(arg)
        elif opt =="-q":
             qos_in.append(int(arg))
        elif opt =="-n":
             options["cname"]=arg
        elif opt =="-d":
            options["loglevel"]="DEBUG"
        elif opt == "-P":
             options["password"] = str(arg)
        elif opt == "-u":
             options["username"] = str(arg)        
        elif opt =="-v":
            options["verbose"]=True
      

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

    #print("message received")
def message_handler(client,msg,topic):
    #data=dict()
    #data["topic"]=topic
    #data["message"]=msg
    if verbose :
        #print("storing changed data",topic, "   ",msg)
        q.put(msg) #put messages on queue

def log_worker():
    """runs in own thread to log data"""
    #create logger
    logger=SQL_data_logger(db_file)
    logger.drop_table(Table_name)
    logger.create_table(Table_name,table_fields)
    readings=[]
    while Log_worker_flag:
        while not q.empty():
            data = q.get()
            if data is None:
                continue
            if data == "***":
                readings=[]
                for i in range(35):
                    data = q.get()
                    if data == "***":
                        q.put("***")
                        continue
                    readings.append(data)
                #print(readings)
                
                
            try:
                data_out=readings
                data_query="INSERT INTO "+ \
                Table_name +"(timestamp,top_accel_x,top_accel_y,top_accel_z,top_mag_x,\
                top_mag_y,top_mag_z,top_gy_x,top_gy_y,top_gy_z,top_q0,top_qx,top_qy,top_qz,\
                top_yaw,top_pitch,top_roll,top_temperature,bottom_accel_x,bottom_accel_y,\
                bottom_accel_z,bottom_mag_x,bottom_mag_y,bottom_mag_z,bottom_gy_x,bottom_gy_y,\
                bottom_gy_z,bottom_q0,bottom_qx,bottom_qy,bottom_qz,bottom_yaw,bottom_pitch,\
                bottom_roll,bottom_temperature)\
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"   
                logger.Log_sensor(data_query,data_out)
            except Exception as e:
                print("problem with logging ",e)
    logger.conn.close()

            #print("message saved ",results["message"])


########################
####

    
def Initialise_clients(cname,cleansession=True):
    #flags set
    client= mqtt.Client(cname)
    if mqttclient_log: #enable mqqt client logging
        client.on_log=on_log
    client.on_connect= on_connect        #attach function to callback
    client.on_message=on_message        #attach function to callback
    client.on_disconnect=on_disconnect
    client.on_subscribe=on_subscribe
    return client
###



###########
def convert(t):
    d=""
    for c in t:  # replace all chars outside BMP with a !
            d =d+(c if ord(c) < 0x10000 else '!')
    return(d)
def print_out(m):
    if display:
        print(m)

    
########################main program
if __name__ == "__main__" and len(sys.argv)>=2:
    command_input(options)
    pass
verbose=options["verbose"]

if not options["cname"]:
    r=random.randrange(1,10000)
    cname="logger-"+str(r)
else:
    cname="logger-"+str(options["cname"])
       
#Initialise_client_object() # add extra flags
logging.info("creating client"+cname)
client=Initialise_clients(cname,False)#create and initialise client object
if username !="":
    client.username_pw_set(username, password)
topics=options["topics"]
broker=options["broker"]
port=1883
keepalive=60
print("starting")

##
t = threading.Thread(target=log_worker) #start logger
Log_worker_flag=True
t.start() #start logging thread
###
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
#loop and wait until interrupted
try:
    while True:
        pass
except KeyboardInterrupt:
    print("interrrupted by keyboard")


client.loop_stop()  #final check for messages
time.sleep(5)
Log_worker_flag=False #stop logging thread
print("ending ")

