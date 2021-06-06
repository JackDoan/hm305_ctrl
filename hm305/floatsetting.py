from modbus import Modbus


class FloatSetting:
    def __init__(
        self,
        modbus: Modbus,
        value_addr: int,
        setpoint_addr: int,
        value_scalar=1.0,
        minimum=0.0,
        min_addr=None,
        maximum=999.0,
        max_addr=None,
    ):
        self._modbus = modbus
        self._value_address = value_addr
        self._value_scalar = value_scalar
        self._setpoint_address = setpoint_addr
        self._sw_setpoint = 0.0
        self._setpoint_out_of_sync = True
        self.min = minimum
        self.min_addr = min_addr
        self.max = maximum
        self.max_addr = max_addr

    def initialize(self):
        self._sw_setpoint = self.instrument_setpoint
        if self.min_addr is not None:
            self.min = self._scaled_reading(self.min_addr)
        if self.max_addr is not None:
            self.max = self._scaled_reading(self.max_addr)

    def _scaled_reading(self, addr) -> float:
        reading = self._modbus.get_by_addr(addr)
        return reading / self._value_scalar

    def _scaled_int_writing(self, addr: int, value: float) -> bool:
        if value < self.min:
            value = self.min
        elif value > self.max:
            value = self.max
        value = int(round(value * self._value_scalar))
        return self._modbus.set_by_addr(addr, value)

    @property
    def setpoint(self) -> float:
        return self._sw_setpoint

    @setpoint.setter
    def setpoint(self, to_set: float):
        self._setpoint_out_of_sync = True
        self._sw_setpoint = to_set  # todo this should be atomic

    @property
    def instrument_setpoint(self) -> float:
        got = self._scaled_reading(self._setpoint_address)
        self.setpoint = got
        self._setpoint_out_of_sync = False
        return got

    @instrument_setpoint.setter
    def instrument_setpoint(self, to_set: float):
        self.setpoint = to_set
        self._scaled_int_writing(self._setpoint_address, self.setpoint)
        self._setpoint_out_of_sync = False

    @property
    def value(self) -> float:
        return self._scaled_reading(self._value_address)

    def increment(self, inc: float):
        # needed to make using lambdas easier
        self.setpoint += inc

    def apply(self):
        self.instrument_setpoint = self._sw_setpoint
