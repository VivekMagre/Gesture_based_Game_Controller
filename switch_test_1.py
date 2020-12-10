import cv2
import math
import numpy as np
import pyautogui as pg
pg.FAILSAFE = False

cap=cv2.VideoCapture(0)


def HSV(crop_image,skin_range):
    gray = cv2.bilateralFilter(crop_image, 11, 17, 17)
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    hsv = cv2.cvtColor(blur, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, np.array([0, 40, 70]), np.array([20, 255, 255]))
    kernel = np.ones((5, 5))
    dilation = cv2.dilate(mask, kernel, iterations=1)
    erosion = cv2.erode(dilation, kernel, iterations=1)
    filtered = cv2.GaussianBlur(erosion, (3, 3), 0)
    ret1, thresh = cv2.threshold(filtered, 127, 255, 0)

    return thresh


def get_contours(image,ori_frame):
    contours,null=cv2.findContours(image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    palm_area=0
    min_area=500
    flag=None
    cnnn=contours
    cnt = None
    for (i, c) in enumerate(contours):
        area = cv2.contourArea(c)
        if area > palm_area:
            palm_area = area
            flag = i
    if flag is not None and palm_area > min_area:
        cnt = contours[flag]
        conto_max = cnt
        cpy=ori_frame.copy()
        cv2.drawContours(cpy, [cnt], 0, (0,0,255),2)
        return (cpy,cnt,palm_area)
    else:
        return image,None,min_area

def get_center(maxx_contt):
    if len(maxx_contt) == 0:
         return None
    M = cv2.moments(maxx_contt)
    cX = int(M["m10"] / M["m00"])
    cY = int(M["m01"] / M["m00"])
    return (cX, cY)

def get_defects(contooo,isl):
    cnt = contooo
    if len(cnt) == 0:
        return cnt
    points = []

    hull = cv2.convexHull(cnt, returnPoints=False)
    count_defects = 0

    top_end = tuple(cnt[cnt[:, :, 1].argmin()][0])
    extRight = tuple(cnt[cnt[:, :, 0].argmax()][0])
    extLeft = tuple(cnt[cnt[:, :, 0].argmin()][0])
    centre = get_center(cnt)

    x1=top_end[0];y1=top_end[1]
    x2=centre[0];y2=centre[1]

    if isl==0:
        x3=extLeft[0];y3=extLeft[1]
    if isl==1:
        x3=extRight[0];y3=extLeft[1]

    m1=(y2-y1)/(x2-x1)
    m2=(y3-y2)/(x3-x2)
    tan8=math.fabs((m2-m1)/(1+m1*m2));
    angle_sw=math.atan(tan8)*180/math.pi

    defects = cv2.convexityDefects(cnt, hull)
    for i in range(defects.shape[0]):
        s, e, f, d = defects[i, 0]
        start = tuple(cnt[s][0])
        end = tuple(cnt[e][0])
        far = tuple(cnt[f][0])
        points.append(end)

        a = math.sqrt((end[0] - start[0]) ** 2 + (end[1] - start[1]) ** 2)
        b = math.sqrt((far[0] - start[0]) ** 2 + (far[1] - start[1]) ** 2)
        c = math.sqrt((end[0] - far[0]) ** 2 + (end[1] - far[1]) ** 2)
        angle = (math.acos((b ** 2 + c ** 2 - a ** 2) / (2 * b * c)) * 180) / 3.14

        if angle <= 70:
            count_defects += 1
            cv2.circle(c, far, 3, [0, 0, 255], -1)

    return count_defects,angle_sw,top_end

def dist(a, b):
    return math.sqrt((a[0] - b[0])**2 + (b[1] - a[1])**2)

def gameMode(right_defect ,left_defect ):
    if right_defect <= 1 and left_defect >= 2:
        print('right_close And left_open ')
    elif right_defect >= 2 and left_defect <= 1:
        print('right_open And left_close ')
    elif right_defect >= 2 and left_defect >= 2:
        print('Both_open ')
    elif right_defect <= 1 and left_defect <= 1:
        print('Both_close')
    else:
        pass
    return

def mouseMode(a,click):
    if click>2:
        print('Click at',a)
    if click<2:
        print('move_mouse',a)
    return



def capture_histogram():
    cap = cv2.VideoCapture(0)
    while True:
        _, frame = cap.read()
        frame = cv2.flip(frame, 1)
        frame = cv2.resize(frame, (1000, 600))

        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(frame, "Place region of the hand inside box and press `A`",(5, 50), font, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.rectangle(frame, (500, 100), (580, 180), (105, 105, 105), 2)
        box = frame[105:175, 505:575]

        cv2.imshow("Capture Histogram", frame)
        key = cv2.waitKey(10)
        if key == 97:
            object_color = box
            cv2.destroyAllWindows()
            break
        if key == 27:
            cv2.destroyAllWindows()
            cap.release()
            break

    object_color_hsv = cv2.cvtColor(object_color, cv2.COLOR_BGR2HSV)
    object_hist = cv2.calcHist([object_color_hsv], [0, 1], None,
                               [12, 15], [0, 180, 0, 256])

    cv2.normalize(object_hist, object_hist, 0, 255, cv2.NORM_MINMAX)
    cap.release()
    return object_hist


skin = capture_histogram()
current_mode = 0
counter = 0
while cap.isOpened():

    # Capture frames from the camera

    ret, frame = cap.read()
    frame = cv2.flip(frame, 1)
    hsv = HSV(frame,skin)
    cv2.rectangle(frame, (300, 0), (640, 320), (255, 0, 0), 1)
    cv2.rectangle(frame, (000, 180), (300, 480), (0, 255, 0), 1)

    crop_right = hsv[0:320, 300:640]
    crop_left = hsv[180:480, 000:319]
    right_cont, max1 ,right_area= get_contours(crop_right, frame[0:320, 300:640])
    left_cont, max2,left_area = get_contours(crop_left, frame[180:480, 000:319])


    if max1 is not None and max2 is not None:

        #print('right_area',right_area)
        #print('left_area',left_area)
        right_defects,right_sw_angle,top_right = get_defects(max1,0)
        left_defects,left_sw_angle,_ = get_defects(max2,1)

        mouse_x = 6 * top_right[0]
        mouse_y = 6 * top_right[1]
        final_mouse = [mouse_x, mouse_y]

        if right_sw_angle >80 and left_sw_angle >80 :
           if left_defects<2 and right_defects<2:
               area_shrink = True
        else:
            area_shrink = False

        if  area_shrink==True and counter==0 :
            if current_mode==0 :
                mouseMode(final_mouse,left_defects)
                current_mode = 1

            else:
                gameMode(right_defects,left_defects)
                current_mode = 0
            counter = 20

        if current_mode==0:
            gameMode(right_defects,left_defects)
        if current_mode==1:
            mouseMode(final_mouse,left_defects)

        if counter != 0:
            counter -=1

        frame[0:320, 300:640] = right_cont
        frame[180:480, 000:319] = left_cont
        cv2.imshow('frame',frame)
        if cv2.waitKey(1) == ord('f'):
            break



    else:
        cv2.imshow('frame', frame)

        if cv2.waitKey(1) == ord('f'):
            break

cap.release()
cv2.destroyAllWindows()

