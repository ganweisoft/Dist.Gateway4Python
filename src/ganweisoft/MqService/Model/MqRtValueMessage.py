from typing import List, Dict, Any


class DataItem:
    def __init__(self):
        self.DeviceId = 0
        self.Attribute: Dict[int, Any] = {}

    def __init__(self, device_id: int, attribute: Dict[int, Any]):
        self.device_id = device_id
        self.attribute = attribute

class MqRtValueMessage:
    def __init__(self):
        self.Time = None
        self.Flow = None
        self.DataItems: List[DataItem] = []

    def __init__(self, time: str, flow: str, data_items: List[DataItem]):
        self.time = time
        self.flow = flow
        self.data_items = data_items