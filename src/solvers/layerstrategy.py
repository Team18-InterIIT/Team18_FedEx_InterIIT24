import csv
from data_analysis import *
import collections
import pandas as pd


ULDs = {
    1: {"dimensions": (224,318,162), "weight_limit": 2500},
    2: {"dimensions": (224,318,162), "weight_limit": 2500},
    3: {"dimensions": (244,318,244), "weight_limit": 2800},
    4: {"dimensions": (244,318,244), "weight_limit": 2800},
    5: {"dimensions": (244,318,285), "weight_limit": 3500},
    6: {"dimensions": (244,318,285), "weight_limit": 3500},
}
packages=[]

filePath='data.csv'
with open(filePath, 'r', newline='', encoding='utf-8') as file:
        csv_reader = list(csv.reader(file))
        k = int(csv_reader[0][0])
        for row in csv_reader:
            if(row):
                if(row[0][0]=="P"):
                      packages.append(row)
     

dimension_frequency = collections.Counter()
for pkg in packages:
    l, b, h = pkg[1:4]
    dimension_frequency[l] += 1
    dimension_frequency[b] += 1
    dimension_frequency[h] += 1



def selectboxes_2d(dimension, package):
    selected=[]
    area=0
    for pkg in package:
            l=int(pkg[1])
            b=int(pkg[2])
            h=int(pkg[3])
            m=int(pkg[4])
            
            if(l==dimension):
               selected.append((pkg[0],b,h,m))
               area+=b*h
            elif(b==dimension):
                selected.append((pkg[0],l,h,m))
                area+=l*h
            elif(h==dimension):
               selected.append((pkg[0],l,b,m))
               area+=l*b
            
    return selected



class Rect:
    def _init_(self,x=0,y=0, w=0, h=0):
        self.x = 0  # x-coordinate of the rectangle's top-left corner
        self.y = 0  # y-coordinate of the rectangle's top-left corner
        self.w = w  # width of the rectangle
        self.h = h  # height of the rectangle
        self.wasPacked = False  # flag to track if the rectangle is packed

def pack_rects_in_container(rects, container_width, container_height):
    # Create a grid to represent the container, initialized to False (empty)
    container = [[False for _ in range(container_width)] for _ in range(container_height)]
    rects.sort(key=lambda rect: rect.h, reverse=True)
    a=0;
    A=container_height*container_width
    
    for rect in rects:
        if rect.wasPacked:
            continue  # Skip packed rectangles
        else:
            packed = False

            # Try to find an empty spot for the rectangle
            for y in range(container_height - rect.h + 1):
                if rect.wasPacked:
                    break
                for x in range(container_width - rect.w + 1):
                    if rect.wasPacked:
                        break
                    can_fit = True
                    # Check if the rectangle fits in the current position (no overlap)
                    for iy in range(y, y + rect.h):
                        if rect.wasPacked:
                            break
                        for ix in range(x, x + rect.w):
                            if rect.wasPacked:
                                break
                            if container[iy][ix]:  # If any pixel is already occupied
                                can_fit = False
                                break
                        if not can_fit:
                            break

                    # If the rectangle fits, place it in the container
                    if can_fit:
                        # Mark the occupied cells in the container as True
                        for iy in range(y, y + rect.h):
                            for ix in range(x, x + rect.w):
                                container[iy][ix] = True
                        
                        # Set rectangle's packed status and position
                        rect.x = x
                        rect.y = y
                        rect.wasPacked = True  # Mark it as packed
                        packed = True
                        print(f"Packed rectangle {rect.w}x{rect.h} at position ({x}, {y})")
                        break  # No need to check further once packed

        # If the rectangle could not be packed, mark it as not packed
            if not packed:
                print(f"Rectangle {rect.w}x{rect.h} could not be packed.")
                rect.wasPacked = False
            
            else:
                rect.wasPacked=True
                a+=rect.w*rect.h
    print(a/A)

    return rects  

# Define some rectangles
selected =selectboxes_2d(74,packages)
rectangles=[]
for pkg in selected:
    rectangles.append(Rect(w=int(pkg[1]),h=int(pkg[2])))

# Define the container size
container_width = ULDs[1]['dimensions'][0]
container_height = ULDs[1]['dimensions'][1]

# Pack the rectangles in the container
packed_rects = pack_rects_in_container(rectangles, container_width, container_height)