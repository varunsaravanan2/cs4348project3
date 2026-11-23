# 11-23 12:34pm

Starting project 3. This time, I need to implement one command-line program in Python that creates, maintains index files containing B-trees (each file contains one B-tree). Every execution of this program performs one command and exits: it creates, inserts into or searches the file.

The file is divided into blocks of 512 bytes each. The first block is the header, containing the magic number 4348PRJ3, block id of the root, and id of the next free block. Then, every other node is allocated its own block, and it has its own id, parent’s id, amount of keys, and then 19 keys, 19 values, and 20 child pointers. All numbers have to be encoded in 8 bytes in big endian order, so I will be using to_bytes(8, 'big') and int.from_bytes to encode and decode numbers. The important restriction is that I will be able to have no more than 3 nodes in memory, so I can’t load the whole tree.

For this session, I will configure the git, add the header and make the creation functionality to work. In addition, I will also do the check if the file is an index file or not by checking the first eight bytes of the file, which should be the magic number.