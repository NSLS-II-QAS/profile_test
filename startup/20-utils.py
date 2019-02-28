import time
import matplotlib.pyplot as plt
from databroker.assets.handlers import AreaDetectorTiffHandler

plt.ion()


def get_images_from_det(det):
    det.stage()
    det.trigger()
    time.sleep(5)
    det.read()
    res, dat = list(det.collect_asset_docs())
    det.unstage()

    h = AreaDetectorTiffHandler(det.tiff.write_path_template,
                                **res[1]['resource_kwargs'])
    img = h(**dat[1]['datum_kwargs'])
    return img
