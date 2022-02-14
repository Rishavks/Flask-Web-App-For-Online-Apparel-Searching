from flask import Flask, request, render_template, Response
import numpy as np
from PIL import Image
from datetime import datetime
from pathlib import Path
import os, io
import glob
import cv2

from google.cloud import vision

credential_path = "C:/Users/Rishav/OneDrive/Desktop/cbir/ImageSearch/servicekey.json"
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credential_path

client = vision.ImageAnnotatorClient()


app = Flask(__name__)

global capture, switch
capture = 0
switch = 0


camera = cv2.VideoCapture(0) 
camera.release()


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files['query_img']

        # Save query image C:/Users/Rishav/OneDrive/Desktop/cbir/ImageSearch/
        img = Image.open(file.stream) 
        uploaded_img_path = "static/uploads/" + datetime.now().isoformat().replace(":", ".") + "_" + file.filename
        img.save(uploaded_img_path)

        # Run search
        with io.open(uploaded_img_path, 'rb') as image_file:
            content = image_file.read()

        image = vision.Image(content = content)
        response = client.web_detection(image = image)
        web_detection = response.web_detection

        return render_template('index.html', 
        uploaded_img_path = uploaded_img_path,
        web_detection = web_detection)

    else:
        return render_template('index.html')
 

def gen_frames():  # generate frame by frame from camera
    global capture
    while True:
        success, frame = camera.read() 
        if success:
            if(capture):
                capture=0
                now = datetime.now()
                p = os.path.sep.join(['static/uploads/', "shot_{}.jpg".format(str(now).replace(":",''))])
                cv2.imwrite(p, frame)
                
            try:
                ret, buffer = cv2.imencode('.jpg', cv2.flip(frame,1))
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            
            except Exception as e:
                pass
            
        else:
            pass


@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/requests',methods=['POST','GET'])
def tasks():
    global switch,camera
    if request.method == 'POST':
        if request.form.get('click') == 'Capture':
            global capture
            capture=1
        elif  request.form.get('stop') == 'Stop/Start':
            
            if(switch==1):
                switch=0
                camera.release()
                cv2.destroyAllWindows()
                
            else:
                camera = cv2.VideoCapture(0)
                switch=1

        elif request.form.get('use') == 'UseImage':
            
            list_of_files = glob.glob('./static/uploads/*.jpg') # specific format *.jpg
            latest_file = max(list_of_files, key=os.path.getctime)
            
            #img = Image.open(latest_file)
            # Run search
            with io.open(latest_file, 'rb') as image_file:
                content = image_file.read()

            image = vision.Image(content = content)
            response = client.web_detection(image = image)
            web_detection = response.web_detection
            
            return render_template('index.html', 
            uploaded_img_path = latest_file,
            web_detection = web_detection)
      
    elif request.method=='GET':
        return render_template('index.html')

    return render_template('index.html')


if __name__=="__main__":
    app.run(debug=True) 

camera.release()
cv2.destroyAllWindows()    
