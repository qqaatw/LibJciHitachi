import base64

from . import utility as util
from .model import JciHitachiAC, JciHitachiDH, JciHitachiHE

class JciHitachiCommand:
    """Abstract class for sending job command.

    Parameters
    ----------
    gateway_mac_address : str
        Gateway mac address.
    """

    def __init__(self, gateway_mac_address):
        self.job_info_base = bytearray.fromhex(
                              "d0d100003c6a9dffff03e0d4ffffffff \
                               00000100000000000000002000010000 \
                               000000000000000002000d278050f0d4 \
                               469dafd3605a6ebbdb130d278052f0d4 \
                               469dafd3605a6ebbdb13060006000000 \
                               0000")
        self.job_info_base[32:40] = bytearray.fromhex(hex(int(gateway_mac_address))[2:])
    
    def get_command(self, command, value):
        raise NotImplementedError
    
    def get_b64command(self, command, value):
        """A wrapper of get_command, generating base64 command.

        Parameters
        ----------
        command : str
            Status name.
        value : int
            Status value.

        Returns
        -------
        str
            Base64 command.
        """

        return base64.b64encode(self.get_command(command, value)).decode()


class JciHitachiCommandAC(JciHitachiCommand):
    """Sending job command to air conditioner.

    Parameters
    ----------
    gateway_mac_address : str
        Gateway mac address.
    """
    
    def __init__(self, gateway_mac_address):
        super().__init__(gateway_mac_address)

    def get_command(self, command, value):
        """Get job command.

        Parameters
        ----------
        command : str
            Status name.
        value : int
            Status value.

        Returns
        -------
        bytearray
            Bytearray command.
        """

        job_info = self.job_info_base.copy()
        
        # Device type
        job_info[77] = 1

        # Command (eg. target_temp)
        job_info[78] = 128 + JciHitachiAC.idx[command]

        # Value (eg. 27)
        job_info[80] = value

        # Checksum 
        # Original algorithm:
        # xor job_info 76~80
        # Since byte 76(0x06), 77(device type), and 79(0x00) are constants,
        # here is the simplified algorithm:
        # command ^ value ^ 0x07 (flip last 3 bits) 
        job_info[81] = job_info[78] ^ job_info[80] ^ 0x07

        return job_info


class JciHitachiCommandDH(JciHitachiCommand):
    """Sending job command to Dehumidifier.

    Parameters
    ----------
    gateway_mac_address : str
        Gateway mac address.
    """

    def __init__(self, gateway_mac_address):
        super().__init__(gateway_mac_address)

    def get_command(self, command, value):
        """Get job command.

        Parameters
        ----------
        command : str
            Status name.
        value : int
            Status value.

        Returns
        -------
        bytearray
            Bytearray command.
        """

        job_info = self.job_info_base.copy()
        
        # Device type
        job_info[77] = 4

        # Command (eg. target_temp)
        job_info[78] = 128 + JciHitachiDH.idx[command]

        # Value (eg. 27)
        job_info[80] = value

        # Checksum
        # Original algorithm:
        # xor job_info 76~80
        # Since byte 76(0x06), 77(device type), and 79(0x00) are constants,
        # here is the simplified algorithm:
        # command ^ value ^ 0x02
        job_info[81] = job_info[78] ^ job_info[80] ^ 0x02

        return job_info


class JciHitachiCommandHE(JciHitachiCommand):
    """Sending job command to heat exchanger.

    Parameters
    ----------
    gateway_mac_address : str
        Gateway mac address.
    """

    def __init__(self, gateway_mac_address):
        super().__init__(gateway_mac_address)

    def get_command(self, command, value):
        """Get job command.

        Parameters
        ----------
        command : str
            Status name.
        value : int
            Status value.

        Returns
        -------
        bytearray
            Bytearray command.
        """

        job_info = self.job_info_base.copy()
        
        # Device type
        job_info[77] = 14

        # Command (eg. target_temp)
        job_info[78] = 128 + JciHitachiHE.idx[command]

        # Value (eg. 27)
        job_info[80] = value

        # Checksum
        # Original algorithm:
        # xor job_info 76~80
        # Since byte 76(0x06), 77(device type), and 79(0x00) are constants,
        # here is the simplified algorithm:
        # command ^ value ^ 0x08
        job_info[81] = job_info[78] ^ job_info[80] ^ 0x08

        return job_info


class JciHitachiStatusInterpreter:
    """Interpreting received status code.

    Parameters
    ----------
    code : str
        status code.
    is_support : bool, optional
        Whether the code is support code, by default False.
    """

    def __init__(self, code, is_support=False):
        self.base64_bytes = base64.standard_b64decode(code)
        if is_support:
            self.num_idx = self._decode_support_number()
        else:
            self.num_idx = self._decode_status_number()

    def _decode_status_number(self):
        if 6 < self.base64_bytes[0] and (self.base64_bytes[1], self.base64_bytes[2]) == (0, 8):
            return int((self.base64_bytes[0] - 4) / 3)
        else:
            return 0

    def _decode_support_number(self):
        if 9 < self.base64_bytes[0]:
            return int((self.base64_bytes[0] - 26) / 3)
        else:
            return 0

    def _decode_single_status(self, max_func_number, while_counter):
        stat_idx = while_counter * 3 + 3

        if stat_idx + 3 <= self.base64_bytes[0] - 1:
            status_bytes = bytearray(4)
            status_bytes[0] = (self.base64_bytes[stat_idx] & 0x80) != 0
            status_bytes[1:4] = self.base64_bytes[stat_idx: stat_idx + 3]

            output = int.from_bytes(status_bytes, byteorder='little') & 0xffff7fff
        else:
            output = util.bin_concat(0xff, max_func_number)
            output = (output << 16) & 0xffff0000 | max_func_number
        return output

    def _decode_single_support(self, max_func_number, while_counter):
        stat_idx = while_counter * 3 + 25

        if stat_idx + 3 <= self.base64_bytes[0] - 1:
            status_bytes = bytearray(4)
            status_bytes[0] = (self.base64_bytes[stat_idx] & 0x80) != 0
            status_bytes[1:4] = self.base64_bytes[stat_idx : stat_idx + 3]

            output = int.from_bytes(status_bytes, byteorder='little') & 0xffff7fff
        else:
            output = util.bin_concat(0xff, max_func_number)
            output = (output << 16) & 0xffff0000 | max_func_number
        return output

    def decode_status(self):
        """Decode all status code of a peripheral.

        Returns
        -------
        dict
            Decoded status.
        """

        table = {}
        for i in range(self.num_idx):
            ret = self._decode_single_status(self.num_idx, i)
            idx = util.cast_bytes(ret >> 8, 1)
            table[idx] = ret >> 0x18 + (ret >> 0x10 * 0x100) 
        return table

    def decode_support(self):
        """Decode all support code of a peripheral.

        Returns
        -------
        dict
            Decoded support.
        """

        table = {
            'brand': self.base64_bytes[8:15].decode(),
            'model': self.base64_bytes[16:24].decode()
        }
        for i in range(self.num_idx):
            ret = self._decode_single_support(self.num_idx, i)
            idx = util.cast_bytes(ret >> 8, 1)
            table[idx] = ret >> 0x18 + (ret >> 0x10 * 0x100)

        return table
