## Modelování rizik v dopravě - Risk modelling in transportation##

This repository contains source files for Master Thesis [Risk modelling in transportaion](https://www.vutbr.cz/en/studies/final-thesis?zp_id=91589)

It collects traffic informations from JSDI provider and solves network problem of shortest path between geographical points. It is based on special paths evaluation depending on the frequency of traffic incidents based on real historical data.

# Installation #

1. Set interface for JSDI traffic information - you can use php script from jsdi-api folder.
2. Set proper FTP login in file src/common/config.py
3. Install python with all supporting libraries (requirements.txt)
4. Start application (python main.py or gui.py)