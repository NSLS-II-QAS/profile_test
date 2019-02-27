from bluesky.run_engine import RunEngine
from databroker import Broker, temp_config
import bluesky.plans as bp


RE = RunEngine({})
db = Broker.from_config(temp_config())
RE.subscribe(db.insert)
