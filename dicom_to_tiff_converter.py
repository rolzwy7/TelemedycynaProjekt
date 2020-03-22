# You can convert tiff format to dicom with dicomwrite:
# dicomwrite( imread('input_image.tif'), 'output_image.dcm')

import pydicom
from PIL import Image
from PIL.TiffImagePlugin import AppendingTiffWriter as TIFF
import os


dcims = []
for r, d, f in os.walk("series-000001"):
    for _ in f:
        dcims.append((os.path.join(r, _), ".".join(_.split(".")[:-1])))
    break


for path, filename in dcims:
    print("- converting:", path)
    rs = pydicom.dcmread(path)
    im = Image.fromarray(rs.pixel_array)

    # im_res = im.resize((128,128), resample=Image.NEAREST)
    im_res = im

    im_res.save(
        os.path.join("series-000001-tiff", "%s.tiff" % filename),
        "TIFF"
    )


with TIFF('TEST_MULTI.tif', True) as tiff_out:
    for r, d, f in os.walk("series-000001-tiff"):
        for _ in f:
            filename = os.path.join(r, _)
            print("- merging:", filename)
            with open(filename, mode="rb") as tiff_in:
                im = Image.open(tiff_in)
                im.save(tiff_out)
                tiff_out.newFrame()

    # for idx in range(im_res.n_frames):
    #         im_res.seek(idx)
    #         im_res.save(
    #             tiff_out,
    #             "TIFF"
    #         )