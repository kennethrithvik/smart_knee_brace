import numpy as np
import pandas as pd
import glob
from sklearn.externals import joblib
from keras.models import load_model

# In[1]
# get sensor data

data_path="../../data/real_world_test/"
output_model_dir="./output_models/"
scale_file_name=output_model_dir+"scaler.dat"
label_encoder_filename=output_model_dir+"label_en.dat"
window_size=18
num_sensors=32

window_array=np.empty((0, window_size, num_sensors))
labels=[]
train_files = [i for i in glob.glob(data_path+'*.csv')]
for file in train_files:
    df = pd.read_csv(file)
    action = df["action"][1]
    df = df.drop(['top_temperature', 'bottom_temperature', 'Unnamed: 0', 'timestamp', 'action'], axis=1)
    df_window_array = df.values
    window_depth_limit = len(df_window_array) % window_size
    if window_depth_limit != 0 :
        df_window_array = df_window_array[:-window_depth_limit, :]
    df_window_array = df_window_array.reshape(len(df_window_array) // window_size, window_size, df_window_array.shape[1])
    df_labels = np.array([action] * df_window_array.shape[0])
    labels=np.append(labels,df_labels)
    window_array=np.append(window_array,df_window_array,axis=0)

num_time_periods, num_sensors = window_array.shape[1], window_array.shape[2]

# In[1]

##prepare test data
X_test=window_array
scaler = joblib.load(scale_file_name)
le=joblib.load(label_encoder_filename)

flatten_2d=X_test.reshape(X_test.shape[0]*X_test.shape[1],X_test.shape[2])
orig_shape=X_test.shape
# normalize the dataset
flatten_2d = scaler.transform(flatten_2d)
X_test=flatten_2d.reshape(orig_shape)
input_shape = (num_time_periods*num_sensors)
X_test = X_test.reshape(X_test.shape[0], input_shape)


# In[1]

## get the classifier

classifier = load_model(output_model_dir+'Model44_0.91.h5')
y_pred_test = classifier.predict(X_test)
# Take the class with the highest probability from the test predictions
max_y_pred_test = np.argmax(y_pred_test, axis=1)
y_pred=le.inverse_transform(max_y_pred_test)

# In[1]

for i,data in enumerate(y_pred):
    print("second",i,"action",data)


# In[1]




# In[1]





# In[1]





# In[1]





# In[1]



