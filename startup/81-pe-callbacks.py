from event_model import DocumentRouter
from ophyd.ophydobj import OphydObject
import bluesky.plan_stubs as bps
import bluesky.plans as bp
import bluesky.preprocessors as bpp
import copy
import time


class DarkSubtractionCallback(DocumentRouter):
    def __init__(self,
                 image_key='pe1_image',
                 primary_stream='primary',
                 dark_stream='dark'):
        """Initializes a dark subtraction callback.

        This will perform dark subtraction and then save to file.

        Parameters
        ----------
        image_key : str (optional)
            The detector image string
        primary_stream : str (optional)
            The primary stream name
        dark_stream : str (optional)
            The dark stream name
        """

        self.pstream = primary_stream
        self.dstream = dark_stream
        self.image_key = image_key
        self.descriptors = {}
        self._last_dark = None
        self._has_started = False

    def start(self, doc):
        if self._has_started:
            raise RuntimeError('Can handle only one run. '
                               'Two start documents found.')
        else:
            self._has_started = True
            return super().start(doc)

    def descriptor(self, doc):
        # Note: we may want to indicate background subtraction
        self.descriptors[doc['uid']] = doc
        return super().descriptor(doc)

    def event_page(self, doc):
        # Note: we may want to update the image key to indicate background
        # subtraction in the outgoing doc.
        stream_name = self.descriptors[doc['descriptor']]['name']

        if stream_name not in [self.pstream, self.dstream]:
            return doc

        if self.image_key in doc['data']:
            if stream_name == self.dstream:
                self._last_dark = doc['data'][self.image_key][-1]
                # TODO: deal with properly-paged data later
                return doc
            elif stream_name == self.pstream:
                # Actual subtraction is happening here:
                return_doc = copy.deepcopy(doc)
                dsub_images = [im - self._last_dark
                               for im in return_doc['data'][self.image_key]]

                return_doc['data'][self.image_key] = dsub_images
                return return_doc
            else:
                raise RuntimeError(f'The stream name "{stream_name}" must be '
                                   f'one of {self.pstream} or {self.dstream}')
        else:
            return doc


# Background subtraction callback
# TODO: this needs to be a wrapped RunRouter, figure out later
# bgsub_callback = DarkSubtractionCallback(image_key="pe1_image",
                                         # primary_stream="primary",
                                         # dark_stream="dark")

# TODO: need to attach a callback registry to the run router above
# RE.subscribe(bgsub_callback)


# From Tom on 02/21/2019:
class DarkFrameCache(OphydObject):
    def __init__(self, *args, **kwargs):
        self.last_collected = None
        return super().__init__(*args, **kwargs)

    def read(self):
        return self._read

    def describe(self):
        return self._describe

    def collect_asset_docs(self):
        # keep track of when we get restaged to restore these
        yield from self._asset_docs_cache
        self._really_cached = self._asset_docs_cache
        self._asset_docs_cache = []

    def stage(self):
        self._asset_docs_cache = self._really_cached


def dark_plan(cam, dark_frame_cache):
    # yield from close_shutter()
    yield from bps.trigger(cam, group='cam')
    yield from bps.wait('cam')

    last_collected = teleport(cam, dark_frame_cache)
    # yield Msg('clone_for_dark_frames', cam, target)



def teleport(cam, dfc):
    dfc._describe = cam.describe()
    dfc._config = cam.read_configuration()
    dfc._read = cam.read()
    dfc._asset_docs_cache = list(cam.collect_asset_docs())
    dfc.last_collected = time.monotonic()

    return dfc.last_collected


# @bpp.stage_decorator
# @bpp.run_decorator
def my_dark_frame_aware_plan(cam, dark_cache, obsolete_secs=60):
    if (dark_cache.last_collected is not None and 
        time.monotonic() > dark_cache.last_collected + obsolete_secs):
        yield from dark_plan(cam, dark_cache)

    yield from bpp.trigger_and_read([dark_cache],
                                    name='dark')

    yield from bpp.trigger_and_read([cam], name='primary')


def master_plan():
    for j in range(5):
        yield from my_dark_frame_aware_plan()


dc = DarkFrameCache(name='dc')

# RE(my_dark_frame_aware_plan(cam, dc))
