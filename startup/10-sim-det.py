# import os
# from os.path import expanduser

from ophyd.areadetector import SimDetector
from ophyd.areadetector.filestore_mixins import FileStoreTIFFIterativeWrite
from ophyd.areadetector.plugins import TIFFPlugin
from ophyd.areadetector.trigger_mixins import SingleTrigger
from ophyd.device import Component as Cpt


class SimTIFFPlugin(TIFFPlugin, FileStoreTIFFIterativeWrite):
    pass


class SimDetectorWithTiff(SingleTrigger, SimDetector):
    tiff = Cpt(SimTIFFPlugin, 'TIFF1:', write_path_template='/tmp')


sim_det = SimDetectorWithTiff('13SIM1:', name='sim_det')
sim_det.read_attrs = ['tiff']
sim_det.tiff.kind = 'normal'
