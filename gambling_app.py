from PyQt5.QtCore import QSize, QRect, QPropertyAnimation, QTimeLine, QTimer, QThread, QEventLoop
from PyQt5.QtGui import QIcon, QPixmap, QTransform, QFont, QCursor
import functools
from time import sleep
import random
from random import randint
import threading
import os

from PyQt5.QtWidgets import QSlider, QTableWidgetItem, QGraphicsOpacityEffect
import requests

import mainwindow
from mainwindow import Ui_MainWindow
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt

import time
import os
import json
import socket


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent=parent)
        self.setupUi(self)

        self.pre_setup()

        self.username = ''
        self.balance = 0.0
        self.logged_in = False

        # Socket Server Stuff
        # self.ip = str(socket.gethostname())
        self.ip = '104.237.133.98'
        self.port = 5000
        self.split_string = '[325][6ofs<f.f2'

        # Crash stuff
        self.data = {}
        self.crash_data = {'check': True}
        self.next_time_crash = 0
        self.crash_multiplier = 1.0
        self.crash_bet = 0
        self.cashed_out = False
        self.crash_rounds = []
        self.crash_amount_style = (False, 'color: (255, 200, 0);')
        self.did_10 = False
        self.last_round_time = 0

        self.close_threads = False

        self.url = 'http://104.237.133.98:8000/'
        # self.url = 'http://127.0.0.1:8000/'

    def crash_button_pressed(self):
        self.hide_everything()
        self.crash_frame.show()

    def send_message(self, msg):
        self.s.send(bytes(msg, 'utf-8'))

    def login_pressed(self):
        self.login_error_label.hide()
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.s.connect((self.ip, self.port))
            self.s.send(bytes(str(socket.gethostname()), 'utf-8'))
            if str(self.username_input.text()) == '':
                QTimer.singleShot(100, lambda: self.send_message('[]'))
            else:
                QTimer.singleShot(100, lambda: self.send_message(str(self.username_input.text())))

            print('sent')

            self.login_error_label.hide()
            self.logged_in = True
            self.username = str(self.username_input.text())
            self.header_name.setText(self.username + ' | $' + "{:.2f}".format(self.balance))
            self.header_frame.show()
            self.login_frame.hide()
            thread = threading.Thread(target=self.update_data)
            thread.start()
            thread = threading.Thread(target=self.update_gui_crash)
            thread.start()
            thread = threading.Thread(target=self.update_balance)
            thread.start()
            thread = threading.Thread(target=self.update_crash_players)
            thread.start()
        except:
            self.login_error_label.show()

    def update_data(self):
        msg = ''
        while not self.close_threads:
            try:
                new_msg = self.s.recv(1024).decode('utf-8')
                msg += new_msg
                while msg.count(self.split_string) > 1:
                    msg = msg[msg.find(self.split_string) + len(self.split_string):]
                    self.data = json.loads(msg[0: msg.find(self.split_string)])
                    msg = msg[msg.find(self.split_string):]
                # self.data = json.loads(msg)
            except:
                pass
        # while not self.close_threads:
        #     try:
        #         msg = self.s.recv(10000).decode('utf-8')
        #         self.data = json.loads(msg)
        #     except Exception as e:
        #         print(e)

    def update_balance(self):
        while not self.close_threads:
            if 'balance' in self.data:
                self.header_name.setText(self.data['username'] + ' | $' + "{:.2f}".format(self.data['balance']))
            else:
                self.header_name.setText(self.username)

    def crash_bet_button_pressed(self):
        try:
            bet = round(float(self.crash_bet_amount.text()), 2)
            if self.data['to_start'] > 0 and self.crash_bet == 0:
                if self.data['balance'] >= bet > 0:
                    self.s.send(bytes('$' + str(bet), 'utf-8'))
                    self.crash_bet = bet
                    self.crash_bet_label.setText("{:.2f}".format(bet))
                    self.crash_bet_amount.setText("{:.2f}".format(bet))
                    self.crash_bet_amount.hide()
                    self.crash_bet_label.show()
            elif self.crash_bet > 0 and self.data['crash_counter'] == 0 and socket.gethostname() in self.data['crash_players'] and self.data['crash_players'][socket.gethostname()]['cashout'] == 0:
                self.s.send(bytes('out', 'utf-8'))
            else:
                self.start_crash_error_timer()
        except Exception as e:
            print(e)

    def update_crash_players(self):
        while not self.close_threads:
            if 'crash_players' in self.data:
                final_label = ''
                for comp_name in self.data['crash_players']:
                    if self.data['crash_players'][comp_name]['cashout'] > 0:
                        final_label += self.data['crash_players'][comp_name]['username'] + ' ' + "{:.2f}".format(round(self.data['crash_players'][comp_name]['cashout'], 2)) + 'x $' + "{:.2f}".format(round(self.data['crash_players'][comp_name]['cashout'] * self.data['crash_players'][comp_name]['bet'], 2)) + '\n'
                    else:
                        final_label += self.data['crash_players'][comp_name]['username'] + '  $' + '{:.2f}'.format(round(self.data['crash_players'][comp_name]['bet'], 2)) + '\n'
                self.crash_players_label.setText(final_label)
            else:
                self.crash_players_label.setText('')

        # r = json.loads(requests.get(self.url + 'api/crash_players/').text)
        # if r['success'] and r['label'] != '':
        #     self.crash_players_label.setText(r['label'])
        # else:
        #     self.crash_players_label.setText('')

    def update_crash_amount_style(self):
        if self.crash_amount_style[0]:
            self.crash_amount.setStyleSheet(self.crash_amount_style[1])
            self.crash_amount_style = (False, self.crash_amount_style[1])
        if 'crash_players' in self.data and socket.gethostname() in self.data['crash_players'] and self.data['to_start'] == 0:
            if self.data['crash_players'][socket.gethostname()]['cashout'] > 0:
                self.crash_bet_button.setStyleSheet('background-color: rgb(0, 100, 0);\n'
                                                    'font-size: 12px;')
            else:
                self.crash_bet_button.setStyleSheet('background-color: rgb(0, 150, 0);\n'
                                                    'font-size: 12px;')
        else:
            self.crash_bet_button.setStyleSheet('background-color: rgb(60, 60, 60);\n'
                                                'font-size: 25px;')

    def start_crash_amount_style_timer(self):
        self.crash_amount_style_timer = QTimer()
        self.crash_amount_style_timer.timeout.connect(self.update_crash_amount_style)
        self.crash_amount_style_timer.setInterval(1)
        self.crash_amount_style_timer.start()

    def update_gui_crash(self):
        tm = time.time()
        while not self.close_threads:
            try:
                if time.time() > tm + 3:
                    print('ping')
                    tm = time.time()
                if 'crash' in self.data:
                    if self.data['to_start'] == 0:
                        self.crash_amount.setText(str("{:.2f}".format(self.data['crash'])) + 'x')
                        if socket.gethostname() in self.data['crash_players']:
                            bet = self.data['crash_players'][socket.gethostname()]['bet']
                            co = self.data['crash_players'][socket.gethostname()]['cashout']
                            multiplier = self.data['crash']
                            if co > 0:
                                self.crash_bet_button.setText('Cashed out\n$' + "{:.2f}".format(round(bet * co, 2)) + '\n(' + str(co) + 'x)')
                            else:
                                self.crash_bet_button.setText('Cash out\n(' + "{:.2f}".format(round(bet * multiplier, 2)) + ')')
                    else:
                        if self.data['to_start'] < 10:
                            self.did_10 = False
                        self.crash_amount.setText('Starting in ' + str(self.data['to_start']))
                    if self.data['crashed']:
                        self.crash_amount_style = (True, 'color: rgb(200, 0, 0);')
                        if time.time() > self.last_round_time + 5:
                            self.crash_rounds.append(self.data['crash'])
                            self.update_history()
                            self.last_round_time = time.time()
                    elif self.data['to_start'] == 10 and not self.did_10:
                        self.crash_amount_style = (True, 'color: rgb(255, 200, 0);')
                        self.crash_bet_amount.show()
                        self.crash_bet_label.hide()
                        self.crash_bet_button.setText('Bet')
                        self.crash_bet = 0.0
                        self.did_10 = True
                else:
                    pass
            except:
                print('crash gui error')
                pass

        # if not self.crash_data['check']:
        #     self.crash_amount.setStyleSheet('color: rgb(255, 200, 0);')
        #     if self.crash_data['running']:
        #         if time.time() >= self.next_time_crash:
        #             self.crash_multiplier += .01
        #             self.crash_multiplier = round(self.crash_multiplier, 2)
        #             amount_to_sleep = .02 / self.crash_multiplier * 10
        #             if not self.cashed_out and self.crash_bet > 0:
        #                 self.crash_bet_button.setText('Cashout \n' + str(round(self.crash_bet * self.crash_multiplier, 2)))
        #             self.next_time_crash = time.time() + amount_to_sleep
        #         if self.crash_multiplier >= self.crash_data['multiplier']:
        #             self.crash_amount.setText("{:.2f}".format(self.crash_data['multiplier']) + 'x')
        #             self.crash_amount.setStyleSheet('color: rgb(200, 0, 0);')
        #             self.crash_data['check'] = True
        #             self.crash_rounds.append(self.crash_multiplier)
        #             self.update_history()
        #             # self.crash_multiplier = 1.00
        #             # self.crash_bet = 0.0
        #         else:
        #             self.crash_amount.setText("{:.2f}".format(self.crash_multiplier) + 'x')
        #         # self.crash_amount.setText(str(self.crash_data['multiplier']) + 'x')
        #     else:
        #         time_left = int(round(self.crash_data['start_time'] - time.time(), 0))
        #         self.crash_amount.setText('Starting in ' + str(time_left))
        #         if self.crash_data['start_time'] - time.time() <= 0:
        #             self.crash_data['running'] = True
        #             if self.crash_bet > 0:
        #                 self.crash_bet_button.setText('Cashout \n' + str(self.crash_bet))
        #                 self.crash_bet_button.setStyleSheet('background-color: rgb(0, 150, 0);\n'
        #                                                     'font-size: 13px;')
        #         else:
        #             self.crash_bet_button.setText('Bet')
        #             self.crash_bet_button.setStyleSheet('background-color: rgb(60, 60, 60);\n'
        #                                                 'font-size: 25px;')

    def crash_error_hide(self):
        self.crash_bet_message.hide()
        self.crash_error_timer.stop()

    def start_crash_error_timer(self):
        self.crash_bet_message.show()
        self.crash_error_timer.stop()
        self.crash_error_timer.start(2500)

    def update_history(self):
        i = 1
        for multiplier in reversed(self.crash_rounds):
            if i == 1:
                if multiplier >= 2:
                    self.crash_history_1.setStyleSheet('color: rgb(0, 200, 0);\n'
                                                       'font-weight: bold;\n'
                                                       'font-size: 12px;')
                elif multiplier >= 10:
                    self.crash_history_1.setStyleSheet('color: rgb(200, 175, 0);\n'
                                                       'font-weight: bold;\n'
                                                       'font-size: 12px;')
                elif multiplier >= 50:
                    self.crash_history_1.setStyleSheet('color: rgb(175, 100, 0);\n'
                                                       'font-weight: bold;\n'
                                                       'font-size: 12px;')
                else:
                    self.crash_history_1.setStyleSheet('color: rgb(200, 0, 0);\n'
                                                       'font-weight: bold;\n'
                                                       'font-size: 12px;')
                self.crash_history_1.setText("{:.2f}".format(multiplier) + 'x')
            elif i == 2:
                if multiplier >= 2:
                    self.crash_history_2.setStyleSheet('color: rgb(0, 200, 0);\n'
                                                       'font-weight: bold;\n'
                                                       'font-size: 12px;')
                elif multiplier >= 10:
                    self.crash_history_2.setStyleSheet('color: rgb(200, 175, 0);\n'
                                                       'font-weight: bold;\n'
                                                       'font-size: 12px;')
                elif multiplier >= 50:
                    self.crash_history_2.setStyleSheet('color: rgb(175, 100, 0);\n'
                                                       'font-weight: bold;\n'
                                                       'font-size: 12px;')
                else:
                    self.crash_history_2.setStyleSheet('color: rgb(200, 0, 0);\n'
                                                       'font-weight: bold;\n'
                                                       'font-size: 12px;')
                self.crash_history_2.setText("{:.2f}".format(multiplier) + 'x')
            elif i == 3:
                if multiplier >= 2:
                    self.crash_history_3.setStyleSheet('color: rgb(0, 200, 0);\n'
                                                       'font-weight: bold;\n'
                                                       'font-size: 12px;')
                elif multiplier >= 10:
                    self.crash_history_3.setStyleSheet('color: rgb(200, 175, 0);\n'
                                                       'font-weight: bold;\n'
                                                       'font-size: 12px;')
                elif multiplier >= 50:
                    self.crash_history_3.setStyleSheet('color: rgb(175, 100, 0);\n'
                                                       'font-weight: bold;\n'
                                                       'font-size: 12px;')
                else:
                    self.crash_history_3.setStyleSheet('color: rgb(200, 0, 0);\n'
                                                       'font-weight: bold;\n'
                                                       'font-size: 12px;')
                self.crash_history_3.setText("{:.2f}".format(multiplier) + 'x')
            elif i == 4:
                if multiplier >= 2:
                    self.crash_history_4.setStyleSheet('color: rgb(0, 200, 0);\n'
                                                       'font-weight: bold;\n'
                                                       'font-size: 12px;')
                elif multiplier >= 10:
                    self.crash_history_4.setStyleSheet('color: rgb(200, 175, 0);\n'
                                                       'font-weight: bold;\n'
                                                       'font-size: 12px;')
                elif multiplier >= 50:
                    self.crash_history_4.setStyleSheet('color: rgb(175, 100, 0);\n'
                                                       'font-weight: bold;\n'
                                                       'font-size: 12px;')
                else:
                    self.crash_history_4.setStyleSheet('color: rgb(200, 0, 0);\n'
                                                       'font-weight: bold;\n'
                                                       'font-size: 12px;')
                self.crash_history_4.setText("{:.2f}".format(multiplier) + 'x')
            elif i == 5:
                if multiplier >= 2:
                    self.crash_history_5.setStyleSheet('color: rgb(0, 200, 0);\n'
                                                       'font-weight: bold;\n'
                                                       'font-size: 12px;')
                elif multiplier >= 10:
                    self.crash_history_5.setStyleSheet('color: rgb(200, 175, 0);\n'
                                                       'font-weight: bold;\n'
                                                       'font-size: 12px;')
                elif multiplier >= 50:
                    self.crash_history_5.setStyleSheet('color: rgb(175, 100, 0);\n'
                                                       'font-weight: bold;\n'
                                                       'font-size: 12px;')
                else:
                    self.crash_history_5.setStyleSheet('color: rgb(200, 0, 0);\n'
                                                       'font-weight: bold;\n'
                                                       'font-size: 12px;')
                self.crash_history_5.setText("{:.2f}".format(multiplier) + 'x')
            else:
                break
            i += 1

    def pre_setup(self):
        self.setFont(QFont('Roboto'))
        self.login_button.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
        self.crash_button.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
        self.crash_bet_button.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
        self.crash_amount.setText('1.00x')
        self.header_frame.hide()
        self.crash_bet_message.hide()
        self.crash_history_1.setText('')
        self.crash_history_2.setText('')
        self.crash_history_3.setText('')
        self.crash_history_4.setText('')
        self.crash_history_5.setText('')

        self.crash_error_timer = QTimer()
        self.crash_error_timer.timeout.connect(self.crash_error_hide)
        self.crash_error_timer.setInterval(4000)

        self.start_crash_amount_style_timer()

        # Hide everything
        self.hide_everything()

        # Show Login
        self.show_login()

        # Buttons
        self.login_button.clicked.connect(self.login_pressed)
        self.crash_button.clicked.connect(self.crash_button_pressed)
        self.crash_bet_button.clicked.connect(self.crash_bet_button_pressed)

    def show_login(self):
        self.login_error_label.hide()
        self.login_frame.show()

    def hide_everything(self):
        self.login_frame.hide()
        self.crash_frame.hide()

    def closeEvent(self, *args, **kwargs):
        super(MainWindow, self).closeEvent(*args, **kwargs)
        self.close_threads = True


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    with open('ui/style.css', 'r+') as style:
        app.setStyleSheet(style.read())
    w = MainWindow()
    w.show()
    # w.close_threads = True
    sys.exit(app.exec_())




































