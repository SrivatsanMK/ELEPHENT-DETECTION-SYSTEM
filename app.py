import signal
from flask import Flask, render_template, Response, request, redirect, url_for
import cv2
import torch
import os
import time
import sendSMS

app = Flask(__name__)

# Load your custom YOLOv5 model
model = torch.hub.load('ultralytics/yolov5', 'custom', path='best.pt')  # Replace with your model path

elephant_detected_timeout = 2  # Close port after this many seconds of no detection
last_detection_time = 0  # Track the last detection time


def generate_frames(video_path):
    global last_detection_time

    cap = cv2.VideoCapture(video_path)
    sms_sent = False
    confidence_threshold = 0.60  # Confidence threshold
    elephant_detected_timeout = 2  # Timeout after which alert stops if no elephant detected
    wrong = False

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # YOLOv5 processing
        results = model(frame)
        elephant_detected = False  # Track if elephant is detected in the current frame

        for *xyxy, conf, cls in results.xyxy[0]:
            if conf < confidence_threshold:
                wrong = True
                continue
            else:
                wrong = False

            label = f'{model.names[int(cls)]} {conf:.2f}'
            cv2.rectangle(frame, (int(xyxy[0]), int(xyxy[1])), (int(xyxy[2]), int(xyxy[3])), (0, 255, 0), 2)
            cv2.putText(frame, label, (int(xyxy[0]), int(xyxy[1]) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            if model.names[int(cls)] == "elephant" and not wrong:
                elephant_detected = True
                last_detection_time = time.time()

                # Send SMS alert if elephant is detected and no SMS sent before
                if not sms_sent:
                    try:
                        sendSMS.send("Elephant Detected -Thoppur")  # Replace with actual SMS function
                        print("SMS sent: Elephant Detected")
                        sms_sent = True
                    except Exception as e:
                        print(f"Error sending SMS: {e}")

        # Convert the frame to JPEG and send it as a response
        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            continue  # Skip if the frame cannot be encoded

        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    cap.release()


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        video = request.files['video']
        video_path = os.path.join('static/uploads', video.filename)
        video.save(video_path)
        return redirect(url_for('video_feed', path=video_path))
    return render_template('index.html')


@app.route('/video_feed/<path:path>')
def video_feed(path):
    return Response(generate_frames(path),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


def handle_sigint(signal_received, frame):
    """Handle SIGINT (Ctrl+C) to clean up resources."""
    print("\nSIGINT received. Cleaning up...")
    exit(0)


# Register the SIGINT handler
signal.signal(signal.SIGINT, handle_sigint)

if __name__ == '__main__':
    app.run(debug=True)
