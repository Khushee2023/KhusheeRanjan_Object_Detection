import cv2
import numpy as np
import math
import matplotlib.pyplot as plt

# Load pre-trained DNN model (example with YOLOv4-tiny)
model_config = "yolov4.cfg"  # Path to config file
model_weights = "yolov4.weights"  # Path to weights file
net = cv2.dnn.readNetFromDarknet(model_config, model_weights)

# Load class names (COCO dataset as example)
with open("classes.txt", "r") as f:
    class_names = [line.strip() for line in f.readlines()]

# Load video
cap = cv2.VideoCapture("busy_road.mp4")

# Check if the video file opened successfully
if not cap.isOpened():
    print("Error: Could not open video file.")
    exit()

# Get video properties for saving
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = int(cap.get(cv2.CAP_PROP_FPS))
fourcc = cv2.VideoWriter_fourcc(*"XVID")
output_video = cv2.VideoWriter("KhusheeRanjan.avi", fourcc, fps, (frame_width, frame_height))


# Detection threshold
conf_threshold = 0.5
nms_threshold = 0.4

# Initialize tracking variables
tracking_objects = {}
track_id = 0

# Function to display a frame in Jupyter
def display_frame(frame):
    """Display a frame using Matplotlib in Jupyter."""
    plt.axis('off')
    plt.imshow(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    plt.show()

# Function to detect objects
def detect_objects(frame):
    # Prepare the image as input for the model
    blob = cv2.dnn.blobFromImage(frame, scalefactor=1 / 255.0, size=(416, 416), swapRB=True, crop=False)
    net.setInput(blob)

    # Get the names of the output layers
    layer_names = net.getLayerNames()
    output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]

    # Perform forward pass and get detections
    detections = net.forward(output_layers)

    boxes = []
    class_ids = []
    confidences = []

    # Parse detections
    for output in detections:
        for detection in output:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]

            if confidence > conf_threshold:  # Set your confidence threshold
                center_x = int(detection[0] * frame.shape[1])
                center_y = int(detection[1] * frame.shape[0])
                w = int(detection[2] * frame.shape[1])
                h = int(detection[3] * frame.shape[0])

                x = int(center_x - w / 2)
                y = int(center_y - h / 2)

                boxes.append([x, y, w, h])
                class_ids.append(class_id)
                confidences.append(float(confidence))

    # Apply Non-Maximum Suppression (NMS) to refine boxes
    indices = cv2.dnn.NMSBoxes(boxes, confidences, conf_threshold, nms_threshold)

    # Extract resulting boxes, class IDs, and confidences
    result_boxes = []
    result_class_ids = []
    result_confidences = []
    if len(indices) > 0:
        for i in indices.flatten():
            result_boxes.append(boxes[i])
            result_class_ids.append(class_ids[i])
            result_confidences.append(confidences[i])

    return result_boxes, result_class_ids, result_confidences

# Ensure output video writer initializes correctly
output_video = cv2.VideoWriter("KhusheeRanjan.avi", fourcc, fps, (frame_width, frame_height))
if not output_video.isOpened():
    print("Error: Could not initialize video writer.")
    exit()

# Process video frames
count = 0
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    count += 1
    center_points_cur_frame = []

    # Detect objects
    boxes, class_ids, confidences = detect_objects(frame)
    for i, box in enumerate(boxes):
        x, y, w, h = box
        cx = int((x + x + w) / 2)
        cy = int((y + y + h) / 2)
        center_points_cur_frame.append((cx, cy))

        # Draw rectangle and label
        label = f"{class_names[class_ids[i]]}: {confidences[i]:.2f}"
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    # Update tracking objects
    new_tracking_objects = {}
    for pt in center_points_cur_frame:
        same_object_detected = False
        for object_id, prev_pt in tracking_objects.items():
            distance = math.hypot(prev_pt[0] - pt[0], prev_pt[1] - pt[1])
            if distance < 35:
                new_tracking_objects[object_id] = pt
                same_object_detected = True
                break

        if not same_object_detected:
            new_tracking_objects[track_id] = pt
            track_id += 1

    tracking_objects = new_tracking_objects

    # Draw tracking points
    for object_id, pt in tracking_objects.items():
        cv2.circle(frame, pt, 5, (0, 0, 255), -1)
        cv2.putText(frame, str(object_id), (pt[0] - 10, pt[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    # Write frame to output video
    output_video.write(frame)

    # Display frame in Jupyter
    #display_frame(frame)

    #if count > 100:  # Limit to 100 frames for testing
    #    break

# Release resources
cap.release()
output_video.release()

print("Video processing complete. Output saved as 'KhusheeRanjan.avi'.")

