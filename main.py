import cv2
import cvzone

img_orig = cv2.imread('testing_images/card5.jpg')
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

for idx, c in enumerate(contours):
    area = cv2.contourArea(c)

    if 20_000 < area < 100_000:
        x, y, w, h = cv2.boundingRect(c)

        cv2.drawContours(image=img_resized_orig, contours=contours, contourIdx=idx, color=(0, 255, 0),
                         thickness=2)

        cvzone.putTextRect(img=img_resized_orig, text=str(area), pos=(x, y))

        epsilon = 0.03 * cv2.arcLength(curve=c, closed=True)

        points = cv2.approxPolyDP(curve=c, epsilon=epsilon, closed=True)


cv2.imshow('img_resized_orig', img_resized_orig)
cv2.waitKey(0)
