from PIL import Image
im = Image.open("data\\0040.BMP")
# im.putpixel()
# im.getpixel

width = im.width
height = im.height


def debug_draw_cross(im, x, y, size=10):
    for i in range(size):
        im.putpixel((x,y), 125)
        im.putpixel((x+i,y), 125)
        im.putpixel((x-i,y), 125)
        im.putpixel((x,y+i), 125)
        im.putpixel((x,y-i), 125)

def get_distance_right(im, x, y):
    x_cp = x
    while im.getpixel((x, y)) == 255:
        x += 1
    return abs(x - x_cp) - 1

def get_distance_left(im, x, y):
    x_cp = x
    while im.getpixel((x, y)) == 255:
        x -= 1
    return abs(x - x_cp) - 1

def get_distance_top(im, x, y):
    y_cp = y
    while im.getpixel((x, y)) == 255:
        y -= 1
    return abs(y - y_cp) - 1

def get_distance_bottom(im, x, y):
    y_cp = y
    while im.getpixel((x, y)) == 255:
        y += 1
    return abs(y - y_cp) - 1


def adjust_position_to_center(im, x, y):
    top = get_distance_top(im, x, y)
    right = get_distance_right(im, x, y)
    bottom = get_distance_bottom(im, x, y)
    left = get_distance_left(im, x, y)
    print("top   :", top)
    print("right :", right)
    print("bottom:", bottom)
    print("left  :", left)
    horizontal_sum = right + left
    vertical_sum = top + bottom
    _sum = horizontal_sum + vertical_sum
    print("horizontal_sum   :", horizontal_sum)
    print("vertical_sum   :", vertical_sum)
    print("sum   :", _sum)
    vertical_adjust = int(vertical_sum / 2)
    horizontal_adjust = int(horizontal_sum / 2)
    print("vertical_adjust:", vertical_adjust)
    print("horizontal_adjust:", horizontal_adjust)


for y in range(height):
    for x in range(width):
        pixel = im.getpixel((x,y))
        if pixel:
            print(pixel)
            adjust_position_to_center(im, x, y)
            debug_draw_cross(im, x, y)
        
            im.show()
            exit(0)
        