# T.U.R.B.O.F.R.E.S.A.  
Turboaggeggio Utile alla Rimorzione di Byte Obrobriosi e di abominevoli  
File da dischi rigidi Riciclati ed altri Elettronici Sistemi di  
Archiviazione di dati.  

## INSTALL  
Download the `install.sh` file and run it with `root` privileges.  

In the `piall@trice`, modify the `/etc/sudoers` file adding these lines:  

`piall ALL=(ALL) NOPASSWD : /sbin/shutdown`  
`piall ALL=(ALL) NOPASSWD : /sbin/badblocks`  
`piall ALL=(ALL) NOPASSWD : /sbin/smartctl`  

And add the required values to the config file.
