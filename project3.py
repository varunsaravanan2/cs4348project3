import sys
import os

BLOCK_SIZE = 512
MAGIC = b"4348PRJ3"


# every number in the file is 8 bytes, big endian
def to_bytes(n):
    return n.to_bytes(8, "big")


def from_bytes(b):
    return int.from_bytes(b, "big")


def error(msg):
    print("Error: " + msg)
    sys.exit(1)


# header is block 0: magic number, root id, next block id, then unused space
def write_header(f, root, next_block):
    data = MAGIC + to_bytes(root) + to_bytes(next_block)
    data = data + bytes(BLOCK_SIZE - len(data))   # pad the rest of the block with zeros
    f.seek(0)
    f.write(data)


def read_header(f):
    f.seek(0)
    data = f.read(BLOCK_SIZE)
    root = from_bytes(data[8:16])
    next_block = from_bytes(data[16:24])
    return root, next_block


# a file is a valid index file if it exists, has a full header block,
# and starts with the magic number
def check_index_file(filename):
    if not os.path.isfile(filename):
        error("file " + filename + " does not exist")
    with open(filename, "rb") as f:
        data = f.read(BLOCK_SIZE)
    if len(data) < BLOCK_SIZE or data[:8] != MAGIC:
        error(filename + " is not a valid index file")


def create(filename):
    if os.path.exists(filename):
        error("file " + filename + " already exists")
    with open(filename, "wb") as f:
        # empty tree: root is 0, and the first node will go in block 1
        write_header(f, 0, 1)
    print("Created index file " + filename)


def main():
    if len(sys.argv) < 3:
        print("Usage: python project3.py <command> <index file> [arguments]")
        print("Commands: create, insert, search, load, print, extract")
        sys.exit(1)

    command = sys.argv[1]
    filename = sys.argv[2]

    if command == "create":
        create(filename)
    elif command in ("insert", "search", "load", "print", "extract"):
        check_index_file(filename)
        print(command + " is not done yet")
    else:
        error("unknown command " + command)


main()