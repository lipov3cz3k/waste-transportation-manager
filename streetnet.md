=======Hledání atributů v síti streetnet:===========


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


====Postup vytvoření nového grafu=====
`python cli.py create ID_OBLASTI`

ID OBLASTÍ
51684 ČR
435541 Hlavní město Praha
442397 Středočeský kraj
442321 Jihočeský kraj
442466 Plzeňský kraj
442314 Karlovarský kraj
442452 Ústecký kraj
442455 Liberecký kraj
442463 Královéhradecký kraj
442460 Pardubický kraj
442459 Olomoucký kraj
442461 Moravskoslezský kraj
442311 Jihomoravský kraj
442449 Zlínský kraj
442453 Kraj Vysočina

=====Postup exportu grafu měst======
`python cli.py export ID_GRAFU --citygraph`
