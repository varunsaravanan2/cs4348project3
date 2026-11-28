import sys
import os

BLOCK_SIZE = 512
MAGIC = b"4348PRJ3"

# minimal degree 10, so a node holds up to 19 keys and 20 children
MAX_KEYS = 19
MAX_CHILDREN = 20


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


# a node in memory is just a dict with the same fields as the block
def new_node(block_id, parent):
    return {
        "id": block_id,
        "parent": parent,
        "n": 0,
        "keys": [0] * MAX_KEYS,
        "values": [0] * MAX_KEYS,
        "children": [0] * MAX_CHILDREN,
    }


# node block layout: id, parent, number of keys, 19 keys, 19 values, 20 children
def write_node(f, node):
    data = to_bytes(node["id"]) + to_bytes(node["parent"]) + to_bytes(node["n"])
    for k in node["keys"]:
        data = data + to_bytes(k)
    for v in node["values"]:
        data = data + to_bytes(v)
    for c in node["children"]:
        data = data + to_bytes(c)
    data = data + bytes(BLOCK_SIZE - len(data))
    f.seek(node["id"] * BLOCK_SIZE)
    f.write(data)


def read_node(f, block_id):
    f.seek(block_id * BLOCK_SIZE)
    data = f.read(BLOCK_SIZE)
    node = new_node(from_bytes(data[0:8]), from_bytes(data[8:16]))
    node["n"] = from_bytes(data[16:24])
    pos = 24
    for i in range(MAX_KEYS):
        node["keys"][i] = from_bytes(data[pos:pos + 8])
        pos += 8
    for i in range(MAX_KEYS):
        node["values"][i] = from_bytes(data[pos:pos + 8])
        pos += 8
    for i in range(MAX_CHILDREN):
        node["children"][i] = from_bytes(data[pos:pos + 8])
        pos += 8
    return node


# keys and values have to fit in an unsigned 8 byte number
def to_number(text, what):
    if not text.isdigit():
        error(what + " must be a non-negative whole number, got " + text)
    n = int(text)
    if n >= 2 ** 64:
        error(what + " is too big, got " + text)
    return n


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


# looks for a key going down from the root, only holding one node at a time.
# gives back the value, or None if the key isn't there
def find(f, root, key):
    block_id = root
    while block_id != 0:
        node = read_node(f, block_id)
        i = 0
        while i < node["n"] and key > node["keys"][i]:
            i += 1
        if i < node["n"] and node["keys"][i] == key:
            return node["values"][i]
        block_id = node["children"][i]
    return None


def is_leaf(node):
    return node["children"][0] == 0


# write just the 8 byte parent field of a node without loading the whole node
def set_parent(f, block_id, parent):
    f.seek(block_id * BLOCK_SIZE + 8)
    f.write(to_bytes(parent))


# splits the full child y, which is child number i of parent x.
# y keeps the first 9 keys, the new node z gets the last 9,
# and the middle key moves up into x. only x, y, and z are in memory.
def split_child(f, x, i, y, next_block):
    z = new_node(next_block, x["id"])
    z["n"] = 9
    for j in range(9):
        z["keys"][j] = y["keys"][j + 10]
        z["values"][j] = y["values"][j + 10]

    # the last 10 children move over to z, so their parent field has to change
    if not is_leaf(y):
        for j in range(10):
            z["children"][j] = y["children"][j + 10]
            set_parent(f, z["children"][j], z["id"])

    middle_key = y["keys"][9]
    middle_value = y["values"][9]

    # clear out the spots y doesn't use anymore
    for j in range(9, MAX_KEYS):
        y["keys"][j] = 0
        y["values"][j] = 0
    for j in range(10, MAX_CHILDREN):
        y["children"][j] = 0
    y["n"] = 9

    # make room in x for z and the middle key
    for j in range(x["n"], i, -1):
        x["children"][j + 1] = x["children"][j]
    x["children"][i + 1] = z["id"]
    for j in range(x["n"] - 1, i - 1, -1):
        x["keys"][j + 1] = x["keys"][j]
        x["values"][j + 1] = x["values"][j]
    x["keys"][i] = middle_key
    x["values"][i] = middle_value
    x["n"] += 1

    write_node(f, y)
    write_node(f, z)
    write_node(f, x)
    return z


def insert(filename, key, value):
    with open(filename, "r+b") as f:
        root, next_block = read_header(f)

        # empty tree, so this key becomes the first node
        if root == 0:
            node = new_node(next_block, 0)
            node["n"] = 1
            node["keys"][0] = key
            node["values"][0] = value
            write_node(f, node)
            write_header(f, node["id"], next_block + 1)
            print("Inserted " + str(key) + ", " + str(value))
            return

        # no duplicate keys
        if find(f, root, key) is not None:
            error("key " + str(key) + " is already in the index")

        x = read_node(f, root)

        # if the root is full, make a new root above it and split the old one.
        # this is the only way the tree gets taller
        if x["n"] == MAX_KEYS:
            new_root = new_node(next_block, 0)
            new_root["children"][0] = x["id"]
            x["parent"] = new_root["id"]
            next_block += 1
            split_child(f, new_root, 0, x, next_block)
            next_block += 1
            root = new_root["id"]
            write_header(f, root, next_block)
            x = new_root
            new_root = None

        # go down to a leaf, splitting any full child before moving into it,
        # so there's always room for a key that gets pushed up
        while not is_leaf(x):
            i = 0
            while i < x["n"] and key > x["keys"][i]:
                i += 1
            child = read_node(f, x["children"][i])
            if child["n"] == MAX_KEYS:
                z = split_child(f, x, i, child, next_block)
                next_block += 1
                write_header(f, root, next_block)
                if key > x["keys"][i]:
                    child = z
                # done with whichever half we're not going into,
                # so it doesn't count toward the 3 nodes in memory
                z = None
            x = child

        # x is a leaf with room, so shift bigger keys over and put the key in
        i = x["n"] - 1
        while i >= 0 and x["keys"][i] > key:
            x["keys"][i + 1] = x["keys"][i]
            x["values"][i + 1] = x["values"][i]
            i -= 1
        x["keys"][i + 1] = key
        x["values"][i + 1] = value
        x["n"] += 1
        write_node(f, x)
        print("Inserted " + str(key) + ", " + str(value))


def search(filename, key):
    with open(filename, "rb") as f:
        root, next_block = read_header(f)
        value = find(f, root, key)
    if value is None:
        error("key " + str(key) + " not found")
    print(str(key) + ", " + str(value))


def main():
    if len(sys.argv) < 3:
        print("Usage: python project3.py <command> <index file> [arguments]")
        print("Commands: create, insert, search, load, print, extract")
        sys.exit(1)

    command = sys.argv[1]
    filename = sys.argv[2]

    if command == "create":
        create(filename)
    elif command == "insert":
        check_index_file(filename)
        if len(sys.argv) != 5:
            error("insert needs a key and a value")
        insert(filename, to_number(sys.argv[3], "key"), to_number(sys.argv[4], "value"))
    elif command == "search":
        check_index_file(filename)
        if len(sys.argv) != 4:
            error("search needs a key")
        search(filename, to_number(sys.argv[3], "key"))
    elif command in ("load", "print", "extract"):
        check_index_file(filename)
        print(command + " is not done yet")
    else:
        error("unknown command " + command)


main()