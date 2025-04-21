from api.kudago import fetch_kudago_events
from pprint import pprint
events = fetch_kudago_events("msk")
pprint(events)