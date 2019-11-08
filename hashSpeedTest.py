import xxhash
import hashlib
import datetime


def md5(file):
    start = datetime.datetime.now()
    h = hashlib.md5()

    with open(file, 'rb') as file_data:
        for chunk in iter(lambda: file_data.read(4096), b''):
            h.update(chunk)

    print(h.hexdigest(), '- md5 -', datetime.datetime.now() - start)


def xxHash32(file):
    start = datetime.datetime.now()
    h = xxhash.xxh32()

    with open(file, 'rb') as file_data:
        for chunk in iter(lambda: file_data.read(4096), b''):
            h.update(chunk)

    print(h.hexdigest(), '- xxHash32 -', datetime.datetime.now() - start)


def xxHash64(file):
    start = datetime.datetime.now()
    h = xxhash.xxh64()

    with open(file, 'rb') as file_data:
        for chunk in iter(lambda: file_data.read(4096), b''):
            h.update(chunk)

    print(h.hexdigest(), '- xxHash64 -', datetime.datetime.now() - start)


md5('testFile.mov')
xxHash32('testFile.mov')
xxHash64('testFile.mov')
