# Copyright (c) 2015 Nicolas JOUANIN
#
# See the file license.txt for copying permission.
import asyncio
from hbmqtt.messages.packet import MQTTPacket, MQTTFixedHeader, PacketType, MQTTVariableHeader
from hbmqtt.codecs import *
from hbmqtt.errors import MQTTException

class ConnectVariableHeader(MQTTVariableHeader):
    USERNAME_FLAG = 0x80
    PASSWORD_FLAG = 0x40
    WILL_RETAIN_FLAG = 0x20
    WILL_FLAG = 0x04
    WILL_QOS_MASK = 0x18
    CLEAN_SESSION_FLAG = 0x02
    RESERVED_FLAG = 0x01

    def __init__(self, connect_flags=0x00, keep_alive=0, proto_name='MQTT', proto_level=0x04):
        self.proto_name = proto_name
        self.proto_level = proto_level
        self.flags = connect_flags
        self.keep_alive = keep_alive

    def _set_flag(self, mask, val):
        if val:
            self.flags |= mask
        else:
            self.flags &= ~mask

    def _get_flag(self, mask):
        if self.flags & mask:
            return True
        else:
            return False

    @property
    def username_flag(self) -> bool:
        return self._get_flag(self.USERNAME_FLAG)

    @username_flag.setter
    def username_flag(self, val: bool):
        self._set_flag(val, self.USERNAME_FLAG)

    @property
    def password_flag(self) -> bool:
        return self._get_flag(self.PASSWORD_FLAG)

    @password_flag.setter
    def password_flag(self, val: bool):
        self._set_flag(val, self.PASSWORD_FLAG)

    @property
    def will_retain_flag(self) -> bool:
        return self._get_flag(self.WILL_RETAIN_FLAG)

    @will_retain_flag.setter
    def will_retain_flag(self, val: bool):
        self._set_flag(val, self.WILL_RETAIN_FLAG)

    @property
    def will_flag(self) -> bool:
        return self._get_flag(self.WILL_FLAG)

    @will_flag.setter
    def will_flag(self, val: bool):
        self._set_flag(val, self.WILL_FLAG)

    @property
    def clean_session_flag(self) -> bool:
        return self._get_flag(self.CLEAN_SESSION_FLAG)

    @clean_session_flag.setter
    def clean_session_flag(self, val: bool):
        self._set_flag(val, self.CLEAN_SESSION_FLAG)

    @property
    def reserved_flag(self) -> bool:
        return self._get_flag(self.RESERVED_FLAG)

    @property
    def will_qos(self):
        if (self.flags & 0x18) >> 3:
            return True
        else:
            return False

    @will_qos.setter
    def will_qos(self, val: int):
        self.flags &= (0x00 << 3)
        self.flags |= (val << 3)

    @classmethod
    def from_stream(cls, reader: asyncio.StreamReader):
        #  protocol name
        protocol_name = yield from decode_string(reader)
        if protocol_name != "MQTT":
            raise MQTTException('[MQTT-3.1.2-1] Incorrect protocol name: "%s"' % protocol_name)

        # protocol level (only MQTT 3.1.1 supported)
        protocol_level_byte = yield from read_or_raise(reader, 1)
        protocol_level = bytes_to_int(protocol_level_byte)

        # flags
        flags_byte = yield from read_or_raise(reader, 1)
        flags = bytes_to_int(flags_byte)
        if flags & 0x01:
            raise MQTTException('[MQTT-3.1.2-3] CONNECT reserved flag must be set to 0')

        # keep-alive
        keep_alive_byte = yield from read_or_raise(reader, 2)
        keep_alive = bytes_to_int(keep_alive_byte)

        return cls(flags, keep_alive, protocol_name, protocol_level)

    def to_bytes(self):
        out = b''

        # Protocol name
        out += encode_string(self.proto_name)
        # Protocol level
        out += int_to_bytes(self.proto_level)
        # flags
        out += int_to_bytes(self.flags)
        # keep alive
        out += int_to_bytes(self.keep_alive, 2)

        return out



class ConnectPayload:
    def __init__(self, client_id=None, will_topic=None, will_message=None, username=None, password=None):
        self.client_id = client_id
        self.will_topic = will_topic
        self.will_message = will_message
        self.username = username
        self.password = password


class ConnectPacket(MQTTPacket):
    def __init__(self, vh: ConnectVariableHeader, payload: ConnectPayload):
        header = MQTTFixedHeader(PacketType.CONNECT, 0x00)
        super().__init__(header)
        self.variable_header = vh
        self.payload = payload