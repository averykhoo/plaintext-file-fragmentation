#   plaintext file fragmentation

##  what and why
-   converts a file or folder into a bunch of ascii plaintext files, and vice versa
-   lets you bypass restrictions on file types
-   note that you may get in trouble for bypassing restrictions and that's entirely on you

##  requirements
-   python 3.6

##  usage
### on the first PC
-   (if **input** folder does not exist) run `encode.bat` to create **input** folder
-   copy files or directories into **input** folder
-   run `encode.bat` *(about 1 min per 100 MB)*
-   your files will be archived to **input_archive**
-   transfer text files in **ascii85_encoded** to the other pc

### on the second PC
-   (if **ascii85_encoded** folder does not exist) run `decode.bat` to create **ascii85_encoded** folder
-   move text files to `ascii85_encoded`
-   run `decode.bat` *(about 1.5 min per 100 MB)*
-   take files out from **output_decoded**

##  how it works
### `frag_encode.py`
1.  tar and gzip input folder to .tgz file on disk
2.  break file into random-sized chunks
3.  encrypt each chunk separately using the rc4-drop stream cipher (randomized salt and IV per-file)
4.  a85 encode each encrypted chunk
5.  write each encoded chunk to a text file (with metadata as json in header line)
6.  backup original input files to a timestamped folder

### `frag_decode.py`
1.  the above steps in reverse
2.  allows you to decode multiple sets of chunks in one go
3.  decoded files are in a folder named according to the datetime you encoded it

##  manual alternative
1.  zip your file (right-click > send to > compressed folder)
2.  `certutil -encode -v archive.zip b64.txt`
3.  transfer **b64.txt** to your other PC
4.  `certutil -decode -v b64.txt archive.zip`

##  todo:
-   better encryption than rc4, but not too slow
    -   so i'm currently using rc4 because it's easy to implement in pure python, reasonably fast, and there aren't any stream ciphers in the builtins
    -   maybe [chacha](https://github.com/pts/chacha20/blob/master/chacha20_python3.py)
        -   check if it succeeds on the [test vectors](https://crypto.stackexchange.com/questions/22338/where-are-the-chacha20-test-vectors-examples)
    -   mitigating factors:
        -   we're using rc4-drop
        -   the key is effectively random
        -   the key is the full 256 bytes long
        -   the stream is limited to less than 2**25 bytes
-   setup logging, or provide receipts when zipping/unzipping?
-   unified text fragment class for reading and writing?
