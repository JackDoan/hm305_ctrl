import logging
from functools import partial

import scpi

from hm305.server_commands import (
    Command,
    MeasureVoltageQuery,
    VoltageSetpointQuery,
    VoltageApplyCommand,
    SetVoltageCommand,
    SetVoltageSetpointCommand,
    SetCurrentCommand,
    SetCurrentSetpointCommand,
    MeasureCurrentQuery,
    CurrentSetpointQuery,
    OutputQuery,
    SetOutputCommand,
    CurrentApplyCommand,
)

logger = logging.getLogger(__name__)


class CommandFactory:
    Commands = scpi.Commands(
        {
            "VOLTage": partial(dict, get=MeasureVoltageQuery, set=SetVoltageCommand),
            "VOLTage:SETPoint": partial(
                dict, get=VoltageSetpointQuery, set=SetVoltageSetpointCommand
            ),
            "VOLTage:APPLY": partial(dict, get=None, set=VoltageApplyCommand),
            "CURRent": partial(dict, get=MeasureCurrentQuery, set=SetCurrentCommand),
            "CURRent:SETPoint": partial(
                dict, get=CurrentSetpointQuery, set=SetCurrentSetpointCommand
            ),
            "CURRent:APPLY": partial(dict, get=None, set=CurrentApplyCommand),
            "OUTput": partial(dict, get=OutputQuery, set=SetOutputCommand),
        }
    )

    @staticmethod
    def parse(cmd_str: str) -> Command:
        cmd_str = cmd_str.strip()  # remove whitespace
        is_query = cmd_str.endswith("?")
        cmd_str = cmd_str.strip("? ")
        while "  " in cmd_str:
            cmd_str = cmd_str.replace("  ", " ")
            logger.debug(f"fixing cmd_str: {cmd_str}")
        num_spaces = cmd_str.count(" ")
        to_return = None
        if num_spaces == 1:  # has arg
            (cmd_str_base, arg_str) = cmd_str.split(" ")
            scpi_cmd = CommandFactory.Commands[cmd_str_base]()
            if scpi_cmd is not None:
                if is_query and scpi_cmd["get"] is not None:
                    to_return = scpi_cmd["get"](arg_str)  # does this case exist?
                elif not is_query and scpi_cmd["set"] is not None:
                    to_return = scpi_cmd["set"](arg_str)
            else:
                to_return = None
        elif num_spaces == 0:  # no arg
            scpi_cmd = CommandFactory.Commands[cmd_str]()
            if scpi_cmd is not None:
                if is_query and scpi_cmd["get"] is not None:
                    to_return = scpi_cmd["get"]()
                elif not is_query and scpi_cmd["set"] is not None:
                    to_return = None  # scpi_cmd['set']()  # does this case exist? I don't think so
            else:
                to_return = None
        else:  # a problem
            to_return = None
        return to_return
