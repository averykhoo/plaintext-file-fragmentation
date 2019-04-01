#   plaintext file fragmentation

##  what
-   breaks a file or folder into a bunch of ascii plaintext files

##  how it works
1.  gzip (using `tarfile`)
2.  a85 encode
4.  automatically break into chunks
5.  automatically combine chunks for decoding