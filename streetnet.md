Hledání atributů v síti streetnet:


Formát excel tabulky:
```
|start       |cil         |parametr |metoda|vysledek
|CZ0644584495|CZ0644584584|AADT_2010|avg   |
```
možné metody (`avg`, `min`, `max`)


spustíme příkazovou řádku (`Win+R`, `cmd`)

spustíme hledání (`python cli.py export ID_GRAFU --trackinfo CESTA_K_EXCELU`)
`python d:/WTM-repo/src/cli.py export 442311_2018-04-04-16-32-10 --trackinfo d:/WTM/test.xlsx`

(během hledání atributů je nutné mít excel tabulku zavřenou)
