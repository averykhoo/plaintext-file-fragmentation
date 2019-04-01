#   plaintext file fragmentation

##  what
-   breaks a file or folder into a bunch of ascii plaintext files

##  how it works
1.  gzip (using `tarfile`)
2.  a85 encode(function included so it works for python 3.3 or lower)
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