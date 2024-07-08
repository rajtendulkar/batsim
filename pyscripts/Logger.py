import logging
import time


class BatSimLogger:
    def __init__(self):
        self.log_filename = "batsim.csv"
        with open(self.log_filename, 'w') as file:
            file.write("time, Vocv(mv), Vbat(mA), Ibat(mA), Vr(mV), Vr1c1(mV), Vr2c2(mV), batt cap(mAh), batt cap(%)\n")

    def log_bastsim_data(self, vocv_mv, vbatt_mv, ibat_ma, vr_mv, vr1c1_mv, vr2c2_mv, batt_cap_mah, batt_cap_percent):
        with open(self.log_filename, 'a') as file:
            file.write(f'{time.time()}, {vocv_mv}, {vbatt_mv}, {ibat_ma}, {vr_mv}, {vr1c1_mv}, {vr2c2_mv}, '
                       f'{batt_cap_mah}, {batt_cap_percent}\n')

