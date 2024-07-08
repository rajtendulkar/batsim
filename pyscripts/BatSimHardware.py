
# This class should implement commands to control battery simulator hardware
# For example Keithley 2308, which has an ability to sink current.
class BatSimHw:
    def __init__(self):
        print("Hardware battery simulator, only simulated")
        self.external_load_mA = 100

    def measure_ibatt_mA(self):
        return self.external_load_mA

    def set_ibatt_load_mA(self, load_mA):
        self.external_load_mA = load_mA
