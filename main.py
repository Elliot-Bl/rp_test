# Emotion detector for Raspberry Pi 4
# Author: Elliot Blanford
# Date: 1/18/2021
# Description:

# Original code/inspiration by Evan Juras
# https://github.com/EdjeElectronics/TensorFlow-Object-Detection-on-the-Raspberry-Pi/blob/master/Object_detection_picamera.py
# I updated it to work with tensorflow v2, changed it to an emotion detection model, and made it run on my intel
# neural compute stick 2

## Some of the code is copied from Google's example at
## https://github.com/tensorflow/models/blob/master/research/object_detection/object_detection_tutorial.ipynb

## and some is copied from Dat Tran's example at
## https://github.com/datitran/object_detector_app/blob/master/object_detection_app.py


# Import packages
import os
import cv2
import numpy as np
from picamera.array import PiRGBArray
from picamera import PiCamera
import tensorflow.compat.v1 as tf
import argparse
import sys
from PIL import Image

import tflite_runtime.interpreter as tflite


# tf.disable_v2_behavior()

# Set up camera constants
IM_WIDTH = 1280
IM_HEIGHT = 720
#IM_WIDTH = 640 #   Use smaller resolution for
#IM_HEIGHT = 480 #  slightly faster framerate

# Select camera type (if user enters --usbcam when calling this script,
# a USB webcam will be used)
camera_type = 'picamera'

# This is needed since the working directory is the object_detection folder.
sys.path.append('..')

# Import utilites
from utils import label_map_util
from utils import visualization_utils as vis_util

# Name of the directory containing the object detection module we're using
# MODEL_NAME = 'ssdlite_mobilenet_v2_coco_2018_05_09'

# Grab path to current working directory
CWD_PATH = os.getcwd()

# Path to frozen detection graph .pb file, which contains the model that is used
# for object detection.
# PATH_TO_CKPT = os.path.join(CWD_PATH, MODEL_NAME, 'frozen_inference_graph.pb')

# Path to label map file
# PATH_TO_LABELS = os.path.join(CWD_PATH, 'data', 'mscoco_label_map.pbtxt')

# Number of classes the object detector can identify
# NUM_CLASSES = 90

## Load the label map.
# Label maps map indices to category names, so that when the convolution
# network predicts `5`, we know that this corresponds to `airplane`.
# Here we use internal utility functions, but anything that returns a
# dictionary mapping integers to appropriate string labels would be fine
# label_map = label_map_util.load_labelmap(PATH_TO_LABELS)
# categories = label_map_util.convert_label_map_to_categories(label_map, max_num_classes=NUM_CLASSES,
#                                                             use_display_name=True)
# category_index = label_map_util.create_category_index(categories)

# Load the Tensorflow model into memory.
# detection_graph = tf.Graph()
# with detection_graph.as_default():
#     od_graph_def = tf.GraphDef()
#     with tf.gfile.GFile(PATH_TO_CKPT, 'rb') as fid:
#         serialized_graph = fid.read()
#         od_graph_def.ParseFromString(serialized_graph)
#         tf.import_graph_def(od_graph_def, name='')
#
#     sess = tf.Session(graph=detection_graph)

# Define input and output tensors (i.e. data) for the object detection classifier

# Input tensor is the image
# image_tensor = detection_graph.get_tensor_by_name('image_tensor:0')

# Output tensors are the detection boxes, scores, and classes
# Each box represents a part of the image where a particular object was detected
# detection_boxes = detection_graph.get_tensor_by_name('detection_boxes:0')

# Each score represents level of confidence for each of the objects.
# The score is shown on the result image, together with the class label.
# detection_scores = detection_graph.get_tensor_by_name('detection_scores:0')
# detection_classes = detection_graph.get_tensor_by_name('detection_classes:0')

# Number of objects detected
# num_detections = detection_graph.get_tensor_by_name('num_detections:0')

# Initialize frame rate calculation
frame_rate_calc = 1
freq = cv2.getTickFrequency()
font = cv2.FONT_HERSHEY_SIMPLEX

# Initialize camera and perform object detection.
# The camera has to be set up and used differently depending on if it's a
# Picamera or USB webcam.

# I know this is ugly, but I basically copy+pasted the code for the object
# detection loop twice, and made one work for Picamera and the other work
# for USB.
frs = np.array([])
num_frames = 0
average_fr = 0
mapper = {0:'anger', 1:'disgust', 2:'fear', 3:'happiness', 4: 'sadness', 5: 'surprise', 6: 'neutral'}
### Picamera ###
if camera_type == 'picamera':
    # Initialize Picamera and grab reference to the raw capture
    camera = PiCamera()
    camera.resolution = (IM_WIDTH, IM_HEIGHT)
    camera.framerate = 10
    rawCapture = PiRGBArray(camera, size=(IM_WIDTH, IM_HEIGHT))
    rawCapture.truncate(0)

    for frame1 in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):

        t1 = cv2.getTickCount()

        # Acquire frame and expand frame dimensions to have shape: [1, None, None, 3]
        # i.e. a single-column array, where each item in the column has the pixel RGB value
        frame = np.copy(frame1.array)
        frame.setflags(write=1)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # print('frame rgb = ', type(frame_rgb), np.shape(frame_rgb))
        # frame_rgb = vis_util._resize_original_image([frame_rgb], [48,48])
        frame_rgb = cv2.resize(frame_rgb, (48,48))
        # print('frame rgb = ', type(frame_rgb), np.shape(frame_rgb))
        frame_expanded = np.expand_dims(frame_rgb/255, axis=2).astype('float32')
        # print('frame expanded = ', type(frame_expanded[0][0][0]), np.shape([frame_expanded]))
        # Load the TFLite model and allocate tensors.
        interpreter = tflite.Interpreter(model_path="emotions.tflite")
        interpreter.allocate_tensors()

        # Get input and output tensors.
        input_details = interpreter.get_input_details()
        output_details = interpreter.get_output_details()

        # Test the model on random input data.
        # input_shape = input_details[0]['shape']
        # input_data = np.array(np.random.random_sample(input_shape), dtype=np.float32)

        interpreter.set_tensor(input_details[0]['index'], [frame_expanded])

        interpreter.invoke()

        # cv2_imshow(image * 255)

        # The function `get_tensor()` returns a copy of the tensor data.
        # Use `tensor()` in order to get a pointer to the tensor.
        output_data = interpreter.get_tensor(output_details[0]['index'])

        # need to show predition on the screen, if it's a 'confident' prediction, i'll show the %
        if(np.max(output_data[0] * 100) > 50):
            print("Guess: ", mapper[np.where(output_data[0] == np.max(output_data[0]))[0][0]],
                  "(%.02f%%)" % np.max(output_data[0] * 100))
        else:
            print("Guess: ", mapper[np.where(output_data[0] == np.max(output_data[0]))[0][0]])

        # Draw the results of the detection (aka 'visulaize the results')
        # vis_util.visualize_boxes_and_labels_on_image_array(
        #     frame,
        #     np.squeeze(boxes),
        #     np.squeeze(classes).astype(np.int32),
        #     np.squeeze(scores),
        #     category_index,
        #     use_normalized_coordinates=True,
        #     line_thickness=8,
        #     min_score_thresh=0.40)
        #
        # cv2.putText(frame, "FPS: {0:.2f}".format(frame_rate_calc), (30, 50), font, 1, (255, 255, 0), 2, cv2.LINE_AA)

        # All the results have been drawn on the frame, so it's time to display it.
        #cv2.imshow('Emotion detector', frame)

        t2 = cv2.getTickCount()
        time1 = (t2 - t1) / freq
        frame_rate_calc = 1 / time1
        
        #frs = np.append(frs, frame_rate_calc)
        #average_fr = np.mean(frs)
        #print("Average frame rate = ", average_fr)
        # Press 'q' to quit
        
        if cv2.waitKey(1) == ord('q'):
            break

        rawCapture.truncate(0)

    camera.close()

cv2.destroyAllWindows()
