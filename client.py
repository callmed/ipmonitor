import os
import platform
import subprocess
import logging
import datetime
import asyncio
from sys import stdout


formatter = logging.Formatter("%(levelname)-7s %(asctime)-19s.%(msecs)03d |"
                              "%(name)-8s | %(funcName)8s %(module)8s | %(message)s",
                              "%d.%m.%Y %H:%M:%S")
console = logging.getLogger('ipmonitor.clients')
console.setLevel(logging.DEBUG)
chandler = logging.StreamHandler(stdout)
chandler.setLevel(logging.DEBUG)
chandler.setFormatter(formatter)
console.addHandler(chandler)


class Clients:

    number_of_packages: int = 1
    directory_alarm_files: str = os.getcwd()

    _logger_formatter = logging.Formatter("%(message)s")
    _logger_loglevel = logging.ERROR
    _logger_output_file = None

    def __init__(self, address: str, interval: int = 5, alarm_file: str = None) -> None:
        self._logger = logging.getLogger('ipm.clients')
        console.setLevel(self._logger_loglevel)
        chandler = logging.StreamHandler(stdout)
        chandler.setLevel(self._logger_loglevel)
        chandler.setFormatter(self._logger_formatter)
        console.addHandler(chandler)
        if self._logger_output_file:
            # setup file for logger
            pass
        self._uuid: str = ''
        self.address: str = address
        self.interval: int = interval
        self._last_ping: str = ""
        self.status = None
        alarm_file = alarm_file.strip() if alarm_file else None
        if alarm_file == "" or alarm_file == " ":
            alarm_file = None
        self.alarm_file = os.path.join(self.directory_alarm_files, alarm_file) if alarm_file else None
        console.debug(f"{self.alarm_file} alarm file for {self.address}")

    def client_ping(self) -> bool:
        """Ping of class ip address."""
        self._last_ping = datetime.datetime.now().isoformat()
        self.status = self.ping(self.address)
        if not self.status:
            console.info(f'{self.address} missing at {self._last_ping}')
            self._logger.error(f'{self.address} missing at {self._last_ping}')
            self.create_alarm_file()
        else:
            console.info(f'{self.address} available at {self._last_ping}')
            self._logger.info(f'{self.address} available at {self._last_ping}')
        return self.status

    async def client_ping_(self) -> bool:
        """Endless ping of class ip address."""
        console.info(f"Ping task started: {self.address} every {self.interval}s")
        while True:
            res = self.client_ping()
            await asyncio.sleep(self.interval)

    @classmethod
    def ping(cls, address: str) -> bool:
        """Ping a network ip address, return true if reachable."""
        param = "-n" if platform.system().lower() == "windows" else "-c"
        # arguments:
        #   -n: number of echo request messages
        #   -t: endless sending echo request messages
        #   -w: timeout to wait for reply message in ms
        command = ["ping", param, f"{Clients.number_of_packages}", "-w", "1", address]

        # output:
        #   - subprocess.DEVNULL ... pipe output to /dev/null
        #   - subprocess.STDOUT ...
        return subprocess.call(command, stdout=subprocess.DEVNULL) == 0

    def create_alarm_file(self) -> bool:
        """Create an empty file in case of an unreachable client."""
        if not self.alarm_file: return False
        # if os.path.exists(self.alarm_file): return False
        with open(self.alarm_file, "a") as f:
            f.write(f"{datetime.datetime.now().isoformat()} {self.address}\n")
        console.error(f'Alarm file {self.alarm_file} created for client {self.address}, {self._last_ping}')
        self._logger.error(f'Alarm file {self.alarm_file} created for client {self.address}, {self._last_ping}')
        return True

    def __str__(self) -> str:
        return f"Client:{self.address}, Interval:{self.interval}, Alarm File:{self.alarm_file}"
