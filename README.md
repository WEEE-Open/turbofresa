# T.U.R.B.O.F.R.E.S.A.  
Turboaggeggio Utile alla Rimorzione di Byte Obrobriosi e di abominevoli  
File da dischi rigidi Riciclati ed altri Elettronici Sistemi di  
Accumulazione (semi)permanente di dati.  

## INSTALLAZIONE
Scaricare il file `install.sh` da qualche parte e avviarlo con `sudo`.

## NOTE
Nella `piall@trice`, per evitare di loggarsi come `root` ma avviare lo stesso  
i subprocess che necessitano privilegi più alti senza dover mettere la password,  
aggiungere la seguente riga al file `/etc/sudoers`:

`piall ALL=(ALL) NOPASSWD : /usr/bin/turbofresa`

## TODO  
- [ ] Rendere i subprocess più sensati (attualmente non lo sono abbastanza).  
- [ ] Gestire i valori di ritorno dei singoli subprocess.  
- [ ] Implementare un algoritmo di lettura statistica del disco che determini con buona probabilità e rapidità se il disco é piallato o no.  
- [ ] Fare in modo che lo script legga da `lshw -c disk -json` il seriale del disco rigido e che interroghi il db del `tarallo` per ottenere il codice di inventario del disco rigido.  
- [ ] Fare in modo che lo script comunichi con il `tarallo` in modo tale da aggiornare l'inventario automaticamente non appena il disco è piallato.  
- [ ] Creare un'amena web-app che controlli lo script tramite `ssh` e che sia in grado di accendere la piall@trice (WOL) e fornire informazioni sullo stato della suddetta macchina e sullo stato dei task in esecuzione.  
