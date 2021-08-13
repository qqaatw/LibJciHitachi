import hashlib
import math


def bin_concat(int_1, int_2, int_1_byte=None, int_2_byte=None):
    """Concatenate two integer.
    Steps:
        1. Zero fill integers according to the given byte.
        2. Concatenate two integers in binary.

    Parameters
    ----------
    int_1 : int
        Left partition.
    int_2 : int
        Right partition.
    int_1_byte : int, optional
        If None is given, int_1 will be zero filled to the number which can be devided exactly by 8,
        otherwise int_1 will be zero filled to int_1_byte*8, by default None.
    int_2_byte : int, optional
        If None is given, int_2 will be zero filled to the number which can be devided exactly by 8,
        otherwise int_2 will be zero filled to int_2_byte*8, by default None.

    Returns
    -------
    int
        Concatenated value.
    """

    int_1_bin = bin(int_1)[2:]
    int_2_bin = bin(int_2)[2:]

    if int_1_byte is not None:
        int_1_bin = int_1_bin.zfill(int_1_byte * 8)
    else:
        int_1_bin = int_1_bin.zfill(math.ceil(len(int_1_bin) / 8) * 8)
    if int_2_byte is not None:
        int_2_bin = int_2_bin.zfill(int_2_byte * 8)
    else:
        int_2_bin = int_2_bin.zfill(math.ceil(len(int_2_bin) / 8) * 8)

    return int(int_1_bin + int_2_bin, base=2)

def cast_bytes(v, nbytes):
    """Cast byte(s) from v.

    Parameters
    ----------
    v : int
        Value to be casted.
    nbytes : int
        Number of bytes will be casted.

    Returns
    -------
    int
        Casted value.
    """

    assert nbytes >= 1 and nbytes <= 8, \
        "Invalid nbytes : {}".format(nbytes)
    return v & (0x100 ** nbytes - 1)

def convert_hash(v):
    """Convert md5 from string.
    Steps:
        1. Use hashlib to convert md5.
        2. Perform "And 255" then "Or 256" to ensure 
           the length of hashed code is limited within 511 (0b111111111).

    Parameters
    ----------
    v : str
        Value to be converted.

    Returns
    -------
    str
        Converted hash code.
    """

    md5 = hashlib.md5(v.encode('utf8')).digest()
    code = [hex((i & 0xff) | 0x100)[3:5] for i in md5]
        
    return ''.join(code)

def extract_bytes(v, start, end):
    """Extract bytes scope, from start(left) to end(right).
    Steps:
        1. Right shift `end` bytes.
        2. Perform cast_bytes to extract the scope of start-end.

    Parameters
    ----------
    v : int
        Value to be extracted.
    start : int
        Starting byte.
    end : int
        Ending byte.

    Returns
    -------
    int
        Extracted value.
    """

    assert start > end and end >= 0, \
        "Starting byte must be greater than ending byte, \
         and ending byte must be greater than zero : \
         {}, {}".format(start, end)
    return cast_bytes(v >> end * 8, start-end)