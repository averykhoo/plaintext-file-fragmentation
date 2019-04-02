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
1.  gzip (using `tarfile`)
2.  a85 encode
3.  automatically break into chunks
4.  automatically combine chunks for decoding
5.  decoded files are in a folder named according to the datetime you encoded it

##  to-do
-   setup logging, or provide receipts when zipping/unzipping?
