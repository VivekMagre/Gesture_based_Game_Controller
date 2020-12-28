import cv2
import math
import pyautogui as pg
import time
pg.FAILSAFE = False

cap=cv2.VideoCapture(0)


def HSV(crop_image,skin_range):

    hsv_frame = cv2.cvtColor(crop_image, cv2.COLOR_BGR2HSV)
    object_segment = cv2.calcBackProject([hsv_frame], [0, 1], skin_range, [0, 180, 0, 256], 1)
    disc = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
    cv2.filter2D(object_segment, -1, disc, object_segment)
    _, segment_thresh = cv2.threshold(object_segment, 70, 255, cv2.THRESH_BINARY)

    return segment_thresh

def capture_histogram():
    cap = cv2.VideoCapture(0)
    while True:
        _, frame = cap.read()
        frame = cv2.flip(frame, 1)
        frame = cv2.resize(frame, (1000, 600))

        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(frame, "Place region of the hand inside box and press `A`",(5, 50), font, 0.7, (0, 0, 255), 2, cv2.LINE_AA)
        cv2.rectangle(frame, (500, 100), (580, 180), (0, 0, 255), 2)
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
    object_hist = cv2.calcHist([object_color_hsv], [0, 1], None,[12, 15], [0, 180, 0, 256])

    cv2.normalize(object_hist, object_hist, 0, 255, cv2.NORM_MINMAX)
    cap.release()
    return object_hist



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
        x3=extRight[0];y3=extRight[1]

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

        if angle <= 60:
            count_defects += 1


    return count_defects,angle_sw,top_end

def dist(a, b):
    return math.sqrt((a[0] - b[0])**2 + (b[1] - a[1])**2)


def get_center(maxx_contt):
    if len(maxx_contt) == 0:
         return None
    M = cv2.moments(maxx_contt)
    cX = int(M["m10"] / M["m00"])
    cY = int(M["m01"] / M["m00"])
    return (cX, cY)


def gameMode(right_defect ,left_defect ,left_drift,right_drift ):
    previous_key= 'q'
    if right_defect >= 2 and left_defect >= 2:
        pg.keyDown('f')
        time.sleep(0.005)
        pg.keyUp('f')

        #print('Both_open ')
    elif right_defect <= 1 and left_defect >= 2:
        pg.keyDown('a')
        time.sleep(0.005)
        pg.keyUp('a')

        #print('right_close And left_open ')
    elif right_defect >= 2 and left_defect <= 1:
        pg.keyDown('d')
        time.sleep(0.005)
        pg.keyUp('d')

        #print('right_open And left_close ')
    elif left_drift ==True and right_defect <= 1:
        if previous_key!='ea':
            pg.keyDown('e')
            time.sleep(0.005)
            pg.keyUp('e')
        pg.keyDown('a')
        time.sleep(0.02)
        pg.keyUp('a')
        previous_key='ea'
        #print('drifyt and left')
    elif right_drift ==True and left_defect <= 1:
        if previous_key != 'ed':
            pg.keyDown('e')
            time.sleep(0.005)
            pg.keyUp('e')
        pg.keyDown('d')
        time.sleep(0.02)
        pg.keyUp('d')
        previous_key='ed'
        #print('drift and right')
    else:
        pass
    return



def mouseMode(a,click):
    if click>2:
        pg.click()
        #print('Click at',a)
    if click<2:
        pg.moveTo(a)
        #print('move_mouse',a)
    return




skin = capture_histogram()
current_mode = 0
counter = 0

while cap.isOpened():

    # Capture frames from the camera
    left_drifts = False
    right_drifts = False

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


        if right_sw_angle >80 :
            right_drifts=True
        if left_sw_angle >80 :
            left_drifts=True


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
                #pg.hotkey('esc')
                mouseMode(final_mouse,left_defects)
                current_mode = 1
                pg.hotkey('esc')
            else:
                gameMode(right_defects,left_defects,left_sw_angle,right_sw_angle)
                current_mode = 0
            counter = 20

        if current_mode==0:
            gameMode(right_defects,left_defects,left_drifts,right_drifts)
        if current_mode==1:
            mouseMode(final_mouse,left_defects)

        if counter != 0:
            counter -=1

        frame[0:320, 300:640] = right_cont
        frame[180:480, 000:319] = left_cont
        cv2.imshow('frame',frame)
        if cv2.waitKey(1) == ord('m'):
            break



    else:
        cv2.imshow('frame', frame)

        if cv2.waitKey(1) == ord('m'):
            break

cap.release()
cv2.destroyAllWindows()

