import logging
import time
import tomllib
import argparse
import asyncio
from sys import argv, exit, stdout
from pathlib import Path
from client import Clients


__version__ = "1.0"
DEFAULT_TOML_FILE = "config.toml"

formatter = logging.Formatter("%(levelname)-7s %(asctime)-19s.%(msecs)03d |"
                              "%(name)-8s | %(funcName)8s %(module)8s | %(message)s",
                              "%d.%m.%Y %H:%M:%S")
console = logging.getLogger('ipmonitor')
console.setLevel(logging.DEBUG)
chandler = logging.StreamHandler(stdout)
chandler.setLevel(logging.DEBUG)
chandler.setFormatter(formatter)
console.addHandler(chandler)


def load_toml_file(file) -> dict:
    """Load configuration from toml file."""
    console.debug(f'Load configuration from TOML file {file}')
    with open(file, 'rb') as f:
        toml_data: dict = tomllib.load(f)
        return toml_data


# TODO: Check for existing alarm files before start!
async def main(arguments):
    clients: list = []

    parser = argparse.ArgumentParser(prog='openDTUexporter', description='', add_help=False)
    parser.add_argument('--version', action='version', version='%(prog)s {version}'.format(version=__version__))
    parser.add_argument('--load', action='store', nargs='?', const='config.toml', metavar='TOML-FILE', help='Load specific configuration file')
    arguments_cli = parser.parse_args()
    console.debug(f"CLI arguments passed in: {arguments_cli}")

    toml_file = Path(DEFAULT_TOML_FILE)
    if arguments_cli.load:
        toml_file = arguments_cli.load
        console.debug(f'TOML configuraton file from CLI {toml_file}')
    if not toml_file.is_file(): raise FileExistsError("TOML File not found")
    configuration = load_toml_file(file=toml_file)
    console.info(f'TOML configuration: {configuration}')

    output_file = configuration.get("logfile", None)
    console.debug(f'Write output to {output_file} file')

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