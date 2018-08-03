## Waste transportation manager##

This repository contains source files for waste management project


# Installation #

1. Set proper FTP login in file src/common/config.py
2. Install python (https://www.python.org/downloads/release/), tick checkbox - Add Python to the PATH
2.1 Install all supporting libraries from (/src/requirements.txt) by command: pip install LIB_NAME (e.g. "pip install Flask" next..)
2.2 Libraries: Shapely, Rtree should be installed manually 
    go to waste-transportation-manager/tools/ or download from http://www.lfd.uci.edu/~gohlke/pythonlibs/#shapely ... this package contains GEOS lib
    command: pip install LIB_PATH (e.g. "pip install X:\waste-transportation-manager-orp_export\tools\shapely\Shapely-1.6.4.post1-cp36-cp36m-win_amd64.whl")
3. Start application (python cly.py or gui.py), browser: http://127.0.0.1:5000
