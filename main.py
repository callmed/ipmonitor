import logging
import os
import time
import tomllib
import argparse
import asyncio
from sys import argv, exit, stdout
from pathlib import Path
from client import Clients

__version__ = "1.0"
DEFAULT_TOML_FILE = "config.toml"
DEFAULT_OUTPUT_FILE = "ping.txt"

formatter = logging.Formatter("%(levelname)-7s %(asctime)-19s.%(msecs)03d |"
                              "%(name)-8s | %(funcName)8s %(module)8s | %(message)s",
                              "%d.%m.%Y %H:%M:%S")
console = logging.getLogger('ipmonitor')
console.setLevel(logging.ERROR)
chandler = logging.StreamHandler(stdout)
chandler.setLevel(logging.ERROR)
chandler.setFormatter(formatter)
console.addHandler(chandler)


def load_toml_file(file) -> dict:
    """Load configuration from toml file."""
    console.debug(f'Load configuration from TOML file {file}')
    with open(file, 'rb') as f:
        toml_data: dict = tomllib.load(f)
        return toml_data


def delete_alarm_files(directory: str, auto_clean: bool = False) -> None:
    """Delete existing alarm files from alarm directory."""
    raise NotImplemented


def alarm_files_exist(path: str) -> bool:
    """Return true if alarm files already exists on program start."""
    if not Path(path).is_dir(): console.warning(f"Path {path} does not exist!")
    for file in os.listdir(path):
        if file.endswith('.alarm'): return True
    return False


# TODO: Check for existing alarm files before start!
async def main(arguments):
    clients: list = []

    parser = argparse.ArgumentParser(prog='openDTUexporter', description='', add_help=False)
    parser.add_argument('--version', action='version', version='%(prog)s {version}'.format(version=__version__))
    parser.add_argument('--load', action='store', nargs='?', const='config.toml', metavar='TOML-FILE',
                        help='Load specific configuration file')
    arguments_cli = parser.parse_args()
    console.debug(f"CLI arguments passed in: {arguments_cli}")

    toml_file = Path(DEFAULT_TOML_FILE)
    if arguments_cli.load:
        toml_file = arguments_cli.load
        console.debug(f'TOML configuraton file from CLI {toml_file}')
    if not toml_file.is_file(): raise FileExistsError("TOML File not found")
    configuration = load_toml_file(file=toml_file)
    console.info(f'TOML configuration: {configuration}')

    verbosity_output = configuration.get("output").get("print_all")
    console.debug(f"Output every ping result: {verbosity_output}")

    output_file = configuration.get("output").get("file", None)
    console.debug(f"Output filename: {output_file}")
    output_dir = configuration.get("output").get("dir", None)
    if not output_dir: output_dir = os.getcwd()
    console.debug(f"Output directory: {output_dir}")
    output_path = os.path.join(output_dir, output_file)
    console.debug(f'Write output to {output_path}')

    alarm_dir = configuration.get("alarm").get("dir", None)
    if not alarm_dir: alarm_dir = os.getcwd()
    Clients.directory_alarm_files = alarm_dir
    console.debug(f"Alarm file directory: {alarm_dir}")

    if alarm_files_exist(alarm_dir): console.warning(f"Alarm files already exists!")

    Clients.number_of_packages = configuration.get("command").get("send_pkg", 1)
    console.debug(f"Number of package to send via ping command: {Clients.number_of_packages}")

    for client in configuration.get("client_group"):
        console.info(f'Client-Configuration:{client}')
        clients.append(
            Clients(
                client.get("address", None),
                client.get("interval", None),
                client.get("alarmfile", None)
            )
        )

    # without asyncio
    # for c in clients:
    #     c.client_ping()
    #     time.sleep(1)

    tasks: list = []
    for client in clients:
        task = asyncio.create_task(client.client_ping_())
        tasks.append(task)

    while True:
        await asyncio.sleep(2)


if __name__ == '__main__':
    try:
        asyncio.run(main(argv[1:]))
        # exit(main(argv[1:]))      # without asyncio
    except KeyboardInterrupt as err:
        print("Program gracefully ended by user key press")
