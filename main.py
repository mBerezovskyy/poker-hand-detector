import os

import cv2
import cvzone
import pytesseract
import numpy as np
import re

from poker_engine import check_hand, get_best_hand, get_higher_card

img_orig = cv2.imread('testing_images/card10.jpg')

img_resized_orig = cv2.resize(src=img_orig, dsize=None, dst=None, fx=0.35, fy=0.35)


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

    return correct_order


def transform_points(points, img):
    tl = points['tl']
    bl = points['bl']
    br = points['br']
    tr = points['tr']

    right_height = abs(tr[1] - br[1])
    left_height = abs(tl[1] - bl[1])
    height = max(right_height, left_height)

    top_width = abs(tr[0] - tl[0])
    bottom_width = abs(br[0] - bl[0])
    width = max(top_width, bottom_width)

    dst = np.array([[0, 0],
                    [0, height],
                    [width, 0],
                    [width, height]], dtype=np.float32)

    pts = np.array([tl,
                    bl,
                    tr,
                    br], dtype=np.float32)

    M = cv2.getPerspectiveTransform(pts, dst)
    warped = cv2.warpPerspective(img, M, (width, height))

    return warped


def get_suit_shapes():
    suit_img_path = os.path.join(os.getcwd(), 'suits')

    shapes = {}

    for suit_img in os.listdir(suit_img_path):
        suit = suit_img.split('.')[0]

        img = cv2.imread(os.path.join(suit_img_path, suit_img), 0)

        blured_img = cv2.GaussianBlur(src=img, ksize=(5, 5), sigmaX=1)

        ret, thresh = cv2.threshold(src=blured_img, thresh=127, maxval=255, type=cv2.THRESH_BINARY)

        thresh = cv2.bitwise_not(src=thresh)

        contours, hierarchy = cv2.findContours(image=thresh, mode=cv2.RETR_TREE, method=cv2.CHAIN_APPROX_SIMPLE)

        contours = sorted(contours, key=lambda c: cv2.contourArea(c), reverse=True)

        shapes[suit] = contours[0]

    return shapes


def detect_suit(img):
    H, W, C = img.shape
    width_cropped = W // 5
    height_cropped = H // 4
    suit_and_number_part = img[25:height_cropped, 0:width_cropped]

    suit_shapes = get_suit_shapes()

    image = cv2.cvtColor(suit_and_number_part, cv2.COLOR_BGR2HSV)
    lower = np.array([0, 98, 0])
    upper = np.array([179, 255, 255])
    mask = cv2.inRange(image, lower, upper)
    result = cv2.bitwise_and(suit_and_number_part, suit_and_number_part, mask=mask)
    result = cv2.cvtColor(src=result, code=cv2.COLOR_BGR2GRAY)

    card_gray = cv2.cvtColor(src=img, code=cv2.COLOR_BGR2GRAY)
    ret, thresh = cv2.threshold(src=card_gray, thresh=127, maxval=255, type=cv2.THRESH_BINARY)
    kernel = np.ones((3, 3), np.uint8)
    eroded = cv2.erode(src=thresh, kernel=kernel, iterations=1)

    number_of_black_pixels = (W * H) - cv2.countNonZero(src=eroded)
    percentage_of_black = number_of_black_pixels / (W * H) * 100

    if percentage_of_black > 62:
        return 'card_back'

    number_of_white_pixels = cv2.countNonZero(src=result)
    warped_image_gray = cv2.cvtColor(src=suit_and_number_part, code=cv2.COLOR_BGR2GRAY)
    ret, thresh = cv2.threshold(src=warped_image_gray, thresh=150, maxval=255, type=cv2.THRESH_BINARY)
    thresh = cv2.bitwise_not(src=thresh)

    contours, hierarchy = cv2.findContours(image=thresh, mode=cv2.RETR_LIST, method=cv2.CHAIN_APPROX_NONE)
    contours = sorted(contours, key=lambda c: cv2.contourArea(c), reverse=True)

    if number_of_white_pixels > 200:
        heart_shape = suit_shapes['heart']
        diamond_shape = suit_shapes['diamond']

        heart_similarity = min(
            [cv2.matchShapes(contour1=heart_shape, contour2=c, method=1, parameter=0.0) for c in contours[:2]])

        diamond_similarity = min([cv2.matchShapes(contour1=diamond_shape, contour2=c, method=1, parameter=0.0) for c in
                                  contours[:2]])
        suit = {
            heart_similarity: 'heart',
            diamond_similarity: 'diamond',
        }

        return suit[min(heart_similarity, diamond_similarity)]

    else:
        spade_shape = suit_shapes['spade']
        club_shape = suit_shapes['club']

        spade_similarity = min(
            [cv2.matchShapes(contour1=spade_shape, contour2=c, method=1, parameter=0.0) for c in contours[:2]])

        club_similarity = min([cv2.matchShapes(contour1=club_shape, contour2=c, method=1, parameter=0.0) for c in
                               contours[:2]])

        suit = {
            spade_similarity: 'spade',
            club_similarity: 'club'
        }

        # print(f'spade_similarity: {spade_similarity}')
        # print(f'club_similarity: {club_similarity}')
        # print(f'card_back_similarity: {card_back_similarity}')

        # cv2.waitKey(0)

        return suit[min(spade_similarity, club_similarity)]


def detect_number(img, suit):
    if suit == 'card_back':
        return ''

    h, w, c = img.shape

    width_cropped = w // 6
    height_cropped = h // 5

    number_part = img[0:height_cropped, 0:width_cropped]

    number_part_gray = cv2.cvtColor(src=number_part, code=cv2.COLOR_BGR2GRAY)

    number_part_gray = cv2.resize(number_part_gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

    blur = cv2.GaussianBlur(src=number_part_gray, ksize=(3, 3), sigmaX=0)

    thresh = cv2.adaptiveThreshold(src=blur, maxValue=255, adaptiveMethod=cv2.ADAPTIVE_THRESH_MEAN_C,
                                   thresholdType=cv2.THRESH_BINARY, blockSize=13, C=7)

    kernel = np.ones((3, 3), np.uint8)

    dilate = cv2.erode(src=thresh, kernel=kernel, iterations=1)

    custom_oem_psm_config = r'--oem 3 --psm 8'
    res = pytesseract.image_to_string(dilate, config=custom_oem_psm_config)

    res = re.sub('[^A-Za-z0-9]+', '', res)

    high_order_cards = ['J', 'Q', 'K', 'A']

    for card in high_order_cards:
        if card in res:
            return card

    return res.strip()


def locate_cards(img):
    img_gray = cv2.cvtColor(src=img, code=cv2.COLOR_BGR2GRAY)

    clahe = cv2.createCLAHE(clipLimit=1.0, tileGridSize=(9, 9))
    equalized = clahe.apply(img_gray)

    blur = cv2.GaussianBlur(src=equalized, ksize=(7, 7), sigmaX=0)

    thresh = cv2.adaptiveThreshold(src=blur, maxValue=255, adaptiveMethod=cv2.ADAPTIVE_THRESH_MEAN_C,
                                   thresholdType=cv2.THRESH_BINARY, blockSize=7, C=3)
    thresh = cv2.bitwise_not(src=thresh)

    contours, hierarchy = cv2.findContours(image=thresh, mode=cv2.RETR_EXTERNAL, method=cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=lambda c: cv2.contourArea(c), reverse=True)

    present_cards = {}

    for idx, c in enumerate(contours):
        area = cv2.contourArea(c)

        if 20_000 < area < 150_000:
            x, y, w, h = cv2.boundingRect(c)

            epsilon = 0.03 * cv2.arcLength(curve=c, closed=True)

            corner_points = cv2.approxPolyDP(curve=c, epsilon=epsilon, closed=True)
            formatted_points = format_points(corner_points)
            ordered_points = order_points(formatted_points)
            warped_image = transform_points(ordered_points, img)

            suit = detect_suit(warped_image)
            number = detect_number(warped_image, suit)

            if suit == 'card_back':
                continue

            correct_format = suit[0].upper() + number
            present_cards[correct_format] = idx

    combinations = check_hand(present_cards.keys())
    best_hand = get_best_hand(combinations)

    if best_hand[1]:
        best_hand_cards = combinations[best_hand[1]]
        for card in best_hand_cards:
            contour_idx = present_cards[card]
            cv2.drawContours(image=img, contours=contours, contourIdx=contour_idx, color=(255, 0, 0), thickness=3)

        combination = best_hand_cards
    else:
        higher_card = get_higher_card(present_cards.keys())
        contour_idx = present_cards[higher_card]
        cv2.drawContours(image=img, contours=contours, contourIdx=contour_idx, color=(255, 0, 0), thickness=3)
        combination = 'Higher card'

    cvzone.putTextRect(img=img, text=f'{combination}', pos=(10, 30), scale=2, thickness=2, colorR=(255, 130, 0))

    cv2.imshow('cards', img)


locate_cards(img_resized_orig)
cv2.waitKey(0)
