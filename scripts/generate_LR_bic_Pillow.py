from PIL import Image
import sys
import os

# import time
from glob import glob

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import util  # noqa: E402
from utils.progress_bar import ProgressBar  # noqa: E402


# LR, HR path
hr_path = "/content/dataset/unknownCelebA_set10/*"
lr_path = "/content/dataset/unknownCelebA_set10_val_50_x4/"
hr_list = sorted(glob(hr_path))

# Scale factor
ratio = 1 / 4
# Coefficient
a = -1 / 2
pbar = ProgressBar(len(hr_list))

util.mkdir(lr_path)

for index, value in enumerate(hr_list):
    pbar.update("Read {}".format(value))
    sys.stdout.flush()
    # Read image
    img = Image.open(value, "r")
    dst = img.resize((tuple([int(x * ratio) for x in img.size])), Image.BICUBIC)
    dst.save(lr_path + os.path.basename(value))

print("Completed!")
