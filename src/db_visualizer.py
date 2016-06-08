import sadisplay

import ddr.ddr_models as ddr

#desc = sadisplay.describe([getattr(ddr, attr) for attr in dir(ddr)])
desc = sadisplay.describe([ddr.DOC, ddr.MJD, ddr.MSG, ddr.MEVT, ddr.TMCE, ddr.EVI, ddr.MLOC, ddr.SNTL, ddr.COORD, ddr.Location, ddr.WDEST, ddr.MTIME, ddr.TSTA, ddr.TSTO, ddr.MTXT])
w = sadisplay.plantuml(desc)
open('schema.plantuml', 'w', encoding="utf-8").write(w)
#open('schema.dot', 'w', encoding="utf-8").write(sadisplay.dot(desc))