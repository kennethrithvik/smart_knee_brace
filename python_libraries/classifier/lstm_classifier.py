import numpy as np
import pandas as pd
import glob
from sklearn.model_selection import train_test_split
from keras.utils import np_utils

# In[1]:
#prepare data

data_path="../../data/"
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

# In[1]
##split into train and test

X_train, X_test, y_train, y_test =\
    train_test_split(window_array, labels, test_size=0.001, random_state=13)

np.save(data_path+"train",X_train)
np.save(data_path+"train_lablel",y_train)
np.save(data_path+"test",X_test)
np.save(data_path+"test_lablel",y_test)
num_time_periods, num_sensors = X_train.shape[1], X_train.shape[2]

# In[1]

from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import MinMaxScaler
from sklearn.externals import joblib
##Normalize the data

flatten_2d=X_train.reshape(X_train.shape[0]*X_train.shape[1],X_train.shape[2])
orig_shape=X_train.shape
scaler = MinMaxScaler(feature_range=(0, 1))
scaler = scaler.fit(flatten_2d)
# normalize the dataset and print
flatten_2d = scaler.transform(flatten_2d)
X_train=flatten_2d.reshape(orig_shape)
# inverse transform and print
#inversed = scaler.inverse_transform(normalized)

##get lablels
le=LabelEncoder()
y_train=le.fit_transform(y_train)
num_classes = le.classes_.size
y_train_hot = np_utils.to_categorical(y_train, num_classes)
print('New y_train shape: ', y_train_hot.shape)

## save the scales and label encoder
joblib.dump(scaler, scale_file_name)
joblib.dump(le, label_encoder_filename)

# In[1]:
# Set input & output dimensions
print(list(le.classes_))
input_shape = (num_time_periods*num_sensors)
X_train = X_train.reshape(X_train.shape[0], input_shape)
print('x_train shape:', X_train.shape)
print('input_shape:', input_shape)


# In[1]:

from keras.models import Sequential
from keras.layers import Dense, Dropout, Flatten, Reshape, LSTM, TimeDistributed
from keras.optimizers import SGD,rmsprop,Adam
##define model

model = Sequential()
model.add(Reshape((window_size, num_sensors), input_shape=(input_shape,)))
model.add(LSTM(activation="sigmoid", return_sequences=True, units=256, recurrent_activation="hard_sigmoid"))
model.add(Dropout(0.5))
model.add(LSTM(activation="sigmoid", units=256, recurrent_activation="hard_sigmoid"))
model.add(Dropout(0.5))
#model.add(TimeDistributed(Dense(window_size)))
model.add(Dense(100, activation='relu'))
#model.add(Flatten())
model.add(Dense(num_classes, activation='softmax'))

# opt = rmsprop(lr=0.0001, decay=1e-6)
# opt = Adam(lr=0.001, beta_1=0.9, beta_2=0.999, epsilon=None, decay=0.0, amsgrad=True)
optimizer = SGD(lr=0.01, decay=1e-6, momentum=0.9, nesterov=True)
model.compile(optimizer = 'adam',
                   loss = 'categorical_crossentropy',
                   metrics = ['accuracy'])
print(model.summary())


# In[1]:
from keras.callbacks import ModelCheckpoint,EarlyStopping, TensorBoard

from keras.optimizers import SGD,rmsprop,Adam

##fitting the model with callbacks

# Part 2 - Fitting the CNN to the images

tensorboard=TensorBoard(log_dir='./logs/', histogram_freq=0,
                         batch_size=32, write_graph=True,
                         write_grads=True, write_images=True)

checkpointer = ModelCheckpoint(filepath=output_model_dir+'Model{epoch:02d}_{val_acc:.2f}.h5',
                               verbose=1, save_best_only=True)

early_stopping = EarlyStopping(monitor='val_loss', min_delta=0.0001,
                               patience=5, verbose=1, mode='auto')

callbacks_list=[tensorboard,checkpointer,early_stopping]

BATCH_SIZE = 75
EPOCHS = 100

history = model.fit(X_train,
                      y_train_hot,
                      batch_size=BATCH_SIZE,
                      epochs=EPOCHS,
                      callbacks=callbacks_list,
                      validation_split=0.2,
                      verbose=1)

# In[1]:
from matplotlib import pyplot as plt
import seaborn as sns
##plot metrics
plt.figure(figsize=(6, 4))
plt.plot(history.history['acc'], 'r', label='Accuracy of training data')
plt.plot(history.history['val_acc'], 'b', label='Accuracy of validation data')
plt.plot(history.history['loss'], 'r--', label='Loss of training data')
plt.plot(history.history['val_loss'], 'b--', label='Loss of validation data')
plt.title('Model Accuracy and Loss')
plt.ylabel('Accuracy and Loss')
plt.xlabel('Training Epoch')
plt.ylim(0)
plt.legend()
plt.show()

# In[1]:
from sklearn import metrics
from sklearn.metrics import classification_report
from keras.models import load_model
## test on test data

def show_confusion_matrix(validations, predictions):

    matrix = metrics.confusion_matrix(validations, predictions)
    plt.figure(figsize=(10, 10))
    sns.heatmap(matrix,
                cmap='coolwarm',
                linecolor='white',
                linewidths=1,
                xticklabels=le.classes_,
                yticklabels=le.classes_,
                annot=True,
                fmt='d')
    plt.title('Confusion Matrix')
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.show()

# In[1]:

##prepare test data
scaler = joblib.load(scale_file_name)
le=joblib.load(label_encoder_filename)

flatten_2d=X_test.reshape(X_test.shape[0]*X_test.shape[1],X_test.shape[2])
orig_shape=X_test.shape
# normalize the dataset
flatten_2d = scaler.transform(flatten_2d)
X_test=flatten_2d.reshape(orig_shape)
input_shape = (num_time_periods*num_sensors)
X_test = X_test.reshape(X_test.shape[0], input_shape)

##get lablels
y_test=le.transform(y_test)
y_test_hot = np_utils.to_categorical(y_test, num_classes)

# In[1

classifier = load_model(output_model_dir+'Model03_0.95.h5')
y_pred_test = classifier.predict(X_test)
# Take the class with the highest probability from the test predictions
max_y_pred_test = np.argmax(y_pred_test, axis=1)
max_y_test = np.argmax(y_test_hot, axis=1)


show_confusion_matrix(max_y_test, max_y_pred_test)
print(classification_report(le.inverse_transform(max_y_test), le.inverse_transform(max_y_pred_test)))

# In[1]:
#ROC Curve for each class
from sklearn.metrics import roc_curve, auc
from sklearn.preprocessing import label_binarize
from sklearn.multiclass import OneVsRestClassifier
import matplotlib.pyplot as plt
from scipy import interp
from itertools import cycle

##plot ROC curve

classnames=le.classes_

y_actual_binary = label_binarize(max_y_test, classes=[0,1,2,3,4])
y_pred_binary = y_pred_test#label_binarize(y_pred_probabilities, classes=[0, 1, 2, 3, 4])
n_classes=5
lw=2

# Compute ROC curve and ROC area for each class
fpr = dict()
tpr = dict()
roc_auc = dict()
for i in range(n_classes):
    fpr[i], tpr[i], _ = roc_curve(y_actual_binary[:, i], y_pred_binary[:, i])
    roc_auc[i] = auc(fpr[i], tpr[i])

# Compute micro-average ROC curve and ROC area
fpr["micro"], tpr["micro"], _ = roc_curve(y_actual_binary.ravel(), y_pred_binary.ravel())
roc_auc["micro"] = auc(fpr["micro"], tpr["micro"])

# Compute macro-average ROC curve and ROC area

# First aggregate all false positive rates
all_fpr = np.unique(np.concatenate([fpr[i] for i in range(n_classes)]))

# Then interpolate all ROC curves at this points
mean_tpr = np.zeros_like(all_fpr)
for i in range(n_classes):
    mean_tpr += interp(all_fpr, fpr[i], tpr[i])

# Finally average it and compute AUC
mean_tpr /= n_classes

fpr["macro"] = all_fpr
tpr["macro"] = mean_tpr
roc_auc["macro"] = auc(fpr["macro"], tpr["macro"])

# Plot all ROC curves
plt.figure(figsize=(7, 7))

colors = cycle(['red','blue','green','yellow','orange'])
for i, color in zip(range(n_classes), colors):
    plt.plot(fpr[i], tpr[i], color=color, lw=lw,
             label='ROC curve of class {0} (area = {1:0.2f})'
             ''.format(classnames[i], roc_auc[i]))

plt.plot([0, 1], [0, 1], 'k--', lw=lw)
plt.xlim([0.0, 1.0])
plt.ylim([0.0, 1.05])
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('Receiver operating characteristic for multi-class')
plt.legend(loc="best")
plt.show()


# In[1]:


# In[1]:




# In[1]:




# In[1]:

