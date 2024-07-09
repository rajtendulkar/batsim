from PyQt6.QtCore import QTimer
import math
import time
from Logger import BatSimLogger
from BatSimHardware import BatSimHw


def calculate_rc_voltage(time_delta, vprev_mv, v_mv, ibatt_mA, r_mohms, c_F):
    tau = r_mohms * c_F / 1e3

    if time_delta <= 5 * tau:
        vrc_mv = vprev_mv * math.exp(-time_delta / tau) + (ibatt_mA * r_mohms / 1000) * (
                    1 - math.exp(-time_delta / tau))
    else:
        # beyond 5RC, voltage drop should be equal to drop across resistor
        vrc_mv = ibatt_mA * r_mohms / 1000

    print("Tau: " + str(tau) + " vrc: " + str(vrc_mv) + " time: " + str(time_delta))

    return vrc_mv


class BatSimCore:
    def __init__(self, ui):
        self.r_mohms = 0
        self.r1_mohms = 0
        self.r2_mohms = 0
        self.c1_F = 0
        self.c2_F = 0
        self.ocv_table = []
        self.rc_enabled = True
        self.battery_capacity_mah = 0
        self.current_battery_capacity_mas = 0
        self.battery_capacity_percent = 0

        self.refreshRateMilliseconds = 1000
        self.log = BatSimLogger()
        self.timer = QTimer()
        self.timer.setInterval(self.refreshRateMilliseconds)
        self.timer.timeout.connect(self.batsim_update_timer_expired)
        self.vbatt_mv = 0
        self.ibatt_mA = 0
        self.vocv_mv = 0
        self.vr_mv = 0
        self.vr1c1_mv = 0
        self.vr2c2_mv = 0
        self.vr1c1_prev_mv = 0
        self.vr2c2_prev_mv = 0
        self.last_update_time = 0
        self.rc_calculation_start_time = 0
        self.last_time = 0

        self.batsimHw = BatSimHw()
        self.ui = ui

    def enable_external_load(self, load_mA):
        self.batsimHw.set_ibatt_load_ma(load_mA)

    def update_rc_params(self, rc_enabled, r_mohms, r1_mohms, r2_mohms, c1_F, c2_F, battery_initial_capacity_percent,
                         battery_capacity_mah, ocv_table):
        self.r_mohms = r_mohms
        self.r1_mohms = r1_mohms
        self.r2_mohms = r2_mohms
        self.c1_F = c1_F
        self.c2_F = c2_F
        self.rc_enabled = rc_enabled
        self.ocv_table = ocv_table
        self.battery_capacity_percent = battery_initial_capacity_percent
        self.battery_capacity_mah = battery_capacity_mah
        self.current_battery_capacity_mas = battery_capacity_mah * 60 * 60

    def calculate_ocv(self):
        if self.battery_capacity_mah != 0:
            self.battery_capacity_percent = self.current_battery_capacity_mas * 100 / (
                        60 * 60 * self.battery_capacity_mah)
        else:
            self.battery_capacity_mah = 0

        if self.battery_capacity_percent.is_integer():
            ocv_mv = self.ocv_table[int(self.battery_capacity_percent)]
        else:
            ocv_lower = self.ocv_table[math.floor(self.battery_capacity_percent)]
            ocv_upper = self.ocv_table[math.ceil(self.battery_capacity_percent)]

            ocv_mv = (ocv_lower + (ocv_upper - ocv_lower) *
                      (self.battery_capacity_percent - math.floor(self.battery_capacity_percent)))

        return ocv_mv

    def batsim_update_timer_expired(self):
        print("timer expired.")
        current_time = time.perf_counter()

        # Drained battery
        drained_battery = self.ibatt_mA * (current_time - self.rc_calculation_start_time)
        self.current_battery_capacity_mas -= drained_battery

        if self.current_battery_capacity_mas < 0:
            self.current_battery_capacity_mas = 0

        # calculate vocv
        self.vocv_mv = self.calculate_ocv()

        # measure ibatt_mA
        self.ibatt_mA = self.batsimHw.measure_ibatt_ma()

        # calculate vbatt voltage
        self.vr_mv = self.vocv_mv - self.ibatt_mA * self.r_mohms / 1000

        # Calculate vbatt
        if not self.rc_enabled:
            # No drop over RC circuits
            self.vr1c1_mv = 0
            self.vr2c2_mv = 0

        else:
            # calculate drop over R1 C1 circuit
            self.vr1c1_mv = calculate_rc_voltage(current_time - self.rc_calculation_start_time, self.vr1c1_prev_mv,
                                                 self.vr_mv, self.ibatt_mA, self.r1_mohms, self.c1_F)

            # calculate drop over R2 C2 circuit
            self.vr2c2_mv = calculate_rc_voltage(current_time - self.rc_calculation_start_time, self.vr2c2_prev_mv,
                                                 self.vr_mv, self.ibatt_mA, self.r2_mohms, self.c2_F)

        self.vbatt_mv = self.vr_mv - self.vr1c1_mv - self.vr2c2_mv

        self.batsimHw.set_vbatt_mv(self.vbatt_mv)

        self.log.log_batsim_data(self.vocv_mv, self.vbatt_mv, self.ibatt_mA, self.vr_mv, self.vr1c1_mv, self.vr2c2_mv,
                                  self.current_battery_capacity_mas / 3600, self.battery_capacity_percent)

        self.ui.update_batsim_data(current_time - self.rc_calculation_start_time, self.vocv_mv, self.vbatt_mv,
                                    self.ibatt_mA, self.vr_mv, self.vr1c1_mv,
                                    self.vr2c2_mv, self.current_battery_capacity_mas / 3600,
                                    self.battery_capacity_percent)

        # Update the last time
        self.last_time = current_time
        self.vr1c1_prev_mv = self.vr1c1_mv
        self.vr2c2_prev_mv = self.vr2c2_mv

        if self.current_battery_capacity_mas == 0:
            self.stop()

    def start(self):
        if self.current_battery_capacity_mas > 0:
            self.last_update_time = time.perf_counter()
            self.rc_calculation_start_time = self.last_update_time
            self.timer.start()

    def stop(self):
        self.last_update_time = 0
        self.timer.stop()
