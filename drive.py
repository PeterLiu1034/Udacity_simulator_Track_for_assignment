import socketio
import eventlet
import numpy as np
from flask import Flask
from keras.models import load_model
import base64
from io import BytesIO
from PIL import Image
import cv2

sio = socketio.Server()  # 初始化两端间实时通讯服务

app = Flask(__name__)  # '__main__'
speed_limit = 20


def img_preprocess(img):
    img = img[60:135, :, :]
    img = cv2.cvtColor(img, cv2.COLOR_RGB2YUV)
    img = cv2.GaussianBlur(img, (3, 3), 0)
    img = cv2.resize(img, (200, 66))
    img = img / 255
    return img


@sio.on('telemetry')
def telemetry(sid, data):
    speed = float(data['speed'])  # 时速
    image = Image.open(BytesIO(base64.b64decode(data['image'])))
    # base64用于解码；BytesIO使用内在字节缓冲区的二进制流，图片解码后要先经过buffer module再读取
    image = np.asarray(image)  # 数据更是调整为array
    print('1：{}'.format(image))
    image = img_preprocess(image)  # 图片预处理
    image = np.array([image])  # 数据由3维转4维？？？？
    print('2：{}'.format(image))
    steering_angle = float(model.predict(image))
    throttle = 1.0 - speed / speed_limit  # 时速与限制车速相同时，油门为0
    print('{} {} {}'.format(steering_angle, throttle, speed))
    send_control(steering_angle, throttle)


@sio.on('connect')
def connect(sid, environ):
    print('Connected')
    send_control(0, 0)  # 连接后发送初始化的油门和方向数据，相当于汽车启动


def send_control(steering_angle, throttle):
    sio.emit('steer', data={
        'steering_angle': steering_angle.__str__(),
        'throttle': throttle.__str__()
    })


if __name__ == '__main__':
    model = load_model('model_assignment_4.h5')  # 加载所需model
    app = socketio.Middleware(sio, app)  # sio为socket server，app为flask app
    eventlet.wsgi.server(eventlet.listen(('', 4567)), app)  # wsgi为send request用；listen()为任何IP下的监听4567端口，对象是app
