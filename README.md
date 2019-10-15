# T.U.R.B.O.F.R.E.S.A.  

Turboaggeggio Utile alla Rimozione di Byte Obrobriosi e di abominevoli
File da dischi rigidi Riciclati ed altri Elettronici Sistemi di
Archiviazione di dati.

## INSTALL  

Use `pipenv shell` to get a shell in the virtual environment, then
`pipenv install` to install dependencies.

If you want to piallare some hard drives, edit `/etc/sudoers` file and add:  

`piall ALL=(ALL) NOPASSWD : /sbin/shutdown`  
`piall ALL=(ALL) NOPASSWD : /sbin/badblocks`  
`piall ALL=(ALL) NOPASSWD : /sbin/smartctl`  
