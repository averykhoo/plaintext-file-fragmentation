#   plaintext file fragmentation

##  what
-   breaks a file or folder into a bunch of ascii plaintext files

##  usage
-   put files/dirs in input folder (`input`)
-   run encode
-   transfer text files to other place (`ascii85_encoded`)
-   run decode
-   take files out (`output_decoded`)

##  how it works
### `frag_encode.py`
1.  gzip (using `tarfile`)
2.  automatically break into chunks
3.  encryt each chunk (blowfish CFB mode)
4.  a85 encode each chunk
5.  write to text file (with metadata in header)

### `frag_decode.py`
1.  the same but in reverse
2.  but it allows you to decode multiple sets of chunks in one go
3.  decoded files are in a folder named according to the datetime you encoded it

##  to-do
-   setup logging, or provide receipts when zipping/unzipping?

##  manual alternative
1.  zip your file
2.  `certutil -encode -v archive.zip b64.txt`
3.  `certutil -decode -v b64.txt archive.zip`
