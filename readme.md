#   plaintext file fragmentation

##  what
-   breaks a file or folder into a bunch of ascii plaintext files
-   requires python >= 3.6 (format strings)
    -   or >= 3.4 (if you fix format strings)
    -   or >= 3 (if you use a85 from utils and fix fstrings)

##  usage
-   put files/dirs in input folder
-   run encode
-   transfer text files to other place
-   run decode

##  how it works
1.  gzip (using `tarfile`)
2.  a85 encode
4.  automatically break into chunks
5.  automatically combine chunks for decoding

##  todo
-   only use two folders?
    -   "plaintext-encoded" and "originals"
-   don't use tempfiles if possible, gzip and b64 encode/decode on the fly
-   use datetimes as folder names when unzipping to deconflict
    -   datetime.tmp.tar.gz
-   provide receipts whe zipping/unzipping
-   better logging
-   write to partial file then rename for atomicity
-   don't use hash, use datetime + file id
-   if temp files are necessary the use a temp folder
-   try a 4mb buffer write direct to base64 using amazon's b64 wrapper
-   use pathlib?