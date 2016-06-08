#MODELOVÁNÍ RIZIK V DOPRAVĚ#
###Adresářová struktura###
```
/src	- zdrojový kód navržené aplikace
/jsdi-api		- skript pro ukládání dopravních informací přes rozhraní DDR
===Příloha DP navíc obsahuje===
/DB				- ukázková databáze (pouze na DVD)
/Latex			- zdrojové soubory textu diplomové práce (pouze na DVD)
readme.txt		- informace o spuštění aplikace
DP-Lipovsky.pdf	- diplomová práce
```

###Aplikace pro hledání nejkratší cesty###
Aplikace umožňuje zpracovat a analyzovat historická data o dopravě pomocí JSDI.
Součástí je konzolové a grafické uživatelské prostředí.
Pro spuštění je nutné mít nainstalován Python ve verzi 3.5 
(https://www.python.org/downloads/release/python-351/) 
a dále externí knihovny sqlalchemy, geopy, flask, networkx, pandas, tqdm,
nominatim, iso8601, geojson.
K instalaci lze použít nástroj pip zadáním příkazu pip install nazev_knihovny.

Grafické rozhraní aplikace se spustí příkazem:
python gui.py (v adresáři s aplikací)
vytvořené konzolové okno je třeba nechat spuštěné, rozhraní pak bude k dispozici
ve webovém prohlížeči na adrese 127.0.0.1:5000

Konzolové rozhraní je spustitelné příkazem:
python main.py
po spuštění konzolové verze bez zadání parametrů je vypsána nápověda.

Pro testovací účely je přibalena také vzorová databáze incidentů,
nakopírujte tedy soubor /DB/data.db do lokálního adresáře aplikace 
(defaultně tedy do c:\ProgramData\MasterThesis\db\ , lze změnit v konfiguraci)

Konfigurace aplikace se provádí v souboru common/config.py.