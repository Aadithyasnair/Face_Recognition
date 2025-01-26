from flask import Flask, request, render_template, jsonify
import cv2
import numpy as np
import base64
import face_recognition
import dlib

app = Flask(__name__)

# Load the known face and create the encoding
known_image = face_recognition.load_image_file("known_face.jpg")
known_face_encoding = face_recognition.face_encodings(known_image)[0]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process_frame', methods=['POST'])
def process_frame():
    data = request.json
    image_data = data['image'].split(',')[1]
    image = base64.b64decode(image_data)
    np_image = np.frombuffer(image, np.uint8)
    frame = cv2.imdecode(np_image, cv2.IMREAD_COLOR)

    # Convert the image from BGR color (which OpenCV uses) to RGB color
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Find all the faces and face encodings in the frame
    face_locations = face_recognition.face_locations(rgb_frame)
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
    # Use dlib to detect facial features
    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")
    dets = detector(rgb_frame, 1)

    for det in dets:
        shape = predictor(rgb_frame, det)
        for i in range(1, 68):
            cv2.circle(frame, (shape.part(i).x, shape.part(i).y), 1, (0, 255, 0), -1)

    for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
        # Draw a box around the face
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

        # See if the face is a match for the known face(s)
        matches = face_recognition.compare_faces([known_face_encoding], face_encoding)
        print(f"Matches: {matches}")

        if True in matches:
            cv2.putText(frame, "Match", (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

    # Encode the frame back to base64 to send back to the client
    _, buffer = cv2.imencode('.jpg', frame)
    encoded_frame = base64.b64encode(buffer).decode('utf-8')

    return jsonify({'image': f'data:image/jpeg;base64,{encoded_frame}'}), 200

if __name__ == '__main__':
    app.run(debug=True)