## Logging MQTT Sensor Data to SQL DataBase With Python

![MQTT-SQL-Python-data-logger](http://www.steves-internet-guide.com/wp-content/uploads/MQTT-SQL-Python-data-logger.jpg)Most MQTT brokers don’t provide any mechanism for logging historical

In this project we will create a simple data logger that logs data to a sqlite database.

The project Consists of two modules.

- A sql logger class module sql_logger.py
- The logging script.

The script uses a main thread to get the data (on_message callback) and a worker thread to log the data.

A queue is used to move the messages between threads.

#### Sensor Data Characteristics

Because sensor data is often repetitive the script only logs** changed data**.

That means that if a sensor sends its status as “ON” once a second then it could result in 3600 “ON” messages logged every hour. The script will however only log 1 message.

#### SQL Logger Class

The class is implemented in a module called **sql_logger.py** (sql logger).

It consists of 5 main methods

- __init__ – initailise the class takes the database name
- Log_sensor -logs the sensor data
- Log_message – replaced by log_sensor
- drop_table – drops a table
- create_table – creates a table

To create an instance you need to supply a single parameter – the database file name:

logger=SQL_data_logger(db_file)

You then create a table to store the data, and optionally delete the old data by dropping the old table

logger.drop_table("logs")
logger.create_table("logs",table_fields) 

The database fields are the fields that you will be storing. In my case they are:

- Time
- Topic
- Sensor name
- Message

To store data in the database you use the **Log_sensor** method with two parameters as shown:

logger.Log_sensor(data_query,data_out)

The **data_query** contains the SQL statements that you want to execute and the **data_out** parameter contains a list of field values:

 data_query="INSERT INTO "+ Table_name \ +"(time,topic,sensor,message)VALUES(?,?,?,?)" 

data_out=[time,topic,sensor,message]

#### MQTT Data Logger

This script will log data on a collections of topics. It logs

- Message time
- Message topic
- message

The **on_message** callback calls the message_handler function to process the message.

The message handler function calls the** has_changed** function to check if the message status is different from the last message.

If it is the same then the message isn’t stored as there is not point storing the same message value multiple times.

If it is different it is placed on the queue.

The worker takes the data from the queue and logs it to disk.

The relevant code is shown below.

def on_message(client,userdata, msg):
topic=msg.topic
m_decode=str(msg.payload.decode("utf-8","ignore"))
message_handler(client,m_decode,topic)
#print("message received")
def message_handler(client,msg,topic):
data=dict()
tnow=time.localtime(time.time())
m=time.asctime(tnow)+" "+topic+" "+msg
data["time"]=tnow
data["topic"]=topic
data["message"]=msg
if has_changed(topic,msg):
print("storing changed data",topic, "   ",msg)
q.put(data) #put messages on queue
def has_changed(topic,msg):
topic2=topic.lower()
if topic2.find("control")!=-1:
return False
if topic in last_message:
if last_message[topic]==msg:
return False
last_message[topic]=msg
return True
def log_worker():
logger=SQL_data_logger(db_file)
logger.drop_table("logs")
logger.create_table("logs",table_fields)
"""runs in own thread to log data"""
while Log_worker_flag:
while not q.empty():
results = q.get()
if results is None:
continue
log.log_json(results)
#print("message saved ",results["message"])
log.close_file()

The worker is started at the beginning of the script.

t = threading.Thread(target=log_worker) #start logger
Log_worker_flag=True
t.start() #start logging thread

The **Log_worker_flag** is used to stop the worker when the script terminates

#### Using the Data Logger

You need to provide the script with:

- List of topics to monitor
- broker name and port
- username and password if needed.
- base log directory and number of logs have defaults

The script can also be run from the command line. Type

python mqtt-data-logger-sql.py -h

for a list of options.

#### Example Usage:

You will always need to specify the broker name or IP address and the topics to log

**Note**: You may not need to use the python prefix or may  
need to use python3 mqtt-data-logger-sql.py (Linux)

**Specify broker and topics**

python mqtt-data-logger-sql.py -b 192.168.1.157 -t sensors/#

**Specify broker and multiple topics**

python mqtt-data-logger-sql.py -b 192.168.1.157 -t sensors/# -t home/#

**Log All Data:**

python mqtt-data-logger-sql.py b 192.168.1.157 -t sensors/# -s

**Specify the client name used by the logger**

python mqtt-data-logger-sql.py b 192.168.1.157 -t sensors/# -n data-logger