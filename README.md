## Waste transportation manager##

This repository contains source files for waste management project


# Installation #

1. Set proper FTP login in file src/common/config.py
2. Install python (https://www.python.org/downloads/release/), tick checkbox - Add Python to the PATH
2.1 Install all supporting libraries from (/src/requirements.txt) by command pip install LIB_NAME
2.2 Libraries: Shapely, Rtree should be installed manually
    go to waste-transportation-manager/tools/ or download from http://www.lfd.uci.edu/~gohlke/pythonlibs/#shapely ... this package contains GEOS lib
    command: pip install LIB_PATH
3. Start application (python main.py or gui.py)
