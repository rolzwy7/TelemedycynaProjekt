from pprint import pprint
from PIL import Image
import math
import os
import random
import json
import random

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("dirpath")
parser.add_argument("K", type=int)
args = parser.parse_args()

K = args.K # K klas
dirpath = args.dirpath

def random_color():
    return "#" + hex(random.randint(0, int('ffffff', 16)))[2:]

RESULT_FILE = "result.json"

DEBUG_COLOR = 125

PIXEL_LOOP = 14
# PIXEL_LOOP = 30

DEBUG = False

_print = print

def print(*args, **kwargs):
    if DEBUG:
        _print(*args, **kwargs)


class Tracker():
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
        self.max_radius = 0
        self.max_radius_x = 0
        self.max_radius_y = 0
        self.max_radius_z = 0
    
    def is_dead(self, im):
        """
            check if tracker is dead (positioned on black pixel)
        """
        return im.getpixel((self.x, self.y)) == 0

    def center_myself(self, im, mark_spot=False):
        """
            Center tracker inside white space
        """
        x = self.x
        y = self.y
        top = self.get_distance_top(im, x, y)
        right = self.get_distance_right(im, x, y)
        bottom = self.get_distance_bottom(im, x, y)
        left = self.get_distance_left(im, x, y)

        if bottom >= top:
            self.y += int((top+bottom)/2) - top
        if top >= bottom:
            self.y -= int((top+bottom)/2) - bottom
        if right >= left:
            self.x += int((right+left)/2) - left
        if left >= right:
            self.x -= int((right+left)/2) - right
        
        self.c_x = self.x
        self.c_y = self.y
        
        # print("[*] Found center:", (self.x, self.y))
        # print("\tradius :", self.calc_radius(im))

        self.calc_radius(im)

        if mark_spot:
            self.debug_draw_cross(im)

    def debug_draw_cross(self, im, size=10):
        """
            Draw debug grey cross
        """
        x = self.x
        y = self.y
        for i in range(size):
            im.putpixel((x,y), DEBUG_COLOR)
            im.putpixel((x+i,y), DEBUG_COLOR)
            im.putpixel((x-i,y), DEBUG_COLOR)
            im.putpixel((x,y+i), DEBUG_COLOR)
            im.putpixel((x,y-i), DEBUG_COLOR)
    
    def calc_radius(self, im):
        """
            Calculate white space radius
        """
        x = self.x
        y = self.y
        distances = [
            self.get_distance_right(im, x, y),
            self.get_distance_left(im, x, y),
            self.get_distance_top(im, x, y),
            self.get_distance_bottom(im, x, y),
        ]
        self.radius = math.ceil(sum(distances)/len(distances))
        if self.max_radius < self.radius:
            self.max_radius = self.radius
            self.max_radius_x = self.x
            self.max_radius_y = self.y
            self.max_radius_z = self.z
        return self.radius

    def get_distance_right(self, im, x, y):
        """
            Get distance from center to white space right border (in pixels)
        """
        x_cp = x
        while im.getpixel((x, y)) in [255, DEBUG_COLOR]:
            x += 1
        self.dist_right = abs(x - x_cp) - 1
        return self.dist_right

    def get_distance_left(self, im, x, y):
        """
            Get distance from center to white space left border (in pixels)
        """
        x_cp = x
        while im.getpixel((x, y)) in [255, DEBUG_COLOR]:
            x -= 1
        self.dist_left = abs(x - x_cp) - 1
        return self.dist_left

    def get_distance_top(self, im, x, y):
        """
            Get distance from center to white space top border (in pixels)
        """
        y_cp = y
        while im.getpixel((x, y)) in [255, DEBUG_COLOR]:
            y -= 1
        self.dist_top = abs(y - y_cp) - 1
        return self.dist_top

    def get_distance_bottom(self, im, x, y):
        """
            Get distance from center to white space bottom border (in pixels)
        """
        y_cp = y
        while im.getpixel((x, y)) in [255, DEBUG_COLOR]:
            y += 1
        self.dist_bottom = abs(y - y_cp) - 1
        return self.dist_bottom
    
    def __str__(self):
        """
            Some debug info
        """
        msg = ""
        _ = {
            "id": str(id(self)),
            "center": "%s, %s" % (self.c_x, self.c_y),
            "radius": self.radius,
            "radius_max": self.max_radius,
            "radius_max_coords": "%s, %s, %s" % (self.max_radius_x, self.max_radius_y, self.max_radius_z),
        }
        return "{id} : c({center}) r({radius}) rm({radius_max}) rc({radius_max_coords})".format(**_)


class Mapper():
    TRACKERS = []
    SPHERES = []

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.z = 1
    
    def clear_lost_trackers(self):
        """
            Remove lost trackers from trackers list
        """
        if not self.TRACKERS:
            return
        tmp = []
        for t in self.TRACKERS:
            if t.is_dead(self.im):
                self.SPHERES.append(t)
                print("Tracker lost:", t)
            else:
                t.z += 1
                tmp.append(t)
        self.TRACKERS = tmp

    def recalculate_centers(self):
        """
            Calculate centers for all trackers
        """
        if not self.TRACKERS:
            return
        print("[*] Recalculating existing centers:")
        for t in self.TRACKERS:
            t.center_myself(self.im, mark_spot=True)
            print(t)
    
    def load_image(self, imagepath):
        """
            Load new image/slice
        """
        self.im = Image.open(imagepath)
        assert self.im.width == self.width
        assert self.im.height == self.height

        self.z += 1

        self.clear_lost_trackers()
        self.recalculate_centers()
    
    def is_center_taken(self, candid):
        """
            Check if white space (its center) is already taken by other tracker
        """
        for t in self.TRACKERS:
            if math.sqrt( (t.x-candid.x)**2 + (t.y-candid.y)**2 ) <= 2:
                # print("[-] (", candid.x, candid.y, ") is taken")
                return True
        # print("[+] (", candid.x, candid.y, ") is free")
        return False
    
    def map_slice(self):
        """
            Map currently loaded image
        """
        for y in range(0, self.im.height, PIXEL_LOOP):
            for x in range(0, self.im.width, PIXEL_LOOP):
                pixel = self.im.getpixel((x,y))
                if pixel:
                    tracker = Tracker(x, y, self.z)
                    tracker.center_myself(self.im)
                    if self.is_center_taken(tracker):
                        continue
                    else:
                        print(tracker)
                        tracker.debug_draw_cross(self.im)
                        self.TRACKERS.append(tracker)
        # if self.TRACKERS:
        #     self.im.show()

# Map objects
obj = Mapper(512, 512)
c = 0
for r, d, files in os.walk(dirpath):
    files_len = len(files)
    for f in files:
        c += 1
        if c % 4:
            continue
        imagepath = os.path.join(r, f)
        _print("\r[*] Filepath   :", imagepath, "%.2f%%" % (
            100*((c)/files_len)
        ), end="" if not DEBUG else "\n")
        obj.load_image(imagepath)
        obj.map_slice()
        print("\ntrackers after", len(obj.TRACKERS))
    break

_print("")
_print("Spheres detected  :", len(obj.SPHERES))
_r = [_.max_radius for _ in obj.SPHERES]
_print(_r)
_print("  - max radius: ", max(_r))
_print("  - min radius: ", min(_r))
_print("Saving results to :", RESULT_FILE)
# Save results
with open(RESULT_FILE, "wb") as dst:
    to_write = {
        "spheres": [
            {
                "x": _.max_radius_x,
                "y": _.max_radius_y,
                "z": _.max_radius_z,
                "r": _.max_radius,
            } for _ in obj.SPHERES
        ]
    }

    dst.write(
        json.dumps(to_write, indent=4).encode()
    )

a = None

# K mean
rand_rad = []
for _ in range(K):
    candid = random.randint(1, max(_r)+5)
    while candid in rand_rad:
        candid = random.randint(min(_r)-3, max(_r)+3)
    rand_rad.append(candid)

_print(rand_rad)

rand_rad_old = None
rand_rad = {x:[] for x in rand_rad}

while True:

    for sph in obj.SPHERES:
        _min = abs(list(rand_rad.keys())[0] - sph.max_radius)
        _class = None
        # _print("\n")
        for rr in rand_rad.keys():
            candid = abs(rr - sph.max_radius)
            # _print("For sphere", sph, "calc", rr, "-", sph.max_radius, "=", candid)
            if candid <= _min:
                _min = candid
                _class = rr
        # _print(_min, "-> class", _class)
        rand_rad[_class].append((
            sph.max_radius,
            sph.max_radius_x,
            sph.max_radius_y,
            sph.max_radius_z
        ))
    
    rand_rad_old = rand_rad

    rand_rad = {sum([x[0] for x in v ])/len(v):[] for k, v in rand_rad.items()}
            
    # pprint(rand_rad_old.keys())
    # pprint(rand_rad.keys())

    if rand_rad_old.keys() == rand_rad.keys():
        break



import numpy as np
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt

def drawSphere(xCenter, yCenter, zCenter, r):
    #draw sphere
    u, v = np.mgrid[0:2*np.pi:20j, 0:np.pi:10j]
    x=np.cos(u)*np.sin(v)
    y=np.sin(u)*np.sin(v)
    z=np.cos(v)
    # shift and scale sphere
    x = r*x + xCenter
    y = r*y + yCenter
    z = r*z + zCenter
    return (x,y,z)

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

c = 0
colors = ["blue", "red", "green"]
for k, v in rand_rad_old.items():
    for t in v:
        r, x, y, z = t
        ri = r
        xi = x
        yi = y
        zi = z
        ax.scatter(xi, yi, zi, s=ri*ri, alpha=0.9, c=colors[c%3])
    c += 1

plt.show()