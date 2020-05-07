from pprint import pprint
from PIL import Image
from math import ceil, sqrt

from os import walk as os_walk
from os import path as os_path

from random import randint
from json import dumps

from argparse import ArgumentParser

import matplotlib.pyplot as plt



parser = ArgumentParser()
parser.add_argument(
    "dirpath",
    help="dirpath <help here>"
)
parser.add_argument(
    "K", type=int,
    choices=[2,3,4,5,6,10],
    help="K <help here>"
)
parser.add_argument(
    "--slice-skip", type=int,
    default=4, choices=[1, 4,5,6,7],
    help="slice skip <help here>"
)
parser.add_argument(
    "--pixel-skip", type=int,
    default=14, choices=[1, 3, 7, 14, 20, 30],
    help="pixel skip <help here>"
)
parser.add_argument(
    "--debug", action="store_true",
    help="debug <help here>"
)
args = parser.parse_args()

slice_skip = args.slice_skip
pixel_skip = args.pixel_skip

K = args.K # K klas
dirpath = args.dirpath

RESULT_FILE = "result.json"

DEBUG_COLOR = 125

PIXEL_LOOP = pixel_skip

DEBUG = args.debug

_print = print



## Info
if DEBUG:
    print("DEBUG is ON")

print("Result file :", RESULT_FILE)
print("Slice skip  :", slice_skip, "slices")
print("Pixel skip  :", pixel_skip, "px")

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
        self.radius = ceil(sum(distances)/len(distances))
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
            if sqrt( (t.x-candid.x)**2 + (t.y-candid.y)**2 ) <= 2:
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
for r, d, files in os_walk(dirpath):
    files_len = len(files)
    for f in files:
        c += 1
        if c % slice_skip:
            continue
        imagepath = os_path.join(r, f)
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
        dumps(to_write, indent=4).encode()
    )

a = None


def KKlas(spheres):
    # import pdb; pdb.set_trace();
    _print("\nKKlas new")
    # K mean
    num_spheres = len(spheres)
    rand_rad = []
    for _ in range(K):
        candid = randint(0, num_spheres)
        while candid in rand_rad:
            candid = randint(0, num_spheres)
        rand_rad.append(candid)

    _print("Rand", rand_rad)
    for i in range(len(rand_rad)):
        rand_rad[i] = spheres[rand_rad[i]].max_radius
    _print("Rand obj", rand_rad)


    rand_rad_old = None
    rand_rad = {x:[] for x in rand_rad}

    while True:

        for sph in spheres:
            _min = max(list(rand_rad.keys())) #abs(list(rand_rad.keys())[0] - sph.max_radius)
            _class = None
            # _print("\n")
            for rr in rand_rad.keys():
                # candid = abs(rr - sph.max_radius)
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
        # _temp = {}
        # for k, v in rand_rad.items():
        #     if len(v) != 0:
        #         _temp[sum([x[0] for x in v ])/len(v)] = []
        # rand_rad = _temp
        
        # pprint(rand_rad_old.keys())
        # pprint(rand_rad.keys())

        if rand_rad_old.keys() == rand_rad.keys():
            break
    return rand_rad_old



while True:
    try:
        rand_rad_old = KKlas(obj.SPHERES)
        break
    except Exception as e:
        _print("Exception:", e)
        continue

# rand_rad_old = KKlas(obj.SPHERES)
     


fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

c = 0

low = [
    ["#488f31"], # green
    ["#a8c162"], # bright green
]
medium = [
    ["#665191"],
    ["#a05195"],
]
high = [
    ["#f9a160"], # bright orange
    ["#de425b"], # bright red
]


colors = [
    "#ff0000",
    "#4c1b13",
    "#7f5500",
    "#d6e600",
    "#61f200",
    "#468c6c",
    "#005580",
    "#00144d",
    "#6d5673",
    "#ff40a6",
]

colors = list(reversed(colors))[:K]

# if K == 2:
#     colors=[low[0], high[1]]
# if K == 3:
#     colors=[low[0], medium[0], high[1]]
# if K == 4:
#     colors=[low[0], medium[0], high[0], high[1]]
# if K == 5:
#     colors=[low[0], low[1], medium[0], high[0], high[1]]
# if K == 6:
#     colors=[low[0], low[1], medium[0], medium[1], high[0], high[1]]
# if K == 10:


for k, v in rand_rad_old.items():
    for t in v:
        r, x, y, z = t
        ri = r
        xi = x
        yi = y
        zi = z
        ax.scatter(xi, yi, zi, s=ri*ri, alpha=0.97, c=colors[c % len(colors)])
    c += 1


plt.show()