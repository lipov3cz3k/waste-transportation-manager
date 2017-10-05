from common.alertc import TMCUpdateClass
from common.highway_classes import HighwayClass
class RoutingType:
    basic = 1
    worstCase = 2
    stochasticWS = 3
    stochasticWad = 4
    lengthOnly = 5


def GetPenaltyMul(incidents):
    worst_penalty_mul = 1
    for incident in incidents:
        worst_penalty_mul += (TMCUpdateClass.ClassToPenalization[incident['class']])
    return worst_penalty_mul

def GetHighwayPenalty(type):
    return HighwayClass.ClassToPenalization.get(type, HighwayClass.ClassToPenalization['default'] )