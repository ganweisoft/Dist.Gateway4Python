from datetime import datetime
from typing import List

from ganweisoft import MessageLevel


class EquipEventItem:
    def __init__(self):
        self.Msg = None
        self.Msg4Linkage = None
        self.Level = None
        self.OccurDateTime = None
        self.EquipNo = 0

    def __init__(self, msg: str, msg4_linkage: str, level: MessageLevel, occur_date_time: datetime, equip_no: int):
        self.msg = msg
        self.msg4_linkage = msg4_linkage
        self.level = level
        self.occur_date_time = occur_date_time
        self.equip_no = equip_no


class EquipEvent:
    def __init__(self):
        self.DeviceId = 0
        self.EquipEvents: List[EquipEventItem] = []

    def __init__(self, device_id: int, equip_events: List[EquipEventItem]):
        self.device_id = device_id
        self.equip_events = equip_events


class MqEvtMessage:
    def __init__(self):
        self.Time = None
        self.Flow = None
        self.EventItems: List[EquipEvent] = []

    def __init__(self, time: str, flow: str, event_items: List[EquipEvent]):
        self.time = time
        self.flow = flow
        self.event_items = event_items
