import serial
import cv2
import uvicorn
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import StreamingResponse

# Global Vars
ser = serial.Serial("COM7", 115200, timeout=None)  # Create Serial connection on port COM7 w/ baudrate 115200
app = FastAPI()
templates = Jinja2Templates(directory="templates")
# Initialize Model
net = cv2.dnn.readNet("dnn_model/yolov4-tiny.weights", "dnn_model/yolov4-tiny.cfg")  # Load model
model = cv2.dnn_DetectionModel(net)  # Define Model
model.setInputParams(size=(320, 320), scale=1 / 255)  # Resize image for detection (larger image is more accurate but slower), must be a multiple of 32
classes = [] # Create empty array to hold classes
with open("dnn_model/classes.txt", "r") as file_object: # Open classes file and read into array
    for class_name in file_object.readlines():
        class_name = class_name.strip()
        classes.append(class_name)

# Initialize Camera
capture = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # Create video capture object
capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1280) # Set camera width
capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 720) # Set camera height

def main():
    ser.close()  # Close serial port, in case it was left open
    ser.open()  # Reopen serial port for communication

    # Wait for ESP32 Setup() to complete
    setup_complete = False
    while setup_complete == False:
        message_received = ser.readline().decode()
        if message_received != "":  # Do not print blank messages
            print(message_received)
        if ("SETUP COMPLETE!" in message_received):  # If message contains "SETUP COMPLETE!" print alert and exit loop
            print("Setup complete received.")
            setup_complete = True

    uvicorn.run(app, host='127.0.0.1', port=8080)

    #command = input("Enter command: ")
    #serialIO(command)
        
    #Cleanup
    ser.close()
    cv2.destroyAllWindows()

@app.get('/')
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get('/video_feed')
def video_feed():
    return StreamingResponse(objectID(), media_type='multipart/x-mixed-replace; boundary=frame')

def serialIO(command):
    ser.write(command.encode())  # Encode and send command
    message_received = ser.readline().decode()  # Read serial response
    while (not "~" in message_received):  # Read serial response until end of message character received
        print(message_received)
        message_received = ser.readline().decode()
        
def objectID():
    while True:
        success, frame = capture.read()
        if not success:
            break
        else:
            # Object Detection
            # All values are arrays of all detected objects
            # class_ids = identifier of the detected object type (see classes.txt)
            # scores = confidence in object detection accuracy
            # bounding_boxes = top left x,y coordinate along with object width and height
            (class_ids, scores, bounding_boxes) = model.detect(frame)

            for class_id, score, bounding_box in zip(class_ids, scores, bounding_boxes):  # Loop through IDed objects
                x, y, width, height = bounding_box  # Extract values from bounding box
                if score > 0.5:
                    cv2.rectangle(frame, (x, y), ((x + width), (y + height)), (255, 0, 0), 3)  # Draw rectangle
                    label = classes[class_id] + ", " + str(round(score * 100)) + "%"
                    cv2.putText(frame, label, (x, y - 5), cv2.FONT_HERSHEY_PLAIN, 1, (255, 0, 0), 2) # Label bounding box with object type

            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

if __name__ == "__main__":
    main()
