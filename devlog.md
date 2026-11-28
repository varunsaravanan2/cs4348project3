# 11-23 12:34pm

Starting project 3. This time, I need to implement one command-line program in Python that creates, maintains index files containing B-trees (each file contains one B-tree). Every execution of this program performs one command and exits: it creates, inserts into or searches the file.

The file is divided into blocks of 512 bytes each. The first block is the header, containing the magic number 4348PRJ3, block id of the root, and id of the next free block. Then, every other node is allocated its own block, and it has its own id, parent’s id, amount of keys, and then 19 keys, 19 values, and 20 child pointers. All numbers have to be encoded in 8 bytes in big endian order, so I will be using to_bytes(8, 'big') and int.from_bytes to encode and decode numbers. The important restriction is that I will be able to have no more than 3 nodes in memory, so I can’t load the whole tree.

For this session, I will configure the git, add the header and make the creation functionality to work. In addition, I will also do the check if the file is an index file or not by checking the first eight bytes of the file, which should be the magic number.

# 11-26 12:32pm

Now header and create command work. Create creates a new file that consists of only the header block, which includes the magic number, root id, next block id, filled with zeros the rest of 512 bytes. If the file already exists it outputs an error and does not touch the file.

When making a new tree I assign root id = 0 and next block id = 1. Assigning 0 to root id means that the tree is empty, which is possible since block 0 is always header block, and therefore the root cannot possibly be there. The first node will reside in block 1. Also, now I have made check whether the file is a valid index file. It checks that the file exists, has length of at least one block and starts with 4348PRJ3 and all other commands except create execute it before doing anything.

I've tested creating a file, then creating the same file again to check that it gives an error and does not change the file and executing search command on a nonexistent file and on some normal text file. All these cases returned the correct errors instead of crashing.

Reading and writing nodes, inserting, and search next.

# 11-26 1:37pm

Starting session 2. Create works but there is no real tree yet, so this session will be about creating nodes, inserting to a one node tree and searching.

The node data structure fits into one 512 byte block, starting at byte n * 512. Inside we have the id of the node, its parent id, number of keys, then 19 keys, 19 values and 20 child pointers, all 8 byte big-endian. I will create one function for converting a node to a list of bytes and vice versa, so the rest of the program can just use the node structure without worrying about offsets.

Inserting a key when the tree is empty, will create the first node in block 1 and will be the root of the tree. Otherwise the key goes into the root node in sorted order. Searching starts at the root node and uses child pointers, therefore it keeps only one node in memory at a time. Splitting will come in the next session, so the tree will stop at 19 keys.


# 11-26 7:42pm

Got nodes, insert, and search running. A node in memory is just a dict with the same keys as the block, and I have one function that writes the node into the block and another that reads it, so everything else uses the dict interface and not any byte offsets. If the tree is empty, insert creates the first node in block 1 and makes that the root. After that, newly added keys will be moved to sorted order.

Since the specification doesn't say how to handle duplicates, I print an error message and ignore the key. Also, I won't accept negative numbers or non-numbers, or anything 2^64 or bigger, as keys or values because they can only be stored as 8 byte unsigned integers.

My test inserts the keys out of order, then searches for all of them and for one key that's not there, adds a duplicate, and throws a negative number and a word. At this point, the tree can only hold 19 keys, as the splitting functionality hasn't been implemented yet.

Splitting coming up next.


# 11-27 12:25pm

Got nodes, insert, and search running. A node in memory is just a dict with the same keys as the block, and I have one function that writes the node into the block and another that reads it, so everything else uses the dict interface and not any byte offsets. If the tree is empty, insert creates the first node in block 1 and makes that the root. After that, newly added keys will be moved to sorted order.

Since the specification doesn't say how to handle duplicates, I print an error message and ignore the key. Also, I won't accept negative numbers or non-numbers, or anything 2^64 or bigger, as keys or values because they can only be stored as 8 byte unsigned integers.

My test inserts the keys out of order, then searches for all of them and for one key that's not there, adds a duplicate, and throws a negative number and a word. At this point, the tree can only hold 19 keys, as the splitting functionality hasn't been implemented yet.

Splitting coming up next.

# 11-27 5:46pm

Splitting works, so now the tree can be extended beyond 19 keys. A full node splits into two nodes of 9 keys each, and the middle key goes up into the parent node. If the root is full, I create a new root above it, so that's how the tree grows in height.

While inserting, I split full nodes along the way down, which means that there will be enough space in the parent for the moved key. So a split operation requires three nodes: parent node, full node and new node. Since children from the full node are moving to the new node, I need to change their parent field, but rather than loading these nodes, I simply store 8-byte long parent fields in each of them. And I had to unload the other half of the split after the split operation, since otherwise another split operation further down would have kept 4 nodes in memory.

I've tested it by inserting 100 keys and looking for keys at beginning, middle, end and one non-existent key.

Next step is to print, load and extract operations.

# 11-27 9:04pm

Starting Session 4. Everything up until now (insert, search, and splitting) works. In this session I will add the last three commands: print, load, and extract.

Both extract and print have to visit every key, in order. The usual algorithm would be in-order traversal that involves keeping every node along the way from the root in memory. This can be more than 3 after the tree gets high enough. For this reason I'm going to do these commands using parent pointers. I will maintain just the current node and once I'm done visiting it, will check the parent for my block ID to resume searching from there. This way I will have at most one or two nodes in memory.

Load command loads a csv file with key/value pairs and adds the entries as the function insert does. I still have to make a decision about how to process lines that aren't valid. This can happen if a value is missing or it isn't a number. The extract command will write every pair into a new file in the same format and if the file already exists, will throw an error, as create did.