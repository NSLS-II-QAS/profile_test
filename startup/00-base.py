from bluesky.run_engine import RunEngine
from bluesky.utils import ts_msg_hook
from databroker import Broker, temp_config


RE = RunEngine({})
db = Broker.from_config(temp_config())

RE.subscribe(db.insert)
RE.msg_hook = ts_msg_hook
