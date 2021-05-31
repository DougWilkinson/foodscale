import gc
print("Start", gc.mem_free())
from micropython import const
from machine import Pin
from time import sleep_us, sleep_ms

CMD1 = const(64)  
CMD2 = const(192) 
CMD3 = const(128) 
DSP_ON = const(8) 
DELAY = const(10) 
MSB = const(128)  

_SEGMENTS = bytearray(b'\x3F\x06\x5B\x4F\x66\x6D\x7D\x07\x7F\x6F\x77\x7C\x39\x5E\x79\x71\x3D\x76\x06\x1E\x76\x38\x55\x54\x3F\x73\x67\x50\x6D\x78\x3E\x1C\x2A\x76\x6E\x5B\x00\x40\x63')
_LOWERSEGMENTS = bytearray(b'\x5C\x7C\x58\x5E\x58\x71\x5C\x74\x04\x0C\x50\x06\x54\x54\x5C\x5C\x5C\x50\x0C\x78\x1C\x1C\x1C\x52\x1C\x48')
_UPPERSEGMENTS = bytearray(b'\x77\x7F\x39\x3F\x79\x71\x7D\x76\x06\x1E\x70\x38\x37\x37\x3F\x73\x3F\x77\x6D\x07\x3E\x3E\x3E\x76\x72\x1B')

class TM1637(object):
    def __init__(self, clk=0, dio=2, brightness=7):
        self.clk = clk
        self.dio = dio

        self._brightness = brightness

        self.clk.init(Pin.OUT, value=0)
        self.dio.init(Pin.OUT, value=0)
        sleep_us(DELAY)

        self._write_data_cmd()
        self._write_dsp_ctrl()

    def _start(self):
        self.dio(0)
        sleep_us(DELAY)
        self.clk(0)
        sleep_us(DELAY)

    def _stop(self):
        self.dio(0)
        sleep_us(DELAY)
        self.clk(1)
        sleep_us(DELAY)
        self.dio(1)

    def _write_data_cmd(self):
        self._start()
        self._write_byte(CMD1)
        self._stop()

    def _write_dsp_ctrl(self):
        self._start()
        self._write_byte(CMD3 | DSP_ON | self._brightness)
        self._stop()

    def _write_byte(self, b):
        for i in range(8):
            self.dio((b >> i) & 1)
            sleep_us(DELAY)
            self.clk(1)
            sleep_us(DELAY)
            self.clk(0)
            sleep_us(DELAY)
        self.clk(0)
        sleep_us(DELAY)
        self.clk(1)
        sleep_us(DELAY)
        self.clk(0)
        sleep_us(DELAY)

    def brightness(self, val=None):
        if val is None:
            return self._brightness
        if not 0 <= val <= 7:
            raise ValueError("Brightness out of range")

        self._brightness = val
        self._write_data_cmd()
        self._write_dsp_ctrl()

    def write(self, segments, pos=0):
        if not 0 <= pos <= 5:
            raise ValueError("Position out of range")
        self._write_data_cmd()
        self._start()

        self._write_byte(CMD2 | pos)
        for seg in segments:
            self._write_byte(seg)
        self._stop()
        self._write_dsp_ctrl()

    def encode_string(self, string, usecase=False):
        segments = bytearray(len(string))
        for i in range(len(string)):
            segments[i] = self.encode_char(string[i], usecase)
        return segments

    def encode_char(self, char, usecase=False):
        o = ord(char)
        if o == 32:
            return _SEGMENTS[36] # space
        if o == 42:
            return _SEGMENTS[38] # star/degrees
        if o == 45:
            return _SEGMENTS[37] # dash
        if o >= 97 and o <= 122:
            return _SEGMENTS[o-87] # lowercase a-z
        if o >= 48 and o <= 57:
            return _SEGMENTS[o-48] # 0-9
        raise ValueError("Character out of range: {:d} '{:s}'".format(o, chr(o)))

    def show(self, string, colon=True, usecase=False):
        segments = self.encode_string(string, usecase)
        if len(segments) > 1 and colon:
            segments[1] |= 128
        self.write(segments[:4])

