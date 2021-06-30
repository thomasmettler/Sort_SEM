# -*- coding: utf-8 -*-
"""
Created on Thu Jun 17 11:10:56 2021

@author: thomas.mettler
"""
import sys
import exifread
import os
from matplotlib import pyplot as plt
import matplotlib
from matplotlib.patches import Rectangle
import numpy as np
import cv2
import sys
import re

verbose = 0 # set 1 for debug, else 0

def drawBoundingBoxes(imageData, imageOutputPath, inferenceResults, color):
    """Draw bounding boxes on an image.
    imageData: image data in numpy array format
    imageOutputPath: output image file path
    inferenceResults: inference results array off object (l,t,w,h)
    colorMap: Bounding box color candidates, list of RGB tuples.
    """
    for res in inferenceResults:
        left = float(res['left'])
        top = float(res['top'])
        right = float(res['left']) + float(res['width'])
        bottom = float(res['top']) + float(res['height'])
        label = res['label']
        xLength = float(res['HFW'])
        yLength = float(res['VFW'])
        X0 = float(res['X0'])
        Y0 = float(res['Y0'])
        imgHeight, imgWidth, _ = imageData.shape
        thick = int((imgHeight + imgWidth) // 900)
        #print(left, top, right, bottom)
        left_c = int((left - X0)/xLength * imgWidth)
        top_c = int((top - Y0)/yLength * imgHeight)
        right_c = int((right - X0)/xLength * imgWidth)
        bottom_c = int((bottom - Y0)/yLength * imgHeight)
        #print(left_c, top_c, right_c, bottom_c)
        cv2.rectangle(imageData,(left_c, top_c), (right_c, bottom_c), color, thick)
        cv2.putText(imageData, label, (left_c, top_c - 12), 0, 1e-3 * imgHeight, color, thick//3)
    cv2.imwrite(imageOutputPath, imageData)

def sort_human(l):
    convert = lambda text: float(text) if text.isdigit() else text
    alphanum = lambda key: [convert(c) for c in re.split('([-+]?[0-9]*\.?[0-9]*)', key)]
    l.sort(key=alphanum)
    return l

# Open image file for reading (binary mode)
path = r'C:\Users\thomas.mettler\OneDrive - Leister Group\Desktop\MOE\SEM\data\20210525_BIB_AA_Wfr8_X15Y12'
#path = input('Please give the path to the tif files:')

print('Path: ',path)
stages = ["StageX", "StageY", "StageZ"] # ,'StageR']
lengths = ["HFW", "VFW"] # ,'StageR']

Nav_count = -1

list_of_files = []
list_of_names = []
list_of_tifs = []

for root, dirs, files in os.walk(path):
    for file in files:
        list_of_files.append(os.path.join(root,file))
        if(file[-3:] == 'tif'):
            list_of_names.append(file)
for name in list_of_files:
    if(name[-3:] == 'tif'):
        list_of_tifs.append(name)

#print(list_of_tifs)
#print(list_of_names)

sort_human(list_of_names)
print('File list: ', list_of_names)

report = ''

x_values = np.zeros((len(list_of_tifs)))
y_values = np.zeros((len(list_of_tifs)))
z_values = np.zeros((len(list_of_tifs)))
h_len = np.zeros((len(list_of_tifs)))
v_len = np.zeros((len(list_of_tifs)))

counter = 0
for f_x, file_name in enumerate(list_of_tifs):
    a = file_name.find("CCD")
    if(a==-1):
        f = open(file_name, 'rb')
        tags = exifread.process_file(f)
        values = []    
        values2 = [] 
        #print(file_name)
        for tag in tags.keys():
            if tag not in ('JPEGThumbnail', 'TIFFThumbnail', 'Filename', 'EXIF MakerNote'):
                if(tag == 'Image Tag 0x877A'):
                    for i,stage in enumerate(stages):
                        message = str(tags[tag])
                        a = message.find(stages[i])
                        if(verbose):print(message[a:a+18])
                        values.append(float(message[a+7:a+17]))
                    # value by value
                    message = str(tags[tag])
                    a = message.find("HFW")
                    if(a!=-1):
                        if(verbose):print(message[a:a+14])
                        values2.append(float(message[a+4:a+14]))
                    else:
                        print("HFW not found")
                        values2.append(0.0)
                    
                    message = str(tags[tag])
                    a = message.find("VFW")
                    if(a!=-1):
                        if(verbose):print(message[a:a+15])
                        values2.append(float(message[a+4:a+15]))
                    else:
                        if(verbose):print("VFW not found")
                        values2.append(0.0)
                    if(file_name.find("Nav-Cam")!=-1):
                        Nav_count = f_x - counter
    
        report += file_name+'\n'
        #print(file_name)
        #print('Stage positions:')
        x_values[f_x] = values[0]
        y_values[f_x] = values[1]
        z_values[f_x] = values[2]
        h_len[f_x] = values2[0]
        v_len[f_x] = values2[1]
        for i,stage in enumerate(stages):
            to_string = stage + ': '+str(values[i])+'\n'
            report += to_string
            #print(stage + ': ',values[i])
        for i,length in enumerate(lengths):
            to_string = length + ': '+str(values2[i])+'\n'
            report += to_string
            #print(stage + ': ',values[i])
        report += '\n'
    else:
        if(verbose):print('CCD side view picture')
        counter+=1



img = cv2.imread(list_of_tifs[Nav_count])
if(verbose):print(list_of_tifs[Nav_count])
height, width, channels = img.shape
if(verbose):print(height, width, channels)



#cv2.rectangle(img, (307, 204), (1307, 1204), (0, 0, 255), 3)

color = (0, 0, 255) # red
results = []
for i,x in enumerate(x_values):
    if(x!=0):
        print(list_of_names[i][9:11].replace('_',''))
        results += [{"left": (x_values[i]-h_len[i]/2.0),\
                    "top": y_values[i]+v_len[i]/2.0,\
                    "width": h_len[i],\
                    "height": v_len[i],\
                    "label": list_of_names[i][9:11].replace('_',''),\
                    "HFW": h_len[Nav_count], "VFW": v_len[Nav_count],\
                    "X0":x_values[Nav_count]-h_len[Nav_count]/2.0, "Y0":y_values[Nav_count]-v_len[Nav_count]/2.0}]
    
drawBoundingBoxes(img, path+r'/Nav-Cam_Positions.png', results, color)
print('Produced output picture: '+'Nav-Cam_Positions.png')
cv2.imshow("bounding_box", img)

#plot the squares at matplot
# find max/min in XY (+20%)
print(np.min(x_values))
x_min = np.min(x_values)
x_max = np.max(x_values)
x_len = x_max - x_min
x_increase = x_len * 0.1

y_min = np.min(y_values)
y_max = np.max(y_values)
y_len = y_max - y_min
y_increase = y_len * 0.1

scale = round(5.0/x_len)
print(scale)

fig, ax = plt.subplots()
fig.set_figheight(10)
fig.set_figwidth(10)
ax.scatter(x_values,y_values)
for i,x in enumerate(x_values):
    plt.text(x_values[i]-h_len[i]/1.9, y_values[i]-v_len[i]/1.9, list_of_names[i][9:11].replace('_',''),color ='red')
    ax.add_patch( Rectangle((x_values[i]-h_len[i]/2.0, y_values[i]-v_len[i]/2.0),
                        h_len[i], v_len[i], fc='none', color ='black',
                        linewidth = 2, edgecolor='r', facecolor="none") )
plt.xlabel("X-AXIS [m]")
plt.ylabel("Y-AXIS [m]")
plt.title(path)
plt.show()
plt.savefig(path+r"\mat_plot_positions.png") #save as png

# print all the files in the path as well as the stage positions      
#print(report)
# store the infos in a txt file at the path given
myText = open(path+r'\tif_file_reports.txt','w')
myText.write(report)
myText.close()

