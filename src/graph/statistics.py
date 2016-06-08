import pandas as pd
from collections import Counter

def createCorrelation(graph, param):
    incidents = []
    for n1, n2, e in graph.edges_iter(data=True):
        if e['incidents']:
            incidents.append(Counter([d[param] for d in e['incidents']]))

    df = pd.DataFrame(incidents).fillna(0)
    return df.corr()
              

def correlationVisualize(corr, name=""):
    try:
        import numpy as np
        import seaborn as sns
        import matplotlib.pyplot as plt
    except ImportError:
        return
    # Generate a mask for the upper triangle
    mask = np.zeros_like(corr, dtype=np.bool)
    mask[np.triu_indices_from(mask)] = True  

    # Set up the matplotlib figure
    f, ax = plt.subplots(figsize=(7, 4))

    # Generate a custom diverging colormap
    cmap = sns.diverging_palette(220, 10, as_cmap=True)

    sns.heatmap(corr, cmap=cmap, vmax=.8, square=True, annot=True)
    plt.savefig('correlation-'+name+'.svg', format='svg', dpi=1200)
    #plt.show()