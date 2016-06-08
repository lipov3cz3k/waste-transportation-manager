from common.alertc import TMCUpdateClass

class RoutingType:
    basic = 0
    worstCase = 1
    stochasticWS = 2
    stochasticWad = 3


def GetPenaltyMul(incidents):
    worst_penalty_mul = 1
    for incident in incidents:
        worst_penalty_mul += (TMCUpdateClass.ClassToPenalization[incident['class']])
    return worst_penalty_mul