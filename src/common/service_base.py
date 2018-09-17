class ServiceBase:
    def __init__(self):
        self.run = {0: False}
        self.state = {}
        self.SetState(action="init", percentage=0)

    def TestIsRun(self):
        if not self.run[0]:
            raise Exception("Service not running")

    def SetState(self, action = None, percentage = None):
        if action != None:
            self.state['action'] = action
        if percentage != None:
            self.state['percentage'] = int(percentage)
