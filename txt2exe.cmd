del b64.txt
type out\*.txt > b64.txt
certutil -decode -v b64.txt transfer.out.7z
del b64.txt