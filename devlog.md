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