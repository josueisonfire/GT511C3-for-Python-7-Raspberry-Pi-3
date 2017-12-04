#!/usr/bin/env python

import fingerpi as fp
# from fingerpi import base

# import struct
import time
import pickle
import matplotlib.pyplot as plt
import numpy as np

def printByteArray(arr):
    return map(hex, list(arr))

f = fp.FingerPi()

print 'Opening connection...'
f.Open(extra_info = True, check_baudrate = True)

print 'Changing baudrate...'
f.ChangeBaudrate(115200)
# f.CmosLed(False)

while True:
    print 'Place the finger on the scanner and press <Enter>'
    _ = raw_input()
    f.CmosLed(True)
    # response = f.IsPressFinger()
    response = f.CaptureFinger()
    if response[0]['ACK']:
        break
    f.CmosLed(False)
    if response[0]['Parameter'] != 'NACK_FINGER_IS_NOT_PRESSED':
        print 'Unknown Error occured', response[0]['Parameter']
        
# print f.UsbInternalCheck()
        
print 'Image captured!'
f.CmosLed(False)

print 'Transmitting image...'
t = time.time()
raw_img = f.GetImage()
tx_time = time.time() - t
print raw_img[0]['ACK'],
print raw_img[1]['Checksum']
print 'Time to transmit:', tx_time

print 'Closing connection...'
f.Close()

with open('raw_img.pickle', 'w') as f:
    pickle.dump(raw_img, f)

time.sleep(5.5)

with open('raw_img.pickle', 'r') as f:
    raw_image = pickle.load(f)

dim = raw_image[1]['Data'][1]
img = bytearray(raw_image[1]['Data'][0])
print "Min, Max: ", (min(img), max(img))
print "Length:", len(img)

img = np.reshape(img, dim)
print "Dimensions: ", img.shape
fig = plt.imshow(img, cmap = 'gray')
fig.axes.get_xaxis().set_visible(False)
fig.axes.get_yaxis().set_visible(False)
plt.axis('off')

plt.savefig('demo_temp.png',
            bbox_inches='tight',
            pad_inches=-.1,
            frameon=False,
            transparent=False
)

