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

## CONFIGURATION
Before running the program you have to create a .env file with the fields `TARALLO_URL` and `TARALLO_TOKEN` with the ones of your T.A.R.A.L.L.O. instance. The file formatting is as follows:

```
export TARALLO_URL=http://localhost:8080
export TARALLO_TOKEN=super-secret-token-nobody-should-actually-know
```
If you're running inside pipenv you might need to restart the virtual shell to allow it to update the environmental variables.
