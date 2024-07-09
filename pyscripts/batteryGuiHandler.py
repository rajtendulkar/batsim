
import math

from PyQt6.QtCore import QTimer
from battery_simulator import Ui_MainWindow
from PyQt6 import QtCore

from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis
from PyQt6.QtGui import QPainter, QColor
from PyQt6.QtCore import QPointF, QMargins, Qt
from batteryLogic import BatSimCore
from ToggleSwitch import ToggleSwitch


class BatSimGui(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.timer = QTimer()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.graph_update_timer_expired)

        self.ocv_chart_view = None
        self.batsim_core = BatSimCore(self)
        self.ui.battParamsPushButton.clicked.connect(self.batt_params_update_button_clicked)
        self.ui.battParamsCheckBox.stateChanged.connect(self.batt_params_enable_checkbox)
        # enable custom window hint
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.CustomizeWindowHint)
        # disable (but not hide) close button
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowMaximizeButtonHint)
        self.ui.battStatusProgressBar.setStyleSheet(
            """
            QProgressBar {
                border: 1px solid black;
                text-align: center;
                padding: 1px;
                border-bottom-right-radius: 7px;
                border-bottom-left-radius: 7px;
                background: QLinearGradient( x1: 0, y1: 0, x2: 1, y2: 0,
                stop: 0 #fff,
                stop: 0.4999 #eee,
                stop: 0.5 #ddd,
                stop: 1 #eee );
                width: 15px;   
            }

            QProgressBar::chunk {
                background: QLinearGradient( x1: 0, y1: 0, x2: 1, y2: 0,
                stop: 0 #78d,
                stop: 0.4999 #46a,
                stop: 0.5 #45a,
                stop: 1 #238 );
                border-bottom-right-radius: 7px;
                border-bottom-left-radius: 7px;
                border: 1px solid black;
            }
            """
        )

        self.batsim_toggle_switch = ToggleSwitch(parent=self)
        self.ui.verticalLayout.addWidget(self.batsim_toggle_switch)
        self.batsim_toggle_switch.statusChanged.connect(self.on_status_changed)

        # Data stored to display graphs
        self.time_data = []
        self.soc_change_data = []
        self.vocv_data = []

        self.draw_ocv_graph()
        self.draw_vocv_graph()
        self.draw_soc_change_graph()
        self.update_batsim_data(0, 0, 0, 0, 0, 0, 0, 0, 0)

    def external_load_control(self):
        if self.ui.externalLoadCheckBox.isEnabled():
            self.batsim_core.enable_external_load(self.ui.externalLoadDoubleSpinBox.value())
        else:
            self.batsim_core.enable_external_load(self.ui.externalLoadDoubleSpinBox.value())

    def graph_update_timer_expired(self):
        self.update_vocv_graph()
        self.update_soc_graph()

    def on_status_changed(self, status):
        print(f'Toggle switch status: {"On" if status else "Off"}')
        if self.batsim_toggle_switch.getstatus():
            print('Start Batsim')
            self.batsim_core.start()
            self.timer.start()
        else:
            print('Stop Batsim')
            self.batsim_core.stop()
            self.timer.stop()

            # Clear data stored to display graphs
            self.time_data = []
            self.soc_change_data = []
            self.vocv_data = []
            self.update_batsim_data(0, 0, 0, 0, 0, 0, 0, 0, 0)

    def update_batsim_data(self, time_delta_seconds, vocv_mv, vbatt_mv, ibat_ma, vr_mv, vr1c1_mv, vr2c2_mv, batt_cap_mah, batt_cap_percent):
        self.ui.vocvLineEdit.setText(str(f"{vocv_mv:.2f}"))
        self.ui.vbattLineEdit.setText(str(f"{vbatt_mv:.2f}"))
        self.ui.ibattLineEdit.setText(str(f"{ibat_ma:.2f}"))
        self.ui.vRLineEdit.setText(str(f"{vr_mv:.2f}"))
        self.ui.vR1c1LineEdit.setText(str(f"{vr1c1_mv:.2f}"))
        self.ui.vR2c2LineEdit.setText(str(f"{vr2c2_mv:.2f}"))
        self.ui.battCapPercentLineEdit.setText(str(f"{batt_cap_percent:.2f}"))
        self.ui.battCapMahLineEdit.setText(str(f"{batt_cap_mah:.2f}"))
        self.ui.battStatusProgressBar.setValue(math.floor(batt_cap_percent))

        self.time_data.append(time_delta_seconds)
        self.soc_change_data.append(batt_cap_percent)
        self.vocv_data.append(vocv_mv)

        # Let us plot only latest 50 data points.
        if len(self.time_data) == 50:
            self.time_data.pop(0)
            self.soc_change_data.pop(0)
            self.vocv_data.pop(0)

    def batt_params_enable_checkbox(self):
        if self.ui.battParamsCheckBox.checkState().value != 0:
            self.ui.r1DoubleSpinBox.setReadOnly(False)
            self.ui.r2DoubleSpinBox.setReadOnly(False)
            self.ui.c1DoubleSpinBox.setReadOnly(False)
            self.ui.c2DoubleSpinBox.setReadOnly(False)
        else:
            self.ui.r1DoubleSpinBox.setReadOnly(True)
            self.ui.r2DoubleSpinBox.setReadOnly(True)
            self.ui.c1DoubleSpinBox.setReadOnly(True)
            self.ui.c2DoubleSpinBox.setReadOnly(True)

    def draw_soc_change_graph(self):
        self.soc_change_chart = QChart()
        self.soc_change_chart.setTitle("")
        self.soc_change_series = QLineSeries()
        self.soc_change_series.setName("")

        self.soc_change_chart.setTheme(QChart.ChartTheme.ChartThemeDark)
        self.soc_change_chart.addSeries(self.soc_change_series)

        self.soc_change_chart.setMargins(QMargins(0, 0, 0, 0))
        self.soc_change_chart.layout().setContentsMargins(0, 0, 0, 0)
        self.soc_change_chart.legend().hide()

        self.socChartocv_axis_x = QValueAxis()
        self.socChartocv_axis_x.setRange(0, 10)
        self.socChartocv_axis_x.setLabelFormat("%d")
        self.socChartocv_axis_x.setTickCount(1)
        self.socChartocv_axis_x.setTitleText("Time (s)")

        self.socChartAxisY = QValueAxis()
        self.socChartAxisY.setRange(0, 100)
        self.socChartAxisY.setLabelFormat("%d")
        self.socChartAxisY.setTickCount(5)
        self.socChartAxisY.setTitleText("SoC (%)")

        self.soc_change_chart.addAxis(self.socChartocv_axis_x, QtCore.Qt.AlignmentFlag.AlignBottom)
        self.soc_change_chart.addAxis(self.socChartAxisY, QtCore.Qt.AlignmentFlag.AlignLeft)

        self.soc_change_chart_view = QChartView(self.soc_change_chart)
        self.soc_change_chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)

        self.ui.verticalLayout_4.addWidget(self.soc_change_chart_view)
        self.soc_change_chart_view.update()

    def draw_ocv_graph(self):
        self.ocv_graph = QChart()
        self.ocv_graph.setTitle("")
        self.ocv_graph_series = QLineSeries()
        self.ocv_graph_series.setName("")

        self.ocv_graph.setTheme(QChart.ChartTheme.ChartThemeDark)
        self.ocv_graph.addSeries(self.ocv_graph_series)

        self.ocv_graph.setMargins(QMargins(0, 0, 0, 0))
        self.ocv_graph.layout().setContentsMargins(0, 0, 0, 0)
        self.ocv_graph.legend().hide()

        ocv_axis_x = QValueAxis()
        ocv_axis_x.setRange(0, 100)
        ocv_axis_x.setLabelFormat("%d")
        ocv_axis_x.setTickCount(10)
        ocv_axis_x.setTitleText("State of Charge (%)")

        self.ocv_axis_y = QValueAxis()
        self.ocv_axis_y.setRange(0, 100)
        self.ocv_axis_y.setLabelFormat("%d")
        self.ocv_axis_y.setTickCount(8)
        self.ocv_axis_y.setTitleText("Vbatt (mV)")

        self.ocv_graph.addAxis(ocv_axis_x, QtCore.Qt.AlignmentFlag.AlignBottom)
        self.ocv_graph.addAxis(self.ocv_axis_y, QtCore.Qt.AlignmentFlag.AlignLeft)

        self.ocv_chart_view = QChartView(self.ocv_graph)
        self.ocv_chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)

        self.ui.verticalLayout_2.addWidget(self.ocv_chart_view)

    def draw_vocv_graph(self):
        self.vocv_graph = QChart()
        self.vocv_graph.setTitle("")
        self.vocv_graph_series = QLineSeries()
        self.vocv_graph_series.setName("")

        self.vocv_graph.setTheme(QChart.ChartTheme.ChartThemeDark)
        self.vocv_graph.addSeries(self.vocv_graph_series)

        self.vocv_graph.setMargins(QMargins(0, 0, 0, 0))
        self.vocv_graph.layout().setContentsMargins(0, 0, 0, 0)
        self.vocv_graph.legend().hide()

        self.vocvocv_axis_x = QValueAxis()
        self.vocvocv_axis_x.setRange(0, 100)
        self.vocvocv_axis_x.setLabelFormat("%d")
        self.vocvocv_axis_x.setTickCount(8)
        self.vocvocv_axis_x.setTitleText("Time (s)")

        self.vocv_axis_y = QValueAxis()
        self.vocv_axis_y.setRange(0, 100)
        self.vocv_axis_y.setLabelFormat("%d")
        self.vocv_axis_y.setTickCount(5)
        self.vocv_axis_y.setTitleText("Vocv (mV)")

        self.vocv_graph.addAxis(self.vocvocv_axis_x, QtCore.Qt.AlignmentFlag.AlignBottom)
        self.vocv_graph.addAxis(self.vocv_axis_y, QtCore.Qt.AlignmentFlag.AlignLeft)

        self.vocv_chart_view = QChartView(self.vocv_graph)
        self.vocv_chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)

        self.ui.verticalLayout_3.addWidget(self.vocv_chart_view)

    def update_vocv_graph(self):
        self.vocv_graph_series.clear()

        for i in range(len(self.time_data)):
            self.vocv_graph_series.append(QPointF(self.time_data[i], self.vocv_data[i]))

        self.vocvocv_axis_x.setRange(min(self.time_data), max(self.time_data))

        if len(self.vocv_data) > 1:
            min_ocv = sorted(self.vocv_data)[1]
        else:
            min_ocv = min(self.vocv_data)

        self.vocv_axis_y.setRange(min_ocv, max(self.vocv_data))
        self.vocv_graph.removeSeries(self.vocv_graph_series)
        self.vocv_graph.addSeries(self.vocv_graph_series)
        self.vocv_chart_view.update()

    def update_soc_graph(self):
        self.soc_change_series.clear()

        for i in range(len(self.time_data)):
            self.soc_change_series.append(QPointF(self.time_data[i], self.soc_change_data[i]))

        self.socChartocv_axis_x.setRange(min(self.time_data), max(self.time_data))
        self.socChartAxisY.setRange(min(self.soc_change_data), max(self.soc_change_data))
        self.soc_change_chart.removeSeries(self.soc_change_series)
        self.soc_change_chart.addSeries(self.soc_change_series)
        self.soc_change_chart_view.update()

    def update_ocv_graph(self, ocvTable):
        self.ocv_graph_series.clear()

        for i in range(len(ocvTable)):
            self.ocv_graph_series.append(QPointF(i, ocvTable[i]))

        self.ocv_axis_y.setRange(min(ocvTable), max(ocvTable))
        self.ocv_graph.removeSeries(self.ocv_graph_series)
        self.ocv_graph.addSeries(self.ocv_graph_series)
        self.ocv_chart_view.update()

    def parseOcvTable(self):
        ocv_input_str = self.ui.ocvTableTextEdit.toPlainText()
        ocv_list = ocv_input_str.split(',')
        if len(ocv_list) == 101:
            check_alpha = any(char.isdigit() for char in ocv_list)
            if check_alpha:
                ocvTable = list(map(int, ocv_list))
                self.update_ocv_graph(ocvTable)
                return ocvTable

        return []

    def batt_params_update_button_clicked(self):

        # Store R and C parameters
        rc_enabled = self.ui.battParamsCheckBox.checkState().value == 0
        r_mohms = self.ui.rDoubleSpinBox.value()
        r1_mohms = self.ui.r1DoubleSpinBox.value()
        r2_mohms = self.ui.r2DoubleSpinBox.value()
        c1_F = self.ui.c1DoubleSpinBox.value()
        c2_F = self.ui.c1DoubleSpinBox.value()
        ocv_table = self.parseOcvTable()
        battery_initial_capacity_percent = self.ui.battCapPercentSpinBox.value()
        battery_capacity_mAh = self.ui.battCapMahSpinBox.value()

        # Then Parse OCV-Table
        if len(ocv_table) == 0:
            red_color = QColor(255, 0, 0)
            self.ui.ocvTableTextEdit.setStyleSheet("QTextEdit { background-color: #FFFFFF; color: #FF0000; }")
        else:
            black_color = QColor(0, 0, 0)
            self.ui.ocvTableTextEdit.setStyleSheet("QTextEdit { background-color: #FFFFFF; color: #000000; }")

        self.batsim_core.update_rc_params(rc_enabled, r_mohms, r1_mohms, r2_mohms, c1_F, c2_F,
                                         battery_initial_capacity_percent, battery_capacity_mAh, ocv_table)

        self.ui.battStatusProgressBar.setValue(battery_initial_capacity_percent)


class BatSimGuiHandler:
    def __init__(self):
        self.app = QApplication([])
        self.gui = BatSimGui()

    def start(self):
        self.gui.show()
        self.app.exec()
