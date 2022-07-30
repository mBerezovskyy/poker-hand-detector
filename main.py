import cv2
import cvzone
import numpy as np

img_orig = cv2.imread('testing_images/card6.jpg')
img_gray = cv2.cvtColor(src=img_orig, code=cv2.COLOR_BGR2GRAY)

img_resized_gray = cv2.resize(src=img_gray, dsize=None, dst=None, fx=0.35, fy=0.35)
img_resized_orig = cv2.resize(src=img_orig, dsize=None, dst=None, fx=0.35, fy=0.35)

equalized = cv2.equalizeHist(src=img_resized_gray)

blur = cv2.GaussianBlur(src=equalized, ksize=(7, 7), sigmaX=0)

thresh = cv2.adaptiveThreshold(src=blur, maxValue=255, adaptiveMethod=cv2.ADAPTIVE_THRESH_MEAN_C,
                               thresholdType=cv2.THRESH_BINARY, blockSize=5, C=3)
thresh = cv2.bitwise_not(src=thresh)

contours, hierarchy = cv2.findContours(image=thresh, mode=cv2.RETR_EXTERNAL, method=cv2.CHAIN_APPROX_SIMPLE)
contours = sorted(contours, key=lambda c: cv2.contourArea(c), reverse=True)

points = {}


def format_points(points):
    points_formatted = []
    for point in points:
        points_formatted.append([point[0][0], point[0][1]])
    return np.array(points_formatted)


def order_points(points):
    sorted_points = points[np.argsort(points[:, 0]), :]

    left_points = sorted_points[:2]
    right_points = sorted_points[2:]

    min_sum = np.min(np.sum(left_points, axis=1))
    max_sum = np.max(np.sum(right_points, axis=1))

    top_left_point_idx = np.where(np.sum(left_points, axis=1) == min_sum)[0][0]
    bottom_right_point_idx = np.where(np.sum(right_points, axis=1) == max_sum)[0][0]

    correct_order = {
        'tl': left_points[top_left_point_idx],
        'bl': left_points[int(not top_left_point_idx)],
        'br': right_points[bottom_right_point_idx],
        'tr': right_points[int(not bottom_right_point_idx)],
    }

    for key, val in correct_order.items():
        cvzone.putTextRect(
            img=img_resized_orig,
            text=f'{key}',
            pos=(val[0], val[1] - 10),
            scale=2,
            thickness=1,
            offset=2
        )

    return correct_order


def locate_cards():
    for idx, c in enumerate(contours):
        area = cv2.contourArea(c)

        if 20_000 < area < 100_000:
            x, y, w, h = cv2.boundingRect(c)

            cv2.drawContours(image=img_resized_orig, contours=contours, contourIdx=idx, color=(0, 255, 0),
                             thickness=2)
            #
            # cvzone.putTextRect(img=img_resized_orig, text=str(area), pos=(x, y))

            epsilon = 0.03 * cv2.arcLength(curve=c, closed=True)

            corner_points = cv2.approxPolyDP(curve=c, epsilon=epsilon, closed=True)

            formatted_points = format_points(corner_points)
            print(order_points(formatted_points))

            for point in corner_points:
                cv2.circle(
                    img=img_resized_orig,
                    center=(point[0][0], point[0][1]),
                    radius=4,
                    color=(0, 0, 255),
                    thickness=-1
                )


locate_cards()

cv2.imshow('img_resized_orig', img_resized_orig)
cv2.waitKey(0)
