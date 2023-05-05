import platform
import subprocess
import logging
import datetime
import asyncio
from sys import stdout


formatter = logging.Formatter("%(message)s")
console = logging.getLogger('ipm.clients')
console.setLevel(logging.INFO)
chandler = logging.StreamHandler(stdout)
chandler.setLevel(logging.DEBUG)
chandler.setFormatter(formatter)
console.addHandler(chandler)


class Clients:

    def __init__(self, address: str, interval: int = 5, alarm_file: str = None) -> None:
        self._uuid: str = ''
        self.address: str = address
        self.interval: int = interval
        self._last_ping: str = ""
        self.status = None
        alarm_file = alarm_file.strip() if alarm_file else None
        if alarm_file == "" or alarm_file == " ":
            alarm_file = None
        self.alarm_file = alarm_file

    def client_ping(self) -> bool:
        self._last_ping = datetime.datetime.now().isoformat()
        self.status = self.ping(self.address)
        if not self.status:
            console.error(f'{self.address} missing at {self._last_ping}')
            self.create_alarm_file()
        else:
            console.info(f'{self.address} available at {self._last_ping}')
        return self.status

    async def client_ping_(self) -> bool:

        console.debug(f"Ping task started: {self.address} every {self.interval}s")
        while True:
            res = self.client_ping()
            await asyncio.sleep(self.interval)

    @classmethod
    def ping(cls, address: str) -> bool:
        param = "-n" if platform.system().lower() == "windows" else "-c"
        # arguments:
        #   -n: number of echo request messages
        #   -t: endless sending echo request messages
        #   -w: timeout to wait for reply message in ms
        command = ["ping", param, "3", "-w", "1", address]

        # output:
        #   - subprocess.DEVNULL ... pipe output to /dev/null
        #   - subprocess.STDOUT ...
        return subprocess.call(command, stdout=subprocess.DEVNULL) == 0

    def create_alarm_file(self) -> bool:
        """Create an empty file in case of an unreachable client."""
        if not self.alarm_file: return False
        with open(self.alarm_file, "w") as f:
            pass
        console.error(f'Alarm file {self.alarm_file} created for client {self.address}, {self._last_ping}')
        return True

    def __str__(self) -> str:
        return f"Client:{self.address}, Interval:{self.interval}, Alarm File:{self.alarm_file}"
