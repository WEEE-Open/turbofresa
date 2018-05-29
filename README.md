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

And modify the `.zshrc` or `.bashrc` file adding the required secret environment variables.  

## TODO  
- [X] Call subprocesses in a decent way (at the moment they kinda suck).  
- [X] Close and reopen the logFile in order to make it readable. Make it more verbose.  
- [X] Retrieve HDD codes from `tarallo` database using `requests` module.  
- [ ] Find a more proper way to parse the serial number of the hard drives.  
- [ ] Sending a proper HTTP request to `tarallo` to tell him to automatically move connected HDDs to `piall@trice`.  
- [ ] Automatically update `tarallo` database once the erasing process is terminated or once it turns out that the HDD is fucked up.  
