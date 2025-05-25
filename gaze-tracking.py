import zipfile
import cv2
import mediapipe as mp
import numpy as np
from datetime import datetime
import signal
import sys
import time
import requests
import argparse
import pyautogui
from PIL import Image, ImageDraw, ImageFont
import os
import shutil

# Initialize MediaPipe Face Mesh
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(static_image_mode=False,
                                   max_num_faces=1,
                                   refine_landmarks=True,  # Needed for iris tracking
                                   min_detection_confidence=0.5,
                                   min_tracking_confidence=0.5)

# Indices for iris and eye landmarks
LEFT_IRIS = [474, 475, 476, 477]
RIGHT_IRIS = [469, 470, 471, 472]
LEFT_EYE = [33, 133]
RIGHT_EYE = [362, 263]

# Function to calculate iris center
def iris_center(landmarks, iris_points, frame_shape):
    h, w = frame_shape
    coords = [(int(landmarks[p].x * w), int(landmarks[p].y * h)) for p in iris_points]
    center_x = int(np.mean([p[0] for p in coords]))
    center_y = int(np.mean([p[1] for p in coords]))
    return center_x, center_y

def writeToCsv(content):
    with open('iris_data.csv', 'a') as f:
        f.write(content +'\n')

def generateZip():
    with zipfile.ZipFile('iris_data.zip', 'w') as zipf:
        zipf.write('iris_data.csv')
        screenshots_dir = 'screenshots'
        if os.path.exists(screenshots_dir) and os.path.isdir(screenshots_dir):
            for filename in os.listdir(screenshots_dir):
                file_path = os.path.join(screenshots_dir, filename)
                if os.path.isfile(file_path):
                    # Add the file to the zip, preserving the 'screenshots/' path within the zip
                    zipf.write(file_path, arcname=os.path.join(screenshots_dir, filename))

def uploadZip():
    generateZip()
    print("Zip file generated")

    upload_url = getUploadUrl()
    if upload_url is None:
        print("Error: Failed to get upload URL")
        return
    
    file_path = "iris_data.zip"
    try:
        response = None
        with open(file_path, 'rb') as f:
            response = requests.put(upload_url, data=f)
        if response.status_code == 200:
            print("Upload successful.")
        
            screenshots_dir = 'screenshots'
            if os.path.exists(screenshots_dir) and os.path.isdir(screenshots_dir):
                try:
                    shutil.rmtree(screenshots_dir)
                    os.remove('iris_data.zip')
                    os.remove('iris_data.csv')
                except OSError as e:
                    print(f"Error deleting files: {e}")
        else:
            print(f"Failed to upload zip file. Status code: {response.status_code}")
            print(response.text)

    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
    except requests.exceptions.RequestException as e:
        print(f"Error during upload request: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def screenshot():
    screenshot = pyautogui.screenshot()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    draw = ImageDraw.Draw(screenshot)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 60)
    except IOError:
        font = ImageFont.load_default()

    position = (10, 10)
    text_color = (255, 255, 255)  # white
    outline_color = (0, 0, 0)     # black for contrast

    # Optional: Add outline for better visibility
    draw.text((position[0]+1, position[1]+1), timestamp, font=font, fill=outline_color)
    draw.text((position[0]-1, position[1]-1), timestamp, font=font, fill=outline_color)
    draw.text((position[0], position[1]), timestamp, font=font, fill=text_color)

    # Save with timestamp in filename
    filename = f"screenshots/screenshot_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.png"
    screenshot.save(filename)

def get_external_ip():
    try:
        return requests.get('https://api.ipify.org').text
    except Exception:
        return 'unknown-ip'

def getUploadUrl():
    ip = get_external_ip()
    api_url = "https://opthurh53e.execute-api.us-east-1.amazonaws.com/generate-url"
    response = requests.post(api_url, json={"file_name": f"iris_data_{ip}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.zip"})

    if response.status_code == 200:
        upload_url = response.json()['upload_url']
        return upload_url
    else:
        print("Error:", response.text)
        return None


def handle_sigint(signum, frame):
    print("\nCaught SIGINT (Ctrl-C). Cleaning up...")
    uploadZip()
    sys.exit(0)

def handle_sigterm(signum, frame):
    print("\nCaught SIGTERM. Cleaning up...")
    uploadZip()
    sys.exit(0)

def handle_sighup(signum, frame):
    print("\nCaught SIGHUP (terminal closed). Cleaning up...")
    uploadZip()
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, handle_sigint)   # Ctrl-C
signal.signal(signal.SIGTERM, handle_sigterm) # Termination signal
signal.signal(signal.SIGHUP, handle_sighup)   # Terminal closed (sometimes sent when terminal is closed)

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Eye gaze tracking with optional CSV upload')
    parser.add_argument('--upload', action='store_true', help='Only upload the CSV file and exit')
    args = parser.parse_args()

    # If --upload flag is set, only upload the CSV and exit
    if args.upload:
        print("Uploading CSV file...")
        uploadZip()
        return

    #  Webcam warnings - 
    print('Research Project - Eye Gaze Tracking')
    print("This program tries to access your webcam and track your eye movements. It will save the data to a CSV file and upload it to a remote server.")
    print("Webcam warnings - 1. Make sure the webcam is connected and working. 2. Make sure the webcam is not being used by another application.")
    print("Press Ctrl+C to stop the program")

    # Create screenshots folder if it doesn't exist
    screenshots_dir = "screenshots"
    if not os.path.exists(screenshots_dir):
        os.makedirs(screenshots_dir)
        print(f"Created directory: {screenshots_dir}")

    # Start webcam
    cap = cv2.VideoCapture(0)
    last_print_time = datetime.now()
    last_screenshot_time = 0

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(frame_rgb)

        if results.multi_face_landmarks:
            landmarks = results.multi_face_landmarks[0].landmark

            ih, iw, _ = frame.shape
            left_eye = [int(landmarks[i].x * iw) for i in LEFT_EYE]
            right_eye = [int(landmarks[i].x * iw) for i in RIGHT_EYE]

            left_center = iris_center(landmarks, LEFT_IRIS, (ih, iw))
            right_center = iris_center(landmarks, RIGHT_IRIS, (ih, iw))

            # Draw iris centers
            cv2.circle(frame, left_center, 2, (0, 255, 0), -1)
            cv2.circle(frame, right_center, 2, (0, 255, 0), -1)

            now = datetime.now()
            time_diff = now - last_print_time
            if time_diff.total_seconds() * 1000 >= 200:
                writeToCsv(f'{left_center}, "{now}"')
                # print(f'right iris: {right_center}, right eye: {right_eye}') # This line was commented out, keep it commented
                last_print_time = now

            if last_screenshot_time >= 300:
                screenshot()
                last_screenshot_time = 0
            else:
                last_screenshot_time += 1

            # Gaze direction logic (very basic)
            if left_center[0] < left_eye[0] and right_center[0] < right_eye[0]:
                gaze = "Looking Left"
            elif left_center[0] > left_eye[1] and right_center[0] > right_eye[1]:
                gaze = "Looking Right"
            else:
                gaze = "Looking Center"

            cv2.putText(frame, gaze, (30, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

        # cv2.imshow('Eye Gaze Tracker', frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
