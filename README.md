#   plaintext file fragmentation

##  what
-   breaks a file or folder into a bunch of ascii plaintext files

##  requirements
-   python 3

##  usage
-   put files/dirs in input folder (`input`)
-   run encode *(about 1 min per 100 MB)*
-   transfer text files to other place (`ascii85_encoded`)
-   run decode *(about 1.5 min per 100 MB)*
-   take files out (`output_decoded`)

##  how it works
### `frag_encode.py`
1.  tar and gzip to binary file on disk
2.  break file into random-sized chunks 
3.  encrypt each chunk separately using the rc4-drop stream cipher (this might be bad practice?)
4.  a85 encode each encrypted chunk
5.  write each encoded chunk to a text file (with metadata as json in header line)
6.  backup original input files to a timestamped folder 

### `frag_decode.py`
1.  the above steps in reverse
2.  allows you to decode multiple sets of chunks in one go
3.  decoded files are in a folder named according to the datetime you encoded it

##  to-do
-   setup logging, or provide receipts when zipping/unzipping?
-   encrypt original file name?

##  manual alternative
1.  zip your file (right-click > send to > compressed folder)
2.  `certutil -encode -v archive.zip b64.txt`
3.  `certutil -decode -v b64.txt archive.zip`

##  todo:
-   use `pathlib`
-   backup inputs to the output folder instead?
-   unified text fragment class for reading and writing?
