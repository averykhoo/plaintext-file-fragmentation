#   plaintext file fragmentation

##  what
-   breaks a file or folder into a bunch of ascii plaintext files

##  usage
-   put files/dirs in input folder
-   run encode
-   transfer text files to other place
-   run decode

##  how it works
1.  gzip (using `tarfile`)
2.  a85 encode
3.  automatically break into chunks
4.  automatically combine chunks for decoding

##  todo
-   don't use tempfiles if possible, gzip and b64 encode/decode on the fly
    -   try a 4mb buffer write direct to base64 using amazon's b64 wrapper
-   setup logging, or provide receipts when zipping/unzipping?