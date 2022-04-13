# sample code, running out of orthanc used to hide part of the image on a US image

from pydicom.pixel_data_handlers.util import apply_color_lut
from pydicom import dcmread, dcmwrite


ds = dcmread("/mnt/c/Users/alain/Downloads/US000016.dcm")
arr = ds.pixel_array

width = ds.Columns
height = ds.Rows

def fill(arr, left, top, right, bottom, value):
    
    for y in range(top, bottom):
        for x in range(left, right):
            arr[y][x] = value

    return arr

arr = fill(arr, 80, 0, 799, 55, 127)

ds.PixelData = arr.tobytes()

ds.save_as("/mnt/c/Users/alain/Downloads/implicit-vr-us-palette.dcm", ds)
