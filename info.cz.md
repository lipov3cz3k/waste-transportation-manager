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

##Instalace##
* Nainstalovat python3.6
(https://www.python.org/downloads/release/python-366/)
* Nainstalovat wheel balíčky z tools
```
pip install tools/shapely/Shapely-1.6.4.post1-cp36-cp36m-win_amd64.whl
pip install tools/rtree/Rtree-0.8.3-cp36-cp36m-win_amd64.whl
```
* Nainstalovat zbytek balíčků z pip
```
pip install -r src/requirements.txt
```
Konfigurace aplikace se provádí v souboru common/config.py.


##Grafické rozhraní##
```
python gui.py
```
Vytvořené konzolové okno je třeba nechat spuštěné, rozhraní pak bude k dispozici
ve webovém prohlížeči na adrese 127.0.0.1:5000

##Konzolové rozhraní##
```
python cli.py
```
Po spuštění bez parametrů je vypsána nápověda


##Import přihlášených odběrných míst/kontejnerů do databáze##
Načte z externího souboru všechny záznamy do databáze a pokusí se lokalizovat jednotlivé adresy
v OpenStreetMap - získá unikátní OSM ID každého záznamu

Neimportují se znovu kontejnery se stejným ID (viz identifikátor daného města)

Omezení API OpenStreetMap je jeden dotaz na adresu za sekundu
viz https://operations.osmfoundation.org/policies/nominatim/



###Podporovaná města###
#### Plzeň - Excel ####
- jako jednoznačný identifikátor je brán sloupeček ID_CONTAINER
- první řádek obsahuje tuto hlavičku (může být různá pořadí)
ID_CONTAINER Volume TrashType CollectionPlaceName Latitude Longitude Interval

#### Stavanger - CSV ####
- jako jednoznačný identifikátor je brán sloupeček CONTAINERNUMBER
- první řádek obsahuje tuto hlavičku
LATITUDE LONGITUDE CONTAINERNUMBER ADDRESS FRACTION COUNTER FILLHEIGHT DATE

#### Jihlava - dbf databáze ####
-  jako jednoznačný identifikátor je brán sloupeček OBJECTID
- tabulka obsahuje tyto sloupečky
ADRESA OBJECTID X Y OBYVATEL NAZEV POCET NADOBA OD_DATUM DO_DATUM CETNO_SVOZ
SVOZ_PO SVOZ_UT SVOZ_ST SVOZ_CT SVOZ_PA POZNAMKA TYP_VLASTN OPTIMUM KOEFICIENT POMER

#### Cheb - Excel ####
- jednotlivé listy jsou typy odpadu
- jednoznačný identifikátor je tvořen z hash těchto sloupců (#TECH_GRP#, Město, Ulice, č. p., Zahájení, číslo řádku)
- první řádek obsahuje tuto hlavičku
'Typ kontejneru ' 'Interval' 'Kód odpadu' 'Název odpadu' '#TECH_GRP#' 'Počet ks' 'MJ' 'Zahájení'
'Ukončení' 'Stav' 'Fakturovat' 'V trase' 'Město' 'Ulice' 'č. p.' 'Jméno a příjmení'
'Poznámka pro dispečera' 'Poznámka do faktury' 'Poznámka' 'Den svozu' 'POZNÁMKY PRO OPRAVY' 'Řádek' 'Pořadí'

Pokud název souboru obsahuje jméno města, není třeba specifikovat ručně. Jinak je nutné doplnit parametr s názvem města
```
python cli.py import --containers D:\cesta_k_souboru\plzen.xlsx
nebo
python cli.py import --containers D:\cesta_k_souboru\plzen.xlsx --city plzen
```

### další info ###
Pro testovací účely je přibalena také vzorová databáze incidentů,
nakopírujte tedy soubor /DB/data.db do lokálního adresáře aplikace 
(defaultně tedy do c:\ProgramData\WTM\db\ , lze změnit v konfiguraci)
