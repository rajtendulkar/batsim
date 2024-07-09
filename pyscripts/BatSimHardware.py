
# This class should implement commands to control battery simulator hardware
# For example Keithley 2308, which has an ability to sink current.
class BatSimHw:
    def __init__(self):
        print("Hardware battery simulator, only simulated")
        self.external_load_mA = 100

    def measure_ibatt_ma(self):
        return self.external_load_mA

    def set_ibatt_load_ma(self, load_mA):
        self.external_load_mA = load_mA

    def set_vbatt_mv(self, vbatt_mv):
        # Set the output voltage on the hardware power supply
        vbatt_mv = 0

