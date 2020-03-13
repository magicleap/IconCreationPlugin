"""mldb module consists of function to interact with the MLSDK and the mldb CLI.
"""

# built-in imports
import subprocess
import logging
import os
import platform
import json

# constants
logging.basicConfig(level=logging.DEBUG)
LOG = logging.getLogger(__name__)


def get_mldb_directory():
    """Uses the MLSDK environment variable to find the full path to MLDB.

    Args:
        None

    Returns:
        str: Path to mldb executable
    """
    mldb_path = None

    if 'MLSDK' in os.environ:
        mldb_path = os.path.join(os.environ['MLSDK'], 'tools', 'mldb')

    if mldb_path is None or not os.path.exists(mldb_path):
        raise ValueError('Cannot find MLDB directory, set MLSDK environment variable')

    return mldb_path


def get_mldb_command():
    """Full path to executable for MLDB.

    Args:
        None

    Returns:
        str: Full path to mldb executable
    """
    if platform.system() == 'Windows':
        mldb_cmd = os.path.join(get_mldb_directory(), 'mldb.exe')
    else:
        mldb_cmd = os.path.join(get_mldb_directory(), 'mldb')

    return mldb_cmd


class BridgeError(Exception):
    """Simple exception for handling improper syntax command line calls to MLDB."""
    pass


class MLDB(object):
    """Simple wrapper around the mldb executable.

    Makes issuing commands and getting output from mldb a lot more simple. Output
    is returned as a dictionary.

    Commands are issued with a single string plus arguments.
    """
    def __init__(self, mldb_path=None):
        self._device_id = None

        if mldb_path is None:
            self._mldb = get_mldb_command()

        self._init()

    def _init(self):
        """Start the device server, this is a pre-run task when instancing the class."""
        kw = dict()
        if platform.system() == 'Windows':
            kw['shell'] = True

        try:
            subprocess.check_output([self._mldb, 'start-server'], **kw)
        except subprocess.CalledProcessError as e:
            raise BridgeError(e)

    @property
    def device_id(self):
        """Get the device ID currently set.

        Args:
            None

        Returns:
            str: Unique device ID
        """
        return self._device_id

    @device_id.setter
    def device_id(self, value):
        """Set the device ID.

        Args:
            value(str): device ID

        Returns:
            None
        """
        self._device_id = value

    def run(self, command, *args):
        """Issues a command with the supplied arguments to mldb.

        Args:
            command(str): Name of an mldb command.
            *args: Any flags or accessory info to issue with command.

        Raises:
            BridgeError: If command syntax is bad

        Returns:
            str: mldb raw output
        """
        if self._device_id is None:
            raise BridgeError('No device id set')

        cmd = [self._mldb, '-s', self.device_id, command]
        cmd.extend(args)

        LOG.debug('Command ran: {0}'.format(' '.join(cmd)))

        kw = dict()
        if platform.system() == 'Windows':
            kw['shell'] = True

        try:
            output = subprocess.check_output(cmd, **kw)
        except subprocess.CalledProcessError as e:
            raise BridgeError(e)

        return output

    def _get_devices(self):
        """Get all ML1 devices that are connected via USB.

        Args:
            None

        Returns:
            str: raw mldb output
        """
        cmd = [self._mldb, 'devices']

        kw = dict()
        if platform.system() == 'Windows':
            kw['shell'] = True

        try:
            output = subprocess.check_output(cmd, **kw)
        except subprocess.CalledProcessError as e:
            raise BridgeError(e)

        return output

    def is_app_running(self, packageId):
        """Check if an app is currently open.

        Args:
            packageId: The app package ID.

        Returns:
            bool
        """
        rawData = self.run('ps', '-j')

        data = json.loads(rawData)
        for item in data:
            if item['package'] == packageId and item['state'] == 'Running':
                return True

        return False

    def run_launch(self, package_name, force=False):
        """Runs mldb launch command to open an app.

        Args:
            package_name(str): The package ID.
            force(bool): Toggles the force flag for mldb.

        Returns:
            None
        """
        if force:
            self.run('launch', '-f', package_name)
        else:
            self.run('launch', package_name)

    def run_install(self, mpk_path):
        """Install an MPK to the current device.

        MPKs are always upgraded even if a similarly named MPK
        is already installed.

        Args:
            mpk_path(str): Absolute path to the mpk package file.

        Returns:
            None
        """
        self.run('install', '-u', mpk_path)

    def run_uninstall(self, package_name):
        """Uninstall an MPK from the current device.

        Args:
            package_name(str): unique name for the MPK that is already installed.

        Returns:
            None
        """
        self.run('uninstall', package_name)

    def fetch_packages(self):
        """Get all installed packages/MPKs.

        Args:
            None

        Returns:
            dict: Information about installed packages on the current device.
        """
        raw_data = self.run('packages', '-j')
        decoded_data = raw_data.decode('utf-8')

        return json.loads(decoded_data)

    def fetch_devices(self):
        """Get all connected devices.

        Gets the following:
            - `devices`: List of device names

        Args:
            None

        Returns:
            dict: Information about connected devices to your computer.
        """
        raw_data = self._get_devices()
        decoded_data = raw_data.decode('utf-8')
        LOG.debug('raw devices data: %s' % decoded_data)

        devices = decoded_data.splitlines()[1:]
        devices.remove('')
        LOG.debug(devices)
        device_list = list()
        if not devices:
            LOG.exception('No connected devices found.')
        else:
            for device in devices:
                device_list.append(device.split('\t')[0])
        result = dict(devices=device_list)
        LOG.debug('formatted devices data: %s' % result)

        return result

    def fetch_fingerprint(self):
        """Get build info about the current device.

        Gets the following:
            - `sdk`: What SDK is being used
            - `nova`: What version of Nova is flashed on the device
            - `build_type`: What flash of Nova is on the device, user debug, debug, production, etc

        Args:
            None

        Returns:
            dict: Information about development with the ML1 device.
        """
        raw_data = self.run('getprop', 'ro.build.fingerprint')
        decoded_data = raw_data.decode('utf-8')
        LOG.debug('raw fingerprint data: %s' % decoded_data)

        fingerprints = decoded_data.split('/')
        sdk = fingerprints[2][8:]
        nova = fingerprints[3]
        build_type = fingerprints[4].split(':')[1]
        result = dict(sdk=sdk, nova=nova, build_type=build_type)
        LOG.debug('formatted fingerprint data: %s' % result)

        return result

    def fetch_wifi_status(self):
        """Get info about the wifi and network for the current device.

        Gets the following:
            - `wifi_status`: WiFi status/is it connected to the internet
            - `network`: What network is the device connected to

        Args:
            None

        Returns:
            dict: Information about wifi/network paired with ML1 device.
        """
        raw_data = self.run('wifi', 'on')
        decoded_data = raw_data.decode('utf-8')
        LOG.debug('raw wifi data: %s' % decoded_data)

        wifi_status = decoded_data.splitlines()[0]
        if wifi_status == 'Wi-Fi is already enabled':
            wifi_connection = True
        elif wifi_status == 'Wi-Fi was successfully turned on':
            wifi_connection = True
        else:
            wifi_connection = False

        raw_data = self.run('wifi', 'list')
        decoded_data = raw_data.decode('utf-8')
        LOG.debug('raw network data: %s' % decoded_data)

        try:
            network = decoded_data.split(' ')[1].split('=')[1]
        except:
            network = 'Not Configured'

        result = dict(wifi_status=wifi_connection, network=network)
        LOG.debug('formatted wifi data: %s' % result)

        return result

    def fetch_controller(self):
        """Get info about the current device related to the controller.

        Gets the following:
            - `control_id`: Control ID
            - `connected`: If the control is connected to the powerpack
            - `paired`: If the control is paired to the powerpack
            - `pending`: If control is pending

        Args:
            None

        Returns:
            dict: Information about control paired with ML1 device.
        """
        raw_data = self.run('controller', 'status')
        decoded_data = raw_data.decode('utf-8')
        LOG.debug('raw controller data: %s' % decoded_data)

        result = dict(control_id='None', connected=False, paired=False)

        data = decoded_data.splitlines()
        if len(data) > 2:
            data = data[2].split()
            result['control_id'] = data[0] if data[0] is not None else 'None'
            result['connected'] = True if data[1] == 'YES' else False
            result['paired'] = True if data[2] == 'YES' else False
            result['pending'] = True if data[3] == 'YES' else False
        LOG.debug('formatted controller data: %s' % result)

        return result

    def fetch_device_ip(self):
        """Get the first connect device's IP address.
        """
        raw_data = self.run('wifi', 'status')
        decoded_data = raw_data.decode('utf-8')
        LOG.debug('raw wifi data: %s' % decoded_data)

        data = decoded_data.split(' ')
        for d in data:
            if d.startswith('IpAddr='):
                return d.split('=')[-1]

        LOG.exception('No device ip address found.')

        return

    def fetch_battery(self):
        """Get info about the current device related to the battery.

        Gets the following:
            - `charge`: Current Charge
            - `health`: Battery Health
            - `power_source_present`: If a power source is present/connected
            - `currently_charging`: If the device is currently charging
            - `connected_to`: What the device battery is connected to

        Args:
            None

        Returns:
            dict: Information about battery of the ML1 device.
        """
        raw_data = self.run('battery')
        decoded_data = raw_data.decode('utf-8')
        LOG.debug('raw battery data: %s' % decoded_data)

        result = dict()
        data = decoded_data.splitlines()[1:]
        for line in data:
            key, value = line.split(': ')
            key = key.replace(' ', '_').replace('\t', '')
            result[key] = value
        LOG.debug('formatted battery data: %s' % result)

        return result
