from flask import Flask, Response
import subprocess
import time

app = Flask(__name__)

def generate_frames():
    # GStreamer pipeline that outputs JPEG frames
    gst_cmd = [
        'gst-launch-1.0',
        '-q',
        'nvarguscamerasrc', 'sensor-id=0',
        '!', 'video/x-raw(memory:NVMM),width=1280,height=720,framerate=30/1',
        '!', 'nvvidconv',
        '!', 'nvjpegenc',
        '!', 'fdsink'
    ]
    
    print(f"Starting GStreamer pipeline...")
    process = subprocess.Popen(gst_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=10**8)
    
    try:
        while True:
            # Read JPEG marker
            marker = process.stdout.read(2)
            if len(marker) != 2 or marker != b'\xff\xd8':
                continue
                
            # Read until end of JPEG
            jpeg_data = marker
            while True:
                byte = process.stdout.read(1)
                if not byte:
                    break
                jpeg_data += byte
                if len(jpeg_data) >= 2 and jpeg_data[-2:] == b'\xff\xd9':
                    break
            
            if len(jpeg_data) > 100:  # Valid JPEG
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + jpeg_data + b'\r\n')
    finally:
        process.terminate()
        process.wait()

@app.route('/')
def index():
    return '''
    <html>
      <head><title>Orin Camera Stream</title></head>
      <body style="margin:0; padding:0; background:#000;">
        <h1 style="color:#fff; text-align:center;">Jetson Camera Stream</h1>
        <div style="text-align:center;">
          <img src="/video_feed" style="max-width:100%; height:auto;">
        </div>
      </body>
    </html>
    '''

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    print("Starting Flask server on port 5000...")
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
