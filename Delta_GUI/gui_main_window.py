import sys
import cv2
import serial.tools.list_ports
import numpy as np
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QComboBox, QGroupBox, 
                             QGridLayout, QDoubleSpinBox, QStatusBar, QMessageBox,
                             QSlider, QTabWidget)
from PyQt5.QtCore import Qt, pyqtSlot, QTimer, QMutex
from PyQt5.QtGui import QPixmap, QImage

from acrome.controller import Delta
from delta_robot import AcromeDelta
from camera_thread import CameraThread, CameraEnumerator
from conveyor_thread import ConveyorThread
from demo_thread import DemoThread
from custom_widgets import XYPadWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Acrome Delta Robot Control GUI")
        self.resize(1100, 750)

        self.robot = AcromeDelta()
        self.dev = None  
        self.dev_mutex = QMutex() 

        self.camera_thread = None
        self.conveyor_thread = None
        self.demo_thread = None

        self.telemetry_timer = QTimer(self)
        self.telemetry_timer.timeout.connect(self.telemetry_tick)
        
        self.in_telemetry_update = False

        self.init_ui()
        
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # --------- LEFT COLUMN ---------
        left_column = QVBoxLayout()
        
        # 1. Connection Group
        conn_group = QGroupBox("Bağlantı Ayarları")
        conn_layout = QGridLayout()
        
        self.port_combo = QComboBox()
        self.refresh_ports()
        btn_refresh_ports = QPushButton("Yenile")
        btn_refresh_ports.clicked.connect(self.refresh_ports)
        
        self.btn_connect = QPushButton("Bağlan")
        self.btn_connect.clicked.connect(self.toggle_connection)
        
        conn_layout.addWidget(QLabel("COM Port:"), 0, 0)
        conn_layout.addWidget(self.port_combo, 0, 1)
        conn_layout.addWidget(btn_refresh_ports, 0, 2)
        conn_layout.addWidget(self.btn_connect, 1, 0, 1, 3)
        conn_group.setLayout(conn_layout)
        left_column.addWidget(conn_group)

        # 2. Camera Group
        cam_group = QGroupBox("Kamera Ayarları")
        cam_layout = QGridLayout()
        
        self.cam_combo = QComboBox()
        self.refresh_cameras()
        btn_refresh_cam = QPushButton("Yenile")
        btn_refresh_cam.clicked.connect(self.refresh_cameras)
        
        self.btn_cam_toggle = QPushButton("Kamerayı Başlat")
        self.btn_cam_toggle.clicked.connect(self.toggle_camera)
        
        cam_layout.addWidget(QLabel("Kamera:"), 0, 0)
        cam_layout.addWidget(self.cam_combo, 0, 1)
        cam_layout.addWidget(btn_refresh_cam, 0, 2)
        cam_layout.addWidget(self.btn_cam_toggle, 1, 0, 1, 3)
        cam_group.setLayout(cam_layout)
        left_column.addWidget(cam_group)

        # 3. Control Modes (Tabs)
        self.mode_tabs = QTabWidget()
        self.mode_tabs.currentChanged.connect(self.on_tab_changed)
        
        # TAB: MANUEL
        self.tab_manual = QWidget()
        man_layout = QVBoxLayout(self.tab_manual)
        
        ik_layout = QHBoxLayout()
        self.spin_x = QDoubleSpinBox()
        self.spin_y = QDoubleSpinBox()
        self.spin_z = QDoubleSpinBox()
        
        for spin, initial in zip([self.spin_x, self.spin_y, self.spin_z], [0, 0, -180]):
            spin.setRange(-400, 400)
            spin.setValue(initial)
            spin.valueChanged.connect(self.on_spin_changed)
            
        ik_layout.addWidget(QLabel("X:"))
        ik_layout.addWidget(self.spin_x)
        ik_layout.addWidget(QLabel("Y:"))
        ik_layout.addWidget(self.spin_y)
        ik_layout.addWidget(QLabel("Z:"))
        ik_layout.addWidget(self.spin_z)
        man_layout.addLayout(ik_layout)
        
        widgets_layout = QHBoxLayout()
        self.xy_pad = XYPadWidget(x_min=-100.0, x_max=100.0, y_min=-100.0, y_max=100.0)
        self.xy_pad.positionChanged.connect(self.on_xypad_changed)
        widgets_layout.addWidget(self.xy_pad, alignment=Qt.AlignCenter)
        
        self.z_slider = QSlider(Qt.Vertical)
        self.z_slider.setRange(-250, -50)
        self.z_slider.setValue(-180)
        self.z_slider.setMinimumHeight(200)
        self.z_slider.valueChanged.connect(self.on_zslider_changed)
        widgets_layout.addWidget(self.z_slider, alignment=Qt.AlignCenter)
        man_layout.addLayout(widgets_layout)

        self.btn_enable = QPushButton("Hareket İzni (Enable): KAPALI")
        self.btn_enable.setCheckable(True)
        self.btn_enable.setStyleSheet("background-color: #f38ba8; color: #11111b; font-weight: bold; padding: 5px;")
        self.btn_enable.clicked.connect(self.toggle_motion_enable)
        man_layout.addWidget(self.btn_enable)

        self.btn_magnet = QPushButton("Mıknatıs AÇ")
        self.btn_magnet.setCheckable(True)
        self.btn_magnet.setStyleSheet("padding: 5px;")
        self.btn_magnet.clicked.connect(self.toggle_magnet)
        man_layout.addWidget(self.btn_magnet)
        man_layout.addStretch()

        # TAB: DEMO
        self.tab_demo = QWidget()
        demo_layout = QVBoxLayout(self.tab_demo)
        
        # Circle Section
        circle_group = QGroupBox("Çember Çizimi")
        circle_layout = QHBoxLayout()
        
        lbl_circle_icon = QLabel()
        lbl_circle_icon.setFixedSize(50, 50)
        lbl_circle_icon.setStyleSheet("background-color: transparent; border: 3px solid #89b4fa; border-radius: 25px;")
        circle_layout.addWidget(lbl_circle_icon)
        
        circle_options = QGridLayout()
        self.spin_circle_x = QDoubleSpinBox()
        self.spin_circle_y = QDoubleSpinBox()
        self.spin_circle_z = QDoubleSpinBox()
        self.spin_circle_r = QDoubleSpinBox()
        
        for spin, val in zip([self.spin_circle_x, self.spin_circle_y, self.spin_circle_z, self.spin_circle_r], [0, 0, -180, 50]):
            if spin != self.spin_circle_r: spin.setRange(-300, 300)
            else: spin.setRange(10, 200)
            spin.setValue(val)
            
        circle_options.addWidget(QLabel("X:"), 0, 0)
        circle_options.addWidget(self.spin_circle_x, 0, 1)
        circle_options.addWidget(QLabel("Y:"), 0, 2)
        circle_options.addWidget(self.spin_circle_y, 0, 3)
        circle_options.addWidget(QLabel("Z:"), 1, 0)
        circle_options.addWidget(self.spin_circle_z, 1, 1)
        circle_options.addWidget(QLabel("Yarıçap:"), 1, 2)
        circle_options.addWidget(self.spin_circle_r, 1, 3)
        circle_layout.addLayout(circle_options)
        
        self.btn_demo_circle = QPushButton("Çember Çiz")
        self.btn_demo_circle.setCheckable(True)
        self.btn_demo_circle.setMinimumHeight(50)
        self.btn_demo_circle.clicked.connect(self.toggle_demo_circle)
        circle_layout.addWidget(self.btn_demo_circle)
        circle_group.setLayout(circle_layout)
        demo_layout.addWidget(circle_group)

        # Square Section
        square_group = QGroupBox("Kare Çizimi")
        square_layout = QHBoxLayout()
        
        lbl_square_icon = QLabel()
        lbl_square_icon.setFixedSize(50, 50)
        lbl_square_icon.setStyleSheet("background-color: transparent; border: 3px solid #f9e2af;")
        square_layout.addWidget(lbl_square_icon)
        
        square_options = QGridLayout()
        self.spin_square_x = QDoubleSpinBox()
        self.spin_square_y = QDoubleSpinBox()
        self.spin_square_z = QDoubleSpinBox()
        self.spin_square_r = QDoubleSpinBox()
        
        for spin, val in zip([self.spin_square_x, self.spin_square_y, self.spin_square_z, self.spin_square_r], [0, 0, -180, 50]):
            if spin != self.spin_square_r: spin.setRange(-300, 300)
            else: spin.setRange(10, 200)
            spin.setValue(val)
            
        square_options.addWidget(QLabel("X:"), 0, 0)
        square_options.addWidget(self.spin_square_x, 0, 1)
        square_options.addWidget(QLabel("Y:"), 0, 2)
        square_options.addWidget(self.spin_square_y, 0, 3)
        square_options.addWidget(QLabel("Z:"), 1, 0)
        square_options.addWidget(self.spin_square_z, 1, 1)
        square_options.addWidget(QLabel("Kenar/2:"), 1, 2)
        square_options.addWidget(self.spin_square_r, 1, 3)
        square_layout.addLayout(square_options)
        
        self.btn_demo_square = QPushButton("Kare Çiz")
        self.btn_demo_square.setCheckable(True)
        self.btn_demo_square.setMinimumHeight(50)
        self.btn_demo_square.clicked.connect(self.toggle_demo_square)
        square_layout.addWidget(self.btn_demo_square)
        square_group.setLayout(square_layout)
        demo_layout.addWidget(square_group)
        
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("Hareket Hızı:"))
        self.slider_speed = QSlider(Qt.Horizontal)
        self.slider_speed.setRange(10, 200)
        self.slider_speed.setValue(100)
        self.slider_speed.valueChanged.connect(self.update_demo_speed)
        self.lbl_speed_val = QLabel("1.00x")
        self.lbl_speed_val.setMinimumWidth(40)
        speed_layout.addWidget(self.slider_speed)
        speed_layout.addWidget(self.lbl_speed_val)
        demo_layout.addLayout(speed_layout)
        demo_layout.addStretch()

        # TAB: CONVEYOR
        self.tab_conveyor = QWidget()
        conv_layout = QVBoxLayout(self.tab_conveyor)
        
        conv_settings = QHBoxLayout()
        self.spin_conv_z = QDoubleSpinBox()
        self.spin_conv_z.setRange(-250, -100)
        self.spin_conv_z.setValue(-206)
        
        conv_settings.addWidget(QLabel("Z Alma Sınırı (mm):"))
        conv_settings.addWidget(self.spin_conv_z)
        conv_layout.addLayout(conv_settings)
        
        self.btn_conveyor = QPushButton("Conveyor Modu: KAPALI")
        self.btn_conveyor.setCheckable(True)
        self.btn_conveyor.setStyleSheet("background-color: #f38ba8; color: #11111b; font-weight: bold; padding: 10px;")
        self.btn_conveyor.clicked.connect(self.toggle_conveyor)
        conv_layout.addWidget(self.btn_conveyor)
        conv_layout.addStretch()

        self.mode_tabs.addTab(self.tab_manual, "Manuel Kontrol")
        self.mode_tabs.addTab(self.tab_demo, "Demo Hareketler")
        self.mode_tabs.addTab(self.tab_conveyor, "Conveyor Modu")
        left_column.addWidget(self.mode_tabs)

        # --------- RIGHT COLUMN ---------
        right_column = QVBoxLayout()
        
        cam_view_group = QGroupBox("Kamera Vizörü")
        cam_view_layout = QVBoxLayout()
        self.lbl_camera_view = QLabel("Kamera Görüntüsü Yok")
        self.lbl_camera_view.setAlignment(Qt.AlignCenter)
        self.lbl_camera_view.setStyleSheet("background-color: black; color: white; min-width: 640px; min-height: 480px;")
        cam_view_layout.addWidget(self.lbl_camera_view)
        cam_view_group.setLayout(cam_view_layout)
        right_column.addWidget(cam_view_group, stretch=1)
        
        # Telemetry Bar (Horizontal minimal)
        telemetry_group = QGroupBox("Cihaz Telemetrisi")
        telemetry_group.setMaximumHeight(80)
        tele_layout = QHBoxLayout()
        
        self.lbl_tel_mot_1 = QLabel("0")
        self.lbl_tel_mot_2 = QLabel("0")
        self.lbl_tel_mot_3 = QLabel("0")
        self.lbl_tel_x = QLabel("0.0 mm")
        self.lbl_tel_y = QLabel("0.0 mm")
        self.lbl_tel_z = QLabel("0.0 mm")
        
        tele_layout.addWidget(QLabel("<b>M1:</b>"))
        tele_layout.addWidget(self.lbl_tel_mot_1)
        tele_layout.addWidget(QLabel("<b>M2:</b>"))
        tele_layout.addWidget(self.lbl_tel_mot_2)
        tele_layout.addWidget(QLabel("<b>M3:</b>"))
        tele_layout.addWidget(self.lbl_tel_mot_3)
        
        tele_layout.addSpacing(20)
        tele_layout.addWidget(QLabel("<b>X:</b>"))
        tele_layout.addWidget(self.lbl_tel_x)
        tele_layout.addWidget(QLabel("<b>Y:</b>"))
        tele_layout.addWidget(self.lbl_tel_y)
        tele_layout.addWidget(QLabel("<b>Z:</b>"))
        tele_layout.addWidget(self.lbl_tel_z)
        
        telemetry_group.setLayout(tele_layout)
        right_column.addWidget(telemetry_group)

        # Main Layout Assembly
        main_layout.addLayout(left_column, stretch=1)
        main_layout.addLayout(right_column, stretch=2)

        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Hazır")
        
        self.update_control_states()

    def on_tab_changed(self, index):
        # Stop Demo Mode
        if self.demo_thread and self.demo_thread.isRunning():
            self.stop_demo()
            self.btn_demo_circle.setChecked(False)
            self.btn_demo_square.setChecked(False)
            self.btn_demo_circle.setText("Çember Çiz")
            self.btn_demo_square.setText("Kare Çiz")
            self.btn_demo_circle.setEnabled(True)
            self.btn_demo_square.setEnabled(True)
            
        # Stop Conveyor Mode
        if self.conveyor_thread and self.conveyor_thread.isRunning():
            self.btn_conveyor.setChecked(False)
            self.toggle_conveyor(False)
            
        self.update_control_states()

    def refresh_ports(self):
        self.port_combo.clear()
        ports = list(serial.tools.list_ports.comports())
        for p in sorted(ports):
            self.port_combo.addItem(f"{p.device} - {p.description}", p.device)

    def refresh_cameras(self):
        self.cam_combo.clear()
        cams = CameraEnumerator.list_cameras()
        if not cams:
            self.cam_combo.addItem("Kamera Bulunamadı")
            self.cam_combo.setEnabled(False)
        else:
            self.cam_combo.setEnabled(True)
            for cid, cname in cams:
                self.cam_combo.addItem(f"{cname}", cid)

    def toggle_connection(self):
        if self.dev is None:
            port = self.port_combo.currentData()
            if not port:
                QMessageBox.warning(self, "Hata", "Lütfen geçerli bir port seçin.")
                return
            try:
                self.dev = Delta(port)
                try:
                    theta = self.robot.inverse_kin(self.spin_x.value(), self.spin_y.value(), self.spin_z.value())
                    pos = self.robot.angle_to_pos(theta)
                    self.dev.set_motors(np.int_(pos))
                except:
                    pass

                self.btn_connect.setText("Bağlantıyı Kes")
                self.btn_connect.setStyleSheet("background-color: #a6e3a1; color: #11111b;")
                self.statusBar.showMessage(f"Bağlandı: {port}")
                self.telemetry_timer.start(10) 
            except Exception as e:
                QMessageBox.critical(self, "Bağlantı Hatası", f"Robota bağlanılamadı:\n{str(e)}")
        else:
            self.telemetry_timer.stop()
            self.dev_mutex.lock()
            self.dev = None  
            self.dev_mutex.unlock()
            self.btn_connect.setText("Bağlan")
            self.btn_connect.setStyleSheet("")
            self.statusBar.showMessage("Bağlantı kesildi.")
            
        self.update_control_states()

    def toggle_camera(self):
        if self.camera_thread is None or not self.camera_thread.isRunning():
            cam_idx = self.cam_combo.currentData()
            if cam_idx is None: return
            
            self.camera_thread = CameraThread(camera_index=cam_idx)
            self.camera_thread.frame_ready.connect(self.update_gui_image)
            
            if self.conveyor_thread and self.conveyor_thread.isRunning():
                self.camera_thread.raw_frame_ready.connect(self.conveyor_thread.set_frame)
            
            self.camera_thread.start()
            self.btn_cam_toggle.setText("Kamerayı Durdur")
            self.cam_combo.setEnabled(False)
        else:
            self.camera_thread.stop()
            self.camera_thread = None
            self.btn_cam_toggle.setText("Kamerayı Başlat")
            self.cam_combo.setEnabled(True)
            self.lbl_camera_view.clear()
            self.lbl_camera_view.setText("Kamera Görüntüsü Yok")

    @pyqtSlot(QImage)
    def update_gui_image(self, q_img):
        if not self.btn_conveyor.isChecked():
            pixmap = QPixmap.fromImage(q_img)
            self.lbl_camera_view.setPixmap(pixmap)

    @pyqtSlot(np.ndarray)
    def update_annotated_image(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        bytes_per_line = ch * w
        q_img = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_img)
        self.lbl_camera_view.setPixmap(pixmap)

    def toggle_conveyor(self, checked):
        if checked:
            if self.dev is None:
                QMessageBox.warning(self, "Uyarı", "Lütfen önce robota bağlanın.")
                self.btn_conveyor.setChecked(False)
                return
                
            if self.camera_thread is None or not self.camera_thread.isRunning():
                QMessageBox.warning(self, "Uyarı", "Lütfen önce kamerayı başlatın.")
                self.btn_conveyor.setChecked(False)
                return

            self.btn_conveyor.setText("Conveyor Modu: AÇIK")
            self.btn_conveyor.setStyleSheet("background-color: #a6e3a1; color: #11111b; font-weight: bold; padding: 10px;")
            
            z_limit = self.spin_conv_z.value()
            self.conveyor_thread = ConveyorThread(self.robot, self.dev, self.dev_mutex, z_limit)
            self.conveyor_thread.status_msg.connect(self.statusBar.showMessage)
            self.conveyor_thread.processed_frame.connect(self.update_annotated_image)
            
            if self.camera_thread:
                self.camera_thread.raw_frame_ready.connect(self.conveyor_thread.set_frame)
                
            self.conveyor_thread.start()
        else:
            self.btn_conveyor.setText("Conveyor Modu: KAPALI")
            self.btn_conveyor.setStyleSheet("background-color: #f38ba8; color: #11111b; font-weight: bold; padding: 10px;")
            
            if self.conveyor_thread:
                if self.camera_thread:
                    try:
                        self.camera_thread.raw_frame_ready.disconnect(self.conveyor_thread.set_frame)
                    except:
                        pass
                self.conveyor_thread.stop()
                self.conveyor_thread = None
                self.statusBar.showMessage("Conveyor durduruldu.")
                
        self.update_control_states()

    def update_control_states(self):
        is_connected = self.dev is not None
        self.tab_manual.setEnabled(is_connected)
        self.tab_demo.setEnabled(is_connected)
        self.tab_conveyor.setEnabled(is_connected)

    def telemetry_tick(self):
        if self.dev is None: return
        try:
            self.dev_mutex.lock()
            self.dev.update()
            motor_pos = self.dev.position
            self.dev_mutex.unlock()
            
            if len(motor_pos) >= 3:
                m1, m2, m3 = motor_pos[0], motor_pos[1], motor_pos[2]
                self.lbl_tel_mot_1.setText(f"{m1}")
                self.lbl_tel_mot_2.setText(f"{m2}")
                self.lbl_tel_mot_3.setText(f"{m3}")
                
                t1 = self.robot.pos_to_angle(m1)
                t2 = self.robot.pos_to_angle(m2)
                t3 = self.robot.pos_to_angle(m3)
                x, y, z = self.robot.forward_kin(t1, t2, t3)
                
                self.lbl_tel_x.setText(f"{x:.1f}")
                self.lbl_tel_y.setText(f"{y:.1f}")
                self.lbl_tel_z.setText(f"{z:.1f}")

                is_dragging = self.xy_pad.is_dragging or self.z_slider.isSliderDown()
                if not is_dragging and not self.in_telemetry_update and not (self.btn_conveyor.isChecked() or (self.demo_thread and self.demo_thread.isRunning())):
                    self.in_telemetry_update = True
                    self.spin_x.setValue(x)
                    self.spin_y.setValue(y)
                    self.spin_z.setValue(z)
                    self.xy_pad.set_position(x, y)
                    self.z_slider.setValue(int(z))
                    self.in_telemetry_update = False
        except:
            pass

    def on_spin_changed(self):
        if self.in_telemetry_update: return
        x = self.spin_x.value()
        y = self.spin_y.value()
        z = self.spin_z.value()
        
        self.in_telemetry_update = True
        self.xy_pad.set_position(x, y)
        self.z_slider.setValue(int(z))
        self.in_telemetry_update = False
        self.go_to_position(x, y, z)

    def on_xypad_changed(self, x, y):
        if self.in_telemetry_update: return
        self.in_telemetry_update = True
        self.spin_x.setValue(x)
        self.spin_y.setValue(y)
        self.in_telemetry_update = False
        self.go_to_position(x, y, self.spin_z.value())

    def on_zslider_changed(self, z):
        if self.in_telemetry_update: return
        self.in_telemetry_update = True
        self.spin_z.setValue(z)
        self.in_telemetry_update = False
        self.go_to_position(self.spin_x.value(), self.spin_y.value(), float(z))

    def go_to_position(self, x, y, z):
        if self.dev is None: return
        if self.btn_conveyor.isChecked() or (self.demo_thread and self.demo_thread.isRunning()): return
        if not self.btn_enable.isChecked(): return
            
        try:
            theta = self.robot.inverse_kin(x, y, z)
            pos = self.robot.angle_to_pos(theta)
            self.dev_mutex.lock()
            self.dev.set_motors(np.int_(pos))
            self.dev_mutex.unlock()
        except:
            pass

    def toggle_motion_enable(self, checked):
        if checked:
            self.btn_enable.setText("Hareket İzni (Enable): AÇIK")
            self.btn_enable.setStyleSheet("background-color: #a6e3a1; color: #11111b; font-weight: bold; padding: 5px;")
            self.go_to_position(self.spin_x.value(), self.spin_y.value(), self.spin_z.value())
        else:
            self.btn_enable.setText("Hareket İzni (Enable): KAPALI")
            self.btn_enable.setStyleSheet("background-color: #f38ba8; color: #11111b; font-weight: bold; padding: 5px;")

    def toggle_magnet(self, checked):
        if self.dev:
            self.dev.pick(checked)
            self.btn_magnet.setText("Mıknatıs KAPAT" if checked else "Mıknatıs AÇ")

    def toggle_demo_circle(self, checked):
        if checked:
            self.btn_demo_square.setChecked(False)
            self.stop_demo()
            self.start_demo(DemoThread.MODE_CIRCLE)
            self.btn_demo_circle.setText("Durdur")
            self.btn_demo_square.setEnabled(False)
        else:
            self.stop_demo()
            self.btn_demo_circle.setText("Çember Çiz")
            self.btn_demo_square.setEnabled(True)

    def toggle_demo_square(self, checked):
        if checked:
            self.btn_demo_circle.setChecked(False)
            self.stop_demo()
            self.start_demo(DemoThread.MODE_SQUARE)
            self.btn_demo_square.setText("Durdur")
            self.btn_demo_circle.setEnabled(False)
        else:
            self.stop_demo()
            self.btn_demo_square.setText("Kare Çiz")
            self.btn_demo_circle.setEnabled(True)

    def update_demo_speed(self, val):
        factor = val / 100.0
        self.lbl_speed_val.setText(f"{factor:.2f}x")
        if self.demo_thread and self.demo_thread.isRunning():
            self.demo_thread.set_speed(factor)

    def start_demo(self, mode):
        if mode == DemoThread.MODE_CIRCLE:
            cx = self.spin_circle_x.value()
            cy = self.spin_circle_y.value()
            cz = self.spin_circle_z.value()
            r = self.spin_circle_r.value()
        else:
            cx = self.spin_square_x.value()
            cy = self.spin_square_y.value()
            cz = self.spin_square_z.value()
            r = self.spin_square_r.value()
            
        self.demo_thread = DemoThread(self.robot, self.dev, self.dev_mutex, mode, cx, cy, cz, r)
        self.demo_thread.status_msg.connect(self.statusBar.showMessage)
        self.demo_thread.set_speed(self.slider_speed.value() / 100.0)
        self.demo_thread.start()

    def stop_demo(self):
        if self.demo_thread:
            self.demo_thread.stop()
            self.demo_thread = None
            self.statusBar.showMessage("Demo durduruldu.")

    def closeEvent(self, event):
        if self.conveyor_thread: self.conveyor_thread.stop()
        if self.camera_thread: self.camera_thread.stop()
        if self.demo_thread: self.demo_thread.stop()
        event.accept()
