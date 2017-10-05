class HighwayClass:
    # Set penalization for specific class
    # becouse interval 0-1 is too large, we divide this values by 2
    # real penalty for each edge is sum of lifetime penalties + 1
    # real penalty is multiplated by edge lengths
    ClassToPenalization = {
        'track' : 1000,

        'default' : 1,
        'NONE' : 0
    }