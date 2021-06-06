import logging
from functools import partial
import hm305
import scpi

logger = logging.getLogger(__name__)


class Command:
    def __init__(self):
        self.stale = False
        self.complete = False
        self.result = None

    wait_for_result = False
    uses_serial_port = True

    def invoke(self, hm: hm305.HM305):
        """
        Used by the command runner to actually perform the command
        Sets result (if applicable) and complete before returning.
        The external command runner checks the stale flag first, not this function
        """
        self.result = "Not implemented"
        self.complete = True

    def result_as_string(self):
        return f"{self.result}"

    def __repr__(self):
        return f"<{self.__class__.__name__}>"


class CommandWithArg(Command):
    def __init__(self, arg):
        super().__init__()
        self.arg = arg

    def __repr__(self):
        return f"<{self.__class__.__name__}>({self.arg})"


class CommandWithFloatArg(CommandWithArg):
    def __init__(self, arg):
        super().__init__(arg)
        try:
            self.arg = float(arg)
        except ValueError as e:
            self.stale = True
            logger.error(e)
            self.result = "error: bad float"

    def result_as_string(self):
        return f"{self.result:2.3f}"

    def __repr__(self):
        return f"<{self.__class__.__name__}({self.arg})={self.result}>"


class QueryCommand(Command):
    wait_for_result = True

    def __repr__(self):
        return f"<{self.__class__.__name__}()={self.result}>"


class OutputQuery(QueryCommand):
    def invoke(self, hm):
        self.result = hm.output
        self.complete = True

    def result_as_string(self):
        return scpi.encode_on_off(self.result)


class SetOutputCommand(CommandWithArg):
    def __init__(self, arg):
        super().__init__(arg)
        self.arg = scpi.decode_on_off(arg)  # ON/OFF->true/false

    uses_serial_port = True
    wait_for_result = False

    def invoke(self, hm):
        if self.arg:
            hm.on()
        else:
            hm.off()
        self.result = self.arg
        self.complete = True

    def result_as_string(self):
        return str(self.arg)


class MeasureVoltageQuery(QueryCommand):
    uses_serial_port = True

    def invoke(self, hm):
        self.result = hm.voltage.value
        self.complete = True


class SetVoltageCommand(CommandWithFloatArg):
    """
    NOTE: This class is manually split into a SetVoltageSetpoint and a VoltageApply
    Need to find a cleaner way to do this
    """

    uses_serial_port = True

    def invoke(self, hm):
        if not self.complete:
            hm.voltage.instrument_setpoint = self.arg
        self.complete = True


class SetVoltageSetpointCommand(CommandWithFloatArg):
    uses_serial_port = False
    wait_for_result = True

    def invoke(self, hm):
        hm.voltage.setpoint = self.arg
        self.result = self.arg
        self.complete = True


class VoltageApplyCommand(Command):
    uses_serial_port = True
    wait_for_result = False
    in_queue = False

    def __init__(self):
        super().__init__()
        if VoltageApplyCommand.in_queue:  # TODO
            self.stale = True
            self.complete = True
        else:
            VoltageApplyCommand.in_queue = True

    def invoke(self, hm):
        VoltageApplyCommand.in_queue = False
        hm.voltage.apply()
        self.complete = True


class VoltageSetpointQuery(QueryCommand):
    uses_serial_port = False
    wait_for_result = True

    def invoke(self, hm):
        self.result = float(hm.voltage.setpoint)
        self.complete = True


class MeasureCurrentQuery(QueryCommand):
    uses_serial_port = True

    def invoke(self, hm):
        self.result = float(hm.current.value)
        self.complete = True


class SetCurrentCommand(CommandWithFloatArg):
    uses_serial_port = True

    def invoke(self, hm):
        if not self.complete:
            hm.current.instrument_setpoint = self.arg
        self.complete = True


class SetCurrentSetpointCommand(CommandWithFloatArg):
    uses_serial_port = False
    wait_for_result = True

    def invoke(self, hm):
        hm.current.setpoint = self.arg
        self.result = self.arg
        self.complete = True


class CurrentApplyCommand(Command):
    uses_serial_port = True
    wait_for_result = False
    in_queue = False

    def __init__(self):
        super().__init__()
        if CurrentApplyCommand.in_queue:  # TODO
            self.stale = True
            self.complete = True
        else:
            CurrentApplyCommand.in_queue = True

    def invoke(self, hm):
        CurrentApplyCommand.in_queue = False
        hm.current.apply()
        self.complete = True


class CurrentSetpointQuery(QueryCommand):
    uses_serial_port = False
    wait_for_result = True

    def invoke(self, hm):
        self.result = float(hm.current.setpoint)
        self.complete = True
