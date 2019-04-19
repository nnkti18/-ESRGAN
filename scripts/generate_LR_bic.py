import cv2
import numpy as np
import math
import sys
import time
from glob import glob

from utils.progress_bar import ProgressBar
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Interpolation kernel
def u(s, a):
    if (abs(s) >= 0) & (abs(s) <= 1):
        return (a + 2) * (abs(s) ** 3) - (a + 3) * (abs(s) ** 2) + 1
    elif (abs(s) > 1) & (abs(s) <= 2):
        return a * (abs(s) ** 3) - (5 * a) * (abs(s) ** 2) + (8 * a) * abs(s) - 4 * a
    return 0


# flake8: noqa
# Padding
def padding(img, H, W, C):
    zimg = np.zeros((H + 4, W + 4, C))
    zimg[2 : H + 2, 2 : W + 2, :C] = img
    # Pad the first/last two col and row
    zimg[2 : H + 2, 0:2, :C] = img[:, 0:1, :C]
    zimg[H + 2 : H + 4, 2 : W + 2, :] = img[H - 1 : H, :, :]
    zimg[2 : H + 2, W + 2 : W + 4, :] = img[:, W - 1 : W, :]
    zimg[0:2, 2 : W + 2, :C] = img[0:1, :, :C]
    # Pad the missing eight points
    zimg[0:2, 0:2, :C] = img[0, 0, :C]
    zimg[H + 2 : H + 4, 0:2, :C] = img[H - 1, 0, :C]
    zimg[H + 2 : H + 4, W + 2 : W + 4, :C] = img[H - 1, W - 1, :C]
    zimg[0:2, W + 2 : W + 4, :C] = img[0, W - 1, :C]
    return zimg


# https://github.com/yunabe/codelab/blob/master/misc/terminal_progressbar/progress.py
def get_progressbar_str(progress):
    # END = 170
    MAX_LEN = 30
    BAR_LEN = int(MAX_LEN * progress)
    return (
        "Progress:["
        + "=" * BAR_LEN
        + (">" if BAR_LEN < MAX_LEN else "")
        + " " * (MAX_LEN - BAR_LEN)
        + "] %.1f%%" % (progress * 100.0)
    )


# Bicubic operation
def bicubic(img, ratio, a):
    # Get image size
    H, W, C = img.shape

    img = padding(img, H, W, C)
    # Create new image
    dH = math.floor(H * ratio)
    dW = math.floor(W * ratio)
    dst = np.zeros((dH, dW, 3))

    h = 1 / ratio

    print("Start bicubic interpolation")
    print("It will take a little while...")
    inc = 0
    for c in range(C):
        for j in range(dH):
            for i in range(dW):
                x, y = i * h + 2, j * h + 2

                x1 = 1 + x - math.floor(x)
                x2 = x - math.floor(x)
                x3 = math.floor(x) + 1 - x
                x4 = math.floor(x) + 2 - x

                y1 = 1 + y - math.floor(y)
                y2 = y - math.floor(y)
                y3 = math.floor(y) + 1 - y
                y4 = math.floor(y) + 2 - y

                mat_l = np.matrix([[u(x1, a), u(x2, a), u(x3, a), u(x4, a)]])
                mat_m = np.matrix(
                    [
                        [
                            img[int(y - y1), int(x - x1), c],
                            img[int(y - y2), int(x - x1), c],
                            img[int(y + y3), int(x - x1), c],
                            img[int(y + y4), int(x - x1), c],
                        ],
                        [
                            img[int(y - y1), int(x - x2), c],
                            img[int(y - y2), int(x - x2), c],
                            img[int(y + y3), int(x - x2), c],
                            img[int(y + y4), int(x - x2), c],
                        ],
                        [
                            img[int(y - y1), int(x + x3), c],
                            img[int(y - y2), int(x + x3), c],
                            img[int(y + y3), int(x + x3), c],
                            img[int(y + y4), int(x + x3), c],
                        ],
                        [
                            img[int(y - y1), int(x + x4), c],
                            img[int(y - y2), int(x + x4), c],
                            img[int(y + y3), int(x + x4), c],
                            img[int(y + y4), int(x + x4), c],
                        ],
                    ]
                )
                mat_r = np.matrix([[u(y1, a)], [u(y2, a)], [u(y3, a)], [u(y4, a)]])
                dst[j, i, c] = np.dot(np.dot(mat_l, mat_m), mat_r)

                # Print progress
                inc = inc + 1
                sys.stderr.write("\r\033[K" + get_progressbar_str(inc / (C * dH * dW)))
                sys.stderr.flush()
    sys.stderr.write("\n")
    sys.stderr.flush()
    return dst


# LR, HR path
hr_path = "/content/dataset/img_align_celeba_png_set_1_HR/*"
lr_path = "/content/dataset/img_align_celeba_png_set_1_LR_x4/"
hr_list = sorted(glob(hr_path))

# Scale factor
ratio = 1 / 4
# Coefficient
a = -1 / 2
pbar = ProgressBar(len(hr_list))

for index, value in enumerate(hr_list):
    pbar.update("Read {}".format(v))
    # Read image
    img = cv2.imread(value)
    dst = bicubic(img, ratio, a)
    cv2.imwrite(lr_path + value, dst)

print("Completed!")
