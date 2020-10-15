from flask import Flask, redirect, url_for, render_template, Response, jsonify
from flask import Blueprint
import cv2, numpy as np
from src.helpers import Vehicle
import time

router = Blueprint('router', __name__)

## HELPER
# Variables

result = [0,0,0,0]
lock = [0]

class B:
    def __init__(self):
        self.value = 1.8
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.vehicles = []
        self.max_p_age = 5
        self.pid = 1
        self.cnt_up = 0
        self.cnt_down = 0
        self.UpMTR = 0
        self.UpLV = 0
        self.UpHV = 0
        self.DownLV = 0
        self.DownHV = 0

def get_time():
    sl = sum(result)
    myround = lambda x,base:round(x*base)/base
    lst = list(map(lambda x: myround(0 if sl ==0 else x*4/sl, 5), result))
    return lst
    
def gen_frame(cap, A, name):
    w = cap.get(3)
    h = cap.get(4)
    frameArea = h*w
    areaTH = frameArea/800

    line_up = int(A.value*(h/5))
    line_down = int(1.7*(h/5))
    
    up_limit = int(1*(h/5))
    down_limit = int(4*(h/5))

    line_down_color = (255, 0, 0)

    pt1 = [0, line_down]

    pt2 = [w, line_down]
    pts_L1 = np.array([pt1, pt2], np.int32)
    pts_L1 = pts_L1.reshape((-1, 1, 2))


    pt5 = [0, up_limit]
    pt6 = [w, up_limit]
    pts_L3 = np.array([pt5, pt6], np.int32)
    pts_L3 = pts_L3.reshape((-1, 1, 2))
    pt7 = [0, down_limit]
    pt8 = [w, down_limit]
    pts_L4 = np.array([pt7, pt8], np.int32)
    pts_L4 = pts_L4.reshape((-1, 1, 2))


    fgbg = cv2.createBackgroundSubtractorMOG2()

    kernelOp = np.ones((3, 3), np.uint8)
    kernelOp2 = np.ones((5, 5), np.uint8)
    kernelCl = np.ones((11, 11), np.uint8)

    while cap.isOpened():
        #frame = function(cap, h, w)
        ret, frame = cap.read()
        for i in A.vehicles:
            i.age_one()    # age every person on frame

        #################
        # PREPROCESSING #
        #################
        fgmask = fgbg.apply(frame)
        fgmask2 = fgbg.apply(frame)

        # Binary to remove shadow

        try:
            ret, imBin = cv2.threshold(fgmask, 200, 255, cv2.THRESH_BINARY)
            ret, imBin2 = cv2.threshold(fgmask2, 200, 255, cv2.THRESH_BINARY)
            # Opening (erode->dilate) to remove noise
            mask = cv2.morphologyEx(imBin, cv2.MORPH_OPEN, kernelOp)
            mask2 = cv2.morphologyEx(imBin2, cv2.MORPH_OPEN, kernelOp)
            # Closing (dilate->erode) to join white region
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernelCl)
            mask2 = cv2.morphologyEx(mask2, cv2.MORPH_CLOSE, kernelCl)
            #cv2.imshow('Image Threshold', cv2.resize(fgmask, (400, 300)))
            #ret, jpeg = cv2.imencode('.jpg', fgmask)
            #return jpeg.tobytes()

        except:
            # If there is no more frames to show...
            print('EOF')
            return 

        #
        # FIND CONTOUR

        contours0, hierarchy = cv2.findContours(
            mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        for cnt in contours0:

            cv2.drawContours(frame, cnt, -1, (0, 255, 0), 3, 8)
            area = cv2.contourArea(cnt)

            if area > areaTH:

                #   TRACKING

                M = cv2.moments(cnt)
                cx = int(M['m10']/M['m00'])
                cy = int(M['m01']/M['m00'])
                x, y, w, h = cv2.boundingRect(cnt)

                new = True
                for i in A.vehicles:
                    if abs(x-i.getX()) <= w and abs(y-i.getY()) <= h:
                        new = False
                        # Update the coordinates in the object and reset age
                        i.updateCoords(cx, cy)
                        if i.going_UP(line_down, line_up) == True:
                            roi = frame[y:y + h, x:x + w]
                            rectangle = cv2.rectangle(
                                frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                            height = h
                            width = w
                            kll = 2 * (height + width)

                            if kll < 300:
                                A.UpMTR += 1
                            elif kll < 500:
                                A.UpLV += 1
                            elif kll > 500:
                                A.UpHV += 1

                            A.cnt_up += 1
                            print("ID:", i.getId(), 'crossed going up at',
                                  time.strftime("%c"))
                        elif i.going_DOWN(line_down, line_up) == True:
                            roi = frame[y:y+h, x:x+w]
                            rectangle = cv2.rectangle(
                                frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                            height = y+h
                            width = x+w
                            luas = height*width

                            if luas < 600000:
                                A.DownLV += 1
                            elif luas > 600000:
                                A.DownHV += 1

                            A.cnt_down += 1
                            print("ID:", i.getId(), 'crossed going down at',
                                  time.strftime("%c"))
                        break
                    if i.getState() == '1':
                        if i.getDir() == 'down' and i.getY() > down_limit:
                            i.setDone()
                        elif i.getDir() == 'up' and i.getY() < up_limit:
                            i.setDone()
                    if i.timedOut():
                        # Remove from the list person
                        index = A.vehicles.index(i)
                        A.vehicles.pop(index)
                        del i
                if new == True:
                    p = Vehicle.MyVehicle(A.pid, cx, cy, A.max_p_age)
                    A.vehicles.append(p)
                    A.pid += 1

                ##################
                ##   DRAWING    ##
                ##################
                cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)
                img = cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

        for i in A.vehicles:

            cv2.putText(frame, str(i.getId()), (i.getX(), i.getY()),
                        A.font, 0.3, i.getRGB(), 1, cv2.LINE_AA)

        # IMAGE
        str_up = 'cnt: ' + str(A.cnt_up)
        MTR_up = 'Up Motor: ' + str(A.UpMTR)
        LV_up = 'Up Mobil: ' + str(A.UpLV)
        HV_up = 'Up Truck/Bus: ' + str(A.UpHV)
        str_down = 'CNT: ' + str(A.cnt_down)
        LV_down = 'Down Mobil: ' + str(A.DownLV)
        HV_down = 'Down Truck/Bus: ' + str(A.DownHV)
        frame = cv2.polylines(frame, [pts_L1], False, line_down_color, thickness=2)
        #frame = cv2.polylines(frame, [pts_L2], False, line_up_color, thickness=2)
        frame = cv2.polylines(frame, [pts_L3], False, (255, 255, 255), thickness=1)
        frame = cv2.polylines(frame, [pts_L4], False, (255, 255, 255), thickness=1)

        cv2.putText(frame, str_down, (10, 90), A.font,
                    2, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, str_down, (10, 90), A.font,
                    2, (255, 0, 0), 1, cv2.LINE_AA)

        #cv2.imshow('Frame', cv2.resize(frame, (400, 300)))
        #print(f'COUNT_{name}:', A.cnt_down)
        ret, jpeg = cv2.imencode('.jpg', frame)
        frame = jpeg.tobytes()
        lock[0] = 1
        while lock[0]:
            result[name] = A.cnt_down
            lock[0] = 0
        #print(result)
        yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

@router.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@router.route("/video_1", methods=["GET"])
def video_stream_one():
    x = gen_frame(cv2.VideoCapture("./src/static/videos/1t.mp4"), B(), 0)
    return Response(x, mimetype='multipart/x-mixed-replace; boundary=frame')

@router.route("/video_2", methods=["GET"])
def video_stream_two():
    x = gen_frame(cv2.VideoCapture("./src/static/videos/2t.mp4"), B(), 1)
    return Response(x, mimetype='multipart/x-mixed-replace; boundary=frame')

@router.route("/video_3", methods=["GET"])
def video_stream_three():
    x = gen_frame(cv2.VideoCapture("./src/static/videos/3t.mp4"), B(), 2)
    return Response(x, mimetype='multipart/x-mixed-replace; boundary=frame')

@router.route("/video_4", methods=["GET"])
def video_stream_four():
    x = gen_frame(cv2.VideoCapture("./src/static/videos/4t.mp4"), B(), 3)
    return Response(x, mimetype='multipart/x-mixed-replace; boundary=frame')

@router.route("/get-signal-time", methods=["GET"])
def get_signal_time():
    return jsonify(time=get_time(), count=result)
