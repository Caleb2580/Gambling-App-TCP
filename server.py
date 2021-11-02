import socket
import threading
import json
import random
import time
from time import sleep


class GamblingServer:
    def __init__(self, ip, port):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.bind((ip, port))

        self.s.listen(20)
        self.data_file_path = 'data.json'

        self.split_string = '[325][6ofs<f.f2'

        try:
            self.server_data = json.loads(open(self.data_file_path, 'r+').read())
        except FileNotFoundError:
            self.server_data = {'players': {},
                                'crash': {'crash_multiplier': self.get_crash(), 'multiplier': 1.00, 'crash_counter': 0, 'to_start': 10, 'players': {}},
                                }
            self.save_server_data()

        self.connections = {}  #'session_id': {'connection': c, 'computer_name': computer_name}

        thread = threading.Thread(target=self.play_crash)
        thread.start()

        thread = threading.Thread(target=self.send_data)
        thread.start()

        # thread = threading.Thread(target=self.deposit)
        # thread.start()

        while True:
            c, a = self.s.accept()
            try:
                comp_name = str(c.recv(100).decode('utf-8'))
                username = str(c.recv(100).decode('utf-8'))
                self.connections[str(a[1])] = {'connection': c, 'computer_name': comp_name}
                if comp_name not in self.server_data['players']:
                    self.server_data['players'][comp_name] = {'balance': 0.0, 'username': username}
                elif '[]' != username != self.server_data['players'][comp_name]['username']:
                    self.server_data['players'][comp_name]['username'] = username
                print('Connected to ' + f"{self.server_data['players'][comp_name]['username']}({comp_name})")
                thread = threading.Thread(target=self.handle_messages, args=(comp_name, c,))
                thread.start()
            except:
                try:
                    self.connections.pop(str(a[1]))
                    c.close()
                except:
                    pass

    def deposit(self):
        while True:
            for p in self.server_data['players']:
                self.server_data['players'][p]['balance'] += .01
            sleep(1)

    def save_server_data(self):
        f = open(self.data_file_path, 'w+')
        try:
            f.write(json.dumps(self.server_data))
        except:
            pass
        finally:
            f.close()

    def get_crash(self):
        x = random.uniform(0, 1)
        multiplier = .99 / (1 - x)
        if multiplier < 1.0:
            return 1.0
        return round(multiplier, 2)

    def play_crash(self):
        while True:
            crash = self.server_data['crash']
            if crash['crash_counter'] == 0 and crash['multiplier'] < crash['crash_multiplier'] and crash['to_start'] == 0:
                crash['multiplier'] += .01
                self.server_data['crash']['multiplier'] = round(crash['multiplier'], 2)
                if self.server_data['crash']['multiplier'] < 10:
                    sleep(.02 / self.server_data['crash']['multiplier'] * 10)
                elif self.server_data['crash']['multiplier'] < 50:
                    sleep(.02 / self.server_data['crash']['multiplier'] * 20)
                elif self.server_data['crash']['multiplier'] < 100:
                    sleep(.02 / self.server_data['crash']['multiplier'] * 30)
            elif crash['crash_counter'] == 0 and crash['multiplier'] == crash['crash_multiplier'] and crash['to_start'] == 0:
                self.server_data['crash']['crash_counter'] = 1
                sleep(1)
            elif 0 < crash['crash_counter'] < 4 and crash['to_start'] == 0:
                self.server_data['crash']['crash_counter'] += 1
                sleep(1)
            elif 0 < crash['crash_counter'] >= 4 and crash['to_start'] == 0:
                self.server_data['crash']['players'] = {}
                self.server_data['crash']['crash_counter'] = 3
                self.server_data['crash']['to_start'] = 10
                sleep(1)
            elif crash['to_start'] > 0:
                self.server_data['crash']['to_start'] -= 1
                if self.server_data['crash']['to_start'] == 0:
                    self.server_data['crash'] = {'crash_multiplier': self.get_crash(), 'multiplier': 1.00, 'crash_counter': 0, 'to_start': 0, 'players': self.server_data['crash']['players']}
                else:
                    sleep(1)
            else:
                self.server_data['crash'] = {'crash_multiplier': self.get_crash(), 'multiplier': 1.00, 'crash_counter': 0, 'to_start': 0, 'players': {}}
            self.save_server_data()
            # print('{:.2f}'.format(round(self.server_data['crash']['multiplier'], 2)))

    def handle_messages(self, computer_name, conn):
        while True:
            try:
                bet = conn.recv(500).decode('utf-8')
                print(bet)
                if bet[0] == '$':
                    bet = float(bet[1:])
                    if self.server_data['crash']['crash_counter'] > 0 and self.server_data['crash']['to_start'] > 0 and self.server_data['players'][computer_name]['balance'] >= bet and computer_name not in self.server_data['crash']['players']:
                        # print(self.server_data['players'][computer_name]['username'] + ' has bet $' + str(bet))
                        self.server_data['players'][computer_name]['balance'] -= bet
                        self.server_data['crash']['players'][computer_name] = {'bet': bet, 'cashout': 0.00, 'username': self.server_data['players'][computer_name]['username']}
                elif bet[:3] == 'dep':
                    # dep%
                    # bet = float(bet[3:])
                    computer_name = bet[3:bet.find('%@#')]
                    amount = float(bet[bet.find('%@#') + 3:])
                    self.server_data['players'][computer_name]['balance'] += amount
                elif bet == 'pla':
                    print(json.dumps(self.server_data['players']))
                    for i in range(3):
                        sleep(.1)
                        conn.send(bytes('p$l$a$' + json.dumps(self.server_data['players']) + 'p%l%a%', 'utf-8'))
                else:
                    if self.server_data['crash']['crash_counter'] == 0 and computer_name in self.server_data['crash']['players'] and self.server_data['crash']['players'][computer_name]['cashout'] == 0:
                        self.server_data['crash']['players'][computer_name]['cashout'] = self.server_data['crash']['multiplier']
                        self.server_data['players'][computer_name]['balance'] += self.server_data['crash']['players'][computer_name]['bet'] * self.server_data['crash']['players'][computer_name]['cashout']
            except Exception as e:
                print('Error in handle messages')
                print(e)
                break

    def send_data(self):
        while True:
            conns = self.connections.copy()
            # print(self.server_data['crash']['players'])
            for addr in conns:
                try:
                    comp_name = self.connections[addr]['computer_name']
                    crashed = False
                    if self.server_data['crash']['crash_counter'] == 1:
                        crashed = True
                    client_data = {
                        'balance': self.server_data['players'][comp_name]['balance'],
                        'crash': self.server_data['crash']['multiplier'],
                        'to_start': self.server_data['crash']['to_start'],
                        'crashed': crashed,
                        'crash_counter': self.server_data['crash']['crash_counter'],
                        'crash_players': self.server_data['crash']['players'],
                        'username': self.server_data['players'][comp_name]['username'],
                    }
                    self.connections[addr]['connection'].sendall(bytes(self.split_string, 'utf-8'))
                    self.connections[addr]['connection'].sendall(bytes(json.dumps(client_data), 'utf-8'))
                except:
                    print('Disconnected from ' + self.connections[addr]['computer_name'])
                    self.connections.pop(addr)
                sleep(.05)

    def __del__(self):
        print('saving')
        # self.save_server_data()


# server_data = {'players': {}, 'crash_game': {}}
# client_data = {'balance': 0.0, 'crash_game': {}}

# server = GamblingServer(socket.gethostname(), 5000)
server = GamblingServer('104.237.133.98', 5000)




































