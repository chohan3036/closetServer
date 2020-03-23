from PIL import Image

def rgb(filestr):
    img = Image.open(filestr)
    width, height = img.size
    r, g, b = img.getpixel(((width / 2, height / 2)))

    return r, g, b