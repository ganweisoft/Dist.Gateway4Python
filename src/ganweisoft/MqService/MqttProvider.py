import os
import json
import logging
import asyncio
import ssl
from typing import List, Dict, Callable
import chardet

import paho
from cryptography.hazmat.backends import default_backend
from cryptography.x509 import load_pem_x509_certificate
import paho.mqtt.client as mqtt

from ganweisoft.EquipCategory import ChangedEquip, ChangedEquipState
from ganweisoft.MqService.Model.MqMessage import Equip, Ycp
from ganweisoft.MqService.Model.MqttTopic import MqttTopic
from ganweisoft.SetItem import SetItem
from ganweisoft.Logging import Logging
from ganweisoft import StationItem


class MqttProvider:
    _instance = None
    EquipTableRows: Dict[int, Equip] = {}
    _mqtt_client = None
    _asp_option = None
    _config = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.__init__()
        return cls._instance

    def __init__(self):
        pass

    def init(self):
        with open('config/config.properties', 'r') as file:
            for line in file:
                line = line.strip()
                if line and not line.startswith('#'):  # 跳过空行和注释行
                    key, value = line.split(':', 1)  # 从第一个冒号处分割
                    self._config[key.strip()] = value.strip()

        username = os.environ.get("IoTCenterMqttName")
        if not username:
            username = self._config.get("MqUsername")

        password = os.environ.get("IoTCenterMqttKey")
        if not password:
            password = self._config.get("MqPassword")

        gateway_id = os.environ.get("IoTCenterGatewayInstanceId")
        if not gateway_id:
            gateway_id = self._config.get("InstanceId")

        mq_server = os.environ.get("IoTCenterMqttServerIp")
        if not mq_server:
            mq_server = self._config.get("MqServer")

        asp_option_builder = {
            "credentials": {"username": username, "password": password},
            "client_id": gateway_id
        }

        mq_port = 0
        mq_ssl_port = 0
        mq_ssl_enable = os.environ.get("MqSslEnable", "False").lower() == "true"
        if mq_ssl_enable:
            mq_ssl_port = int(os.environ.get("MqSslPort", 8883))
            mq_ssl_cert = os.environ.get("MqSslCert")
            mq_ssl_cert_pwd = os.environ.get("MqSslCertPassword")
            mq_ssl_cert_ca = os.environ.get("MqSslCertCa")

            ca_certs = load_pem_x509_certificate(mq_ssl_cert.encode(), default_backend())
            ca_cert = load_pem_x509_certificate(mq_ssl_cert_ca.encode(), default_backend())
            ca_cert_collection = [ca_certs]

            tls_options = {
                "ca_certs": ca_cert,
                "certfile": ca_certs,
                "keyfile": mq_ssl_cert_pwd,
                "cert_reqs": ssl.CERT_REQUIRED,
                "tls_version": ssl.PROTOCOL_TLSv1_2,
                "ciphers": None,
                "insecure": False
            }

            asp_option_builder["server"] = mq_server
            asp_option_builder["port"] = mq_ssl_port
            asp_option_builder["tls"] = tls_options
        else:
            mq_port_str = os.environ.get("IoTCenterMqttServerPort")
            if not mq_port_str:
                mq_port = int(self._config.get("MqPort"))
            else:
                mq_port = int(mq_port_str)

            asp_option_builder["server"] = mq_server
            asp_option_builder["port"] = mq_port

        self._asp_option = asp_option_builder
        self._mqtt_client = mqtt.Client(client_id=gateway_id)
        self._mqtt_client.enable_logger()
        self._mqtt_client.username_pw_set(username, password)
        self._mqtt_client.on_connect = self.handle_connected
        self._mqtt_client.on_disconnect = self.handle_disconnected
        self._mqtt_client.on_message = self.handle_application_message_received

        if mq_ssl_enable:
            self._mqtt_client.tls_set(ca_certs=None, certfile=None, keyfile=None, cert_reqs=ssl.CERT_REQUIRED,
                                      tls_version=ssl.PROTOCOL_TLSv1_2, ciphers=None)
            self._mqtt_client.tls_insecure_set(False)

        self._mqtt_client.connect_async(mq_server, port=mq_ssl_enable and mq_ssl_port or mq_port)
        self._mqtt_client.loop_start()
        # self.reconnect_handle()

    def reconnect_handle(self):
        async def monitor():
            while True:
                try:
                    if not self._mqtt_client.is_connected():
                        self._mqtt_client.reconnect()
                        Logging.write_log_file("The MQTT client is connected.")
                except Exception as ex:
                    Logging.write_log_file(f"Reconnect error: {ex}")
                await asyncio.sleep(5)

        asyncio.run(monitor())

    def handle_application_message_received(self, client, userdata, message):
        topic = message.topic
        encoding = chardet.detect(message.payload)['encoding']
        payload = message.payload.decode(encoding)
        Logging.write_log_file(f"topic: {topic}")
        Logging.write_log_file(f"payload: {payload}")

        # Handle different topics
        if mqtt.topic_matches_sub(MqttTopic.TopicIotsysEquipDown, topic):
            # Handle equip add/remove
            des_msg_object = json.loads(payload)
            if des_msg_object.get("FlowType") == 2 and des_msg_object.get("Equips"):
                for equip in des_msg_object.get("Equips"):
                    self.EquipTableRows[equip["EquipNo"]] = Equip(equip)
                self.equip_inited()

        elif mqtt.topic_matches_sub(MqttTopic.TopicIotsysCommandDown, topic):
            # Handle set event
            des_msg_object = json.loads(payload)
            equip_item = StationItem.StationItem.get_equip_item_from_equip_no(des_msg_object.get("EquipNo"))
            if equip_item:
                equip_item.AddSetItem(SetItem(
                    equipno=des_msg_object.get("EquipNo"),
                    main_instruct=des_msg_object.get("MainInstruct"),
                    minor_instruct=des_msg_object.get("MinorInstruct"),
                    value=des_msg_object.get("Value")
                ))

        elif mqtt.topic_matches_sub(MqttTopic.TopicIotsysEquipAddDown, topic):
            # Handle equip add
            des_msg_object = json.loads(payload)
            if des_msg_object.get("FlowType") == 2 and des_msg_object.get("Equips"):
                for equip in des_msg_object["Equips"]:
                    self.EquipTableRows[equip["EquipNo"]] = equip
                    StationItem.StationItem.add_changed_equip(ChangedEquip(
                        i_sta_no=equip.get("StaN"),
                        i_eqp_no=equip.get("EquipNo"),
                        state=ChangedEquipState.Add
                    ))

        elif mqtt.topic_matches_sub(MqttTopic.TopicIotsysEquipDeleteDown, topic):
            # Handle equip delete
            des_msg_object = json.loads(payload)
            if des_msg_object.get("FlowType") == 2 and des_msg_object.get("EquipNos"):
                for equip_no in des_msg_object["EquipNos"]:
                    if equip_no in self.EquipTableRows:
                        del self.EquipTableRows[equip_no]
                    StationItem.StationItem.add_changed_equip(ChangedEquip(
                        i_sta_no=1,
                        i_eqp_no=equip_no,
                        state=ChangedEquipState.Delete
                    ))

    def handle_connected(self, client, userdata, flags, rc):
        self._mqtt_client.subscribe(MqttTopic.TopicIotsysCommandDown)
        self._mqtt_client.subscribe(MqttTopic.TopicIotsysEquipAddDown)
        self._mqtt_client.subscribe(MqttTopic.TopicIotsysEquipDeleteDown)
        self._mqtt_client.subscribe(MqttTopic.TopicIotsysEquipDown)
        Logging.write_log_file(f"Connected with result code {rc}")

    def handle_disconnected(self, client, userdata, rc):
        code_to_str = paho.mqtt.client.error_string(rc)
        Logging.write_log_file(f"Disconnected with result code {code_to_str}")

    def publish_yc_rt_value_async(self, msg):
        topic = MqttTopic.TOPIC_IOTSYS_MINIDCYC_DEVICE_DATA_REPORT.format(self._asp_option["client_id"])
        payload = json.dumps(msg, default=lambda o: o.__dict__)
        self._mqtt_client.publish(topic, payload)

    def publish_yx_rt_value_async(self, msg):
        topic = MqttTopic.TOPIC_IOTSYS_MINIDCYX_DEVICE_DATA_REPORT.format(self._asp_option["client_id"])
        payload = json.dumps(msg, default=lambda o: o.__dict__)
        self._mqtt_client.publish(topic, payload)

    def publish_rt_state_async(self, msg):
        topic = MqttTopic.TOPIC_IOTSYS_DEVICE_STATE_REPORT.format(self._asp_option["client_id"])
        payload = json.dumps(msg, default=lambda o: o.__dict__)
        self._mqtt_client.publish(topic, payload)

    def publish_evt_value_async(self, msg):
        topic = MqttTopic.TOPIC_IOTSYS_MINIDCYX_DEVICE_EVT_REPORT.format(self._asp_option["client_id"])
        payload = json.dumps(msg, default=lambda o: o.__dict__)
        self._mqtt_client.publish(topic, payload)

    def equip_inited(self):
        # Implement equip initialized logic
        from ganweisoft.Database.GWDbProvider import GWDbProvider
        GWDbProvider().InitCompleted = True
