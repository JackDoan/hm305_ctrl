import logging
from queue import Empty

from modbus import CRCError

logger = logging.getLogger(__name__)


class HM305pSerialQueueHandler:  # todo priority queue? monitoring commands for i3bar are much less important
    time_to_die = False

    def __init__(self, queue, hm):
        self.queue = queue
        self.hm = hm

    def run(self):
        while not self.time_to_die:
            try:
                item = self.queue.get(timeout=1)
                if item.stale:
                    logger.debug(f"stale item! {item}")
                else:
                    logger.debug(f"processing {item}")
                    try:
                        item.invoke(self.hm)
                    except CRCError as e:
                        logger.error(e)
                self.queue.task_done()
            except Empty:
                continue


class HM305pFastQueueHandler:
    time_to_die = False

    def __init__(self, queue, hm):
        self.queue = queue
        self.hm = hm

    def run(self):
        while not self.time_to_die:
            try:
                item = self.queue.get(timeout=1)
                if item.stale:
                    logger.debug(f"stale item! {item}")
                elif item.uses_serial_port:
                    logger.error(
                        f"Bad programmer! You cannot put {item} in the fast queue!"
                    )
                    item.result = "QUEUE ERROR"
                else:
                    logger.debug(f"processing {item}")
                    item.invoke(self.hm)
                self.queue.task_done()
            except Empty:
                continue
