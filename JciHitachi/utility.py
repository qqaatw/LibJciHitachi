import hashlib
import math

def bin_concat(int_1, int_2, int_1_byte=None, int_2_byte=None):
    int_1_bin = bin(int_1)[2:]
    int_2_bin = bin(int_2)[2:]

    if int_1_byte is not None:
        int_1_bin = int_1_bin.zfill(int_1_byte * 8)
    else:
        int_1_bin = int_1_bin.zfill( math.ceil(len(int_1_bin) / 8) * 8)
    if int_2_byte is not None:
        int_2_bin = int_2_bin.zfill(int_2_byte * 8)
    else:
        int_2_bin = int_2_bin.zfill( math.ceil(len(int_2_bin) / 8) * 8)

    return int(int_1_bin + int_2_bin, base=2)

def cast_bytes(v, nbytes):
    assert nbytes >= 1 and nbytes <= 8, \
        "Invalid nbytes : {}".format(nbytes)
    return v & (0x100 ** nbytes - 1)

def convert_hash(v):
    md5 = hashlib.md5(v.encode('utf8')).digest()
    code = [hex((i & 0xff) | 0x100)[3:5] for i in md5]
        
    return ''.join(code)

def extract_bytes(v, start, end):
    assert start > end and end >= 0, \
        "Invalid start or end : {}, {}".format(start, end)
    return cast_bytes(v >> end * 8, start-end)