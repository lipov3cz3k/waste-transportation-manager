#Správce svozu odpadu#
###Adresářová struktura###
```
/src	- zdrojový kód navržené aplikace
/jsdi-api		- skript pro ukládání dopravních informací přes rozhraní DDR
/tools -
database_structure.cz.md - struktura databáze
info.cz.md - tento soubor
README.md		- informace o spuštění aplikace
```

### Import a export dat přihlášených odběrných míst/kontejnerů z růných ORP ###
Pro spuštění je nutné mít nainstalován Python ve verzi 3.5 
(https://www.python.org/downloads/release/python-351/) 
a dále externí knihovny sqlalchemy, geopy, flask, networkx, tqdm, 
nominatim, iso8601, geojson, shapepy, openpyxl, dbfread, pyproj. (pandas)

K instalaci lze použít nástroj pip zadáním příkazu pip install nazev_knihovny.

Grafické rozhraní aplikace se spustí příkazem:
python gui.py (v adresáři s aplikací)
vytvořené konzolové okno je třeba nechat spuštěné, rozhraní pak bude k dispozici
ve webovém prohlížeči na adrese 127.0.0.1:5000

Konzolové rozhraní je spustitelné příkazem:
python cli.py
po spuštění konzolové verze bez zadání parametrů je vypsána nápověda.

Pro testovací účely je přibalena také vzorová databáze incidentů,
nakopírujte tedy soubor /DB/data.db do lokálního adresáře aplikace 
(defaultně tedy do c:\ProgramData\WTM\db\ , lze změnit v konfiguraci)

Konfigurace aplikace se provádí v souboru common/config.py.
