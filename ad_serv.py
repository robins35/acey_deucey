#!/usr/bin/env python

import sys
import getopt
import socket
import select
import time
from collections import deque
from random import shuffle

# DEFINING CLIENT CLASS HERE
class Client:
	next_id = 2
	max_msg_len = 80
	max_name_len = 16
	start_money = 4000
	def __init__(self, sock):
		self.sock = sock
		self.name = ''
		self.current_msg = ''
		self.msgs_to_srv = deque()
		self.id = Client.next_id
		#self.money = Client.start_money
		self.lobby_pos = -1
		self.game_pos = -1
		self.strikes_left = 3
		Client.next_id += 1

	def send_strike(self, code):
		self.strikes_left -= 1

		if self.strikes_left <= 0:
			# KICK THEM
			self.kick(0)
			return True
		else:
			# STRIKE THEM
			try:
				self.sock.send("[STRK|%d|%d]" % (3-self.strikes_left, code))
			except:
				self.kick(1)
			return False

	def kick(self, code):
		self.save_cli_info(code)
		if code != 1:
			print "SOMEBODY WAS KICKED"
		if self.game_pos > -1:
			pos = self.game_pos
			game[self.game_pos - 1] = None
			game_states['people_in_game'] -= 1
		elif self.lobby_pos > -1:
			pos = -1
			lobby[self.lobby_pos - 1] = None
			game_states['people_in_lobby'] -= 1
		else:
			pos = -1
		
		if code != 1:
			try:
				self.sock.send("[KICK|%d|%d]" % (pos, code))
			except:
				pass

		for i in range(0, len(pending_msgs)):
			if pending_msgs[i] == inputs[rd]:
				del pending_msgs[i]

		del inputs[self.sock]
		try:
			self.sock.shutdown(socket.SHUT_RDWR)
			self.sock.close()
		except:
			pass

	def save_cli_info(self, code):
		player_exists = False
		pos = -1

		try:
			f = open('account_info.txt', 'r')
			lines = f.readlines()
			f.close()
		except:
			lines = []

		for i in range(0, len(lines)):
			name = lines[i].split(' ')[0]
			if name == self.name:
				pos = i
				break
		if pos == -1:
			if code == 2:
				return
			lines.append("%s %d\n" % (self.name, self.money))
		else:
			if code == 2:
				del lines[pos]
			else:
				lines[pos] = "%s %d\n" % (self.name, self.money)
		f = open('account_info.txt', 'w')
		f.writelines(lines)
		f.close()

	def load_cli_info(self):
		money = Client.start_money
		entry = []
		try:
			f = open('account_info.txt', 'r')
			lines = f.readlines()
			f.close()
			for i in range(0, len(lines)):
				name, money = lines[i].split(' ')
				if name == self.name:
					break
				money = Client.start_money
			self.money = int(money)
		except:
			self.money = money
		print "THIS CHAP: %s HAS %d MONIESS" % (self.name, self.money)

	def add_msg(self, msg):
		for c in msg:
			if len(self.current_msg) >= Client.max_msg_len:
				print "ERROR: Message Length Excedes Maximum: %d" % Client.max_msg_len
				self.current_msg = ''
				self.send_strike(1)
				break;
			elif c == '[':
				if self.current_msg != '':
					print "ERROR: Invalid character '[' inside message: " + self.current_msg
					self.current_msg = ''
					self.send_strike(1)
					break
				else:
					self.current_msg = '['
			elif c == ']':
				if (not self.current_msg) or (self.current_msg[0] != '[') or (len(self.current_msg) < 7):
					print "ERROR: Incorrect Message Format1: msg: %s%c" % (self.current_msg, c)
					self.current_msg = ''
					self.send_strike(1)
					break
				else:
					if self not in pending_msgs:
						pending_msgs.append(self)
					self.msgs_to_srv.append(self.current_msg + ']')
					self.current_msg = ''
			else:
				self.current_msg += c
				if self.current_msg[0] != '[':
					print "ERROR: Incorrect Message Format2: msg: %s%c" % (self.current_msg, c)
					self.current_msg = ''
					self.send_strike(1)
					break

host = '' 
port = 36729
backlog = 5
size = 1024 
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind((host,port))
s.listen(backlog)

inputs = {
	s: {
		'current_id': 1
	}
}
lobby = deque()
game = deque()
pending_msgs = []

game_states = {
	'game_in_progress' : False,
	'waiting_for_bet' : False,
	'time_of_start' : float("inf"),
	'time_of_skip' : float("inf"),
	'turn' : -1,
	'people_in_lobby' : 0,
	'people_in_game' : 0,
	'current_cards' : (),
	'pot' : 0,
	'ante' : 30,
	'min_bet' : 20
}

max_players = 256
max_game = 40
min_game = 2
start_timeout = 5
bet_timeout = 45

try:
	opts, args = getopt.getopt(sys.argv[1:],"m:l:t:")
except getopt.GetoptError:
	print 'Invalid commandline argument format'
	sys.exit(2)
for opt, arg in opts:
	if opt == '-m':
		min_game = int(arg)
	elif opt == '-l':
		start_timeout = int(arg)
	elif opt == '-t':
		bet_timeout = int(arg)

def bet_outcome(card3, amount, bet):
	card1, card2 = game_states['current_cards']
	card1 = (int(card1) % 13) + 1
	card2 = (int(card2) % 13) + 1
	card3 = (int(card3) % 13) + 1
	# WE GOT AN ACE
	if card3 == 1:
		if card1 == 1 or card2 == 1:
			return (4 * amount)
		return amount
	elif card1 == card2:
		if card3 == card1:
			return (2 * amount)
		if bet == 'H':
			if card3 > card1:
				return (-1 * amount)
			return amount
		if bet == 'L':
			if card3 < card1:
				return (-1 * amount)
			return amount
		else:
			return 'err'
	elif card3 == card1 or card3 == card2:
		return (2 * amount)
	elif card3 > max(card1, card2) or card3 < min(card1, card2):
		return amount
	return (-1 * amount)


def process_cli_msg(cli):
	sent_strike = False
	msg = cli.msgs_to_srv.popleft()
	command = msg[1:5]

	if msg[5] != '|' and msg[5] != ' ':
		print "ERROR: Incorrect Command Length"
		cli.send_strike(0)
		return
	
	params = msg.split('|')[1:]
	params[-1] = params[-1][0:-1]
	
	if command == 'JOIN':
		if cli in lobby or cli in game:
			print "ERROR: Client has already joined"
			cli.send_strike(1)
			return
		elif len(params) != 1:
			print "ERROR: Wrong Number of Parameters"
			cli.send_strike(1)
			return
		name = params[0].strip()
		for c in name:
			if (ord(c) not in range(48, 58)) and (ord(c) not in range(65, 91)) and (ord(c) not in range(97, 123)):
				print "ERROR: Illegal Character in Name"
				cli.send_strike(1)
				return
		if len(name) > Client.max_name_len:
			print "ERROR: Username Too Long"
			cli.send_strike(1)
			return
		orig_name = name
		num = 1
		while (name in [x.name for x in lobby if x]) or (name in [x.name for x in game if x]):
			name = "%s%d" % (orig_name, num)
			num += 1
			if len(name) > Client.max_name_len:
				name = name[1:]
		lobby.append(cli)
		game_states['people_in_lobby'] += 1
		cli.name = name
		cli.lobby_pos = len(lobby)
		cli.load_cli_info()
		try:
			cli.sock.send("[JOIN|%s|%d|%d]" % (name, cli.money, len(lobby)))
		except:
			cli.kick(1)
		if game_states['game_in_progress']:
			for plyr in game:
				if plyr:
					try:
						cli.sock.send("[PLYR|%s|%d|%d]" % (plyr.name, plyr.game_pos, plyr.money))
					except:
						cli.kick(1)
	elif command == 'CHAT':
		print "Detected 'CHAT' Command"
		if cli.name == '':
			# CLIENT HASN'T JOINED YET
			return
		for c in params[0]:
			if (ord(c) not in range(32, 127)) or (ord(c) == 91 or ord(c) == 93):
				print "ERROR: Illegal Character in Chat"
				try:
					cli.send_strike(1)
				except:
					cli.kick(1)
				return
		broadcast("[CHAT|%s|%s]" % (cli.name, params[0]))
	elif command == 'BETS':
		print "RECEIVED: %s" % msg
		kicked = False
		bet = int(params[0])

		if (not game_states['game_in_progress']) or \
			(not game_states['waiting_for_bet']) or \
			(cli.game_pos != game[game_states['turn']].game_pos):
			cli.send_strike(4)
			return
		elif len(params) != 2:
			kicked = cli.send_strike(2)
			sent_strike = True
		elif (int(params[0]) > cli.money) or (int(params[0] < game_states['min_bet'])):
			kicked = cli.send_strike(4)
			sent_strike = True
		elif bet > game_states['pot']:
			bet = game_states['pot']

		car3 = deck.popleft()
		outcome = bet_outcome(car3, bet, params[1])
		if outcome > 0:
			print "PLAYER LOST"
		elif outcome < 0:
			print "PLAYER WON!"
		if outcome == 'err':
			kicked = cli.send_strike(2)
			sent_strike = True

		if kicked:
			next_turn()
			game_states['waiting_for_bet'] = False
			return

		if sent_strike:
			game_states['time_of_skip'] = int(time.time()) + bet_timeout
			return

		next_turn()
		game_states['waiting_for_bet'] = False
		cli.money -= outcome
		if cli.money < game_states['min_bet'] or cli.money <= 0:
			cli.kick(2)
		game_states['pot'] += outcome
		broadcast("[CAR3|%d|%s|%d|%d|%d]" % (cli.game_pos, car3, (-1 * outcome), game_states['pot'], cli.money))
	else:
		print "ERROR: Invalid Command: %s" % command
		cli.send_strike(0)

def broadcast(msg):
	print "BROADCAST: %s" % msg
	for sock in writable:
		if sock is not s:
			try:
				sock.send(msg)
			except:
				if sock in inputs:
				 	inputs[sock].kick(1)

def build_deck():
	deck = deque()
	for i in range(0,52):
		card = i
		if i < 10:
			card = '0' + str(i)
		else:
			card = str(i)
		deck.append(card)
		deck.append(card)
	shuffle(deck)
	return deck

def game_start():
	global deck
	if int(time.time()) >= game_states['time_of_start']:
		game_states['time_of_start'] = float("inf")
		print "Starting Game!"
		while (len(game) < max_game) and (len(lobby) > 0):
			plr = lobby.popleft()
			if plr:
				# NEED TO CHECK IF THEY HAVE ENOUGH MONIESSS
				game.append(plr)
				game_states['people_in_game'] += 1
				plr.game_pos = len(game)
				plr.lobby_pos = -1
				if (plr.money - (game_states['min_bet'] + game_states['ante'])) < 0:
					plr.kick(2)
				else:
					plr.money -= game_states['ante']
					game_states['pot'] += game_states['ante']
		print game_states['people_in_game']
		if len(game) < min_game:
			print "Somebody Quit, Start Aborted"
		else:
			# CREATING DECK, STARTING GAME
			deck = build_deck()
			########################
			game_states['game_in_progress'] = True
			game_states['turn'] = 0
			broadcast("[STRT|%d|%d]" % (game_states['ante'], game_states['pot']))
			for player in game:
				if player:
					broadcast("[PLYR|%s|%d|%d]" % (player.name, player.game_pos, player.money))
			time.sleep(3)


def game_over():
	global game
	count = 1
	
	for i in range(0, len(lobby)):
		if not lobby[i]:
			del lobby[i]
	game_states['people_in_lobby'] = len(lobby)
	for plyr in game:
		if plyr:
			if plyr.money < game_states['ante']:
				plyr.kick(2)
			else:
				lobby.append(plyr)
				for i in range(0, len(pending_msgs)):
					if pending_msgs[i] == plyr:
						del pending_msgs[i]
				game_states['people_in_lobby'] += 1
				plyr.game_pos = -1
	game = deque()
	game_states['people_in_game'] = 0
	for plyr in lobby:
			plyr.lobby_pos = count
			plyr.sock.send("[GMOV|%d|%d]" % (plyr.lobby_pos, plyr.money))
			count += 1
	game_states['time_of_skip'] = float("inf")
	game_states['time_of_start'] = float("inf")
	game_states['game_in_progress'] = False
	game_states['waiting_for_bet'] = False
	game_states['pot'] = 0
	print "GAME OVER"
	time.sleep(.5)

def next_turn():
	game_states['turn'] += 1
	if game_states['turn'] >= len(game):
		game_states['turn'] = 0
	while not game[game_states['turn']]:
		game_states['turn'] += 1
		if game_states['turn'] >= len(game):
			game_states['turn'] = 0

while 1:
	#time.sleep(.01)
	readable, writable, exceptional = select.select(inputs.keys(), inputs.keys(), inputs.keys(), 0.01)

	# CHECK FOR NEW CONNECTIONS, NEW MESSAGES, OR SEVERED CONNECTIONS
	for rd in readable:
		if rd is s:
			if (len(inputs) - 1) < max_players:
				client, address = s.accept()
				if client:
					print "Client Connected"
					inputs[client] = Client(client)
		else:
			try:
				data = rd.recv(size)
			except:
				print "Client Crashed"
				data = 0
			if data:
				inputs[rd].add_msg(data)
			else:
				print "Client Quit\n"
				inputs[rd].kick(1)

	# PROCESS ALL PENDING MESSAGES INCOMING
	for cli in pending_msgs:
		process_cli_msg(cli)
		if not len(cli.msgs_to_srv) and cli in pending_msgs:
			pending_msgs.remove(cli)

	# BASIC GAME LOOP BASIC GAME LOOP
	if game_states['game_in_progress']:
		#CHECK THAT WE HAVE ENOUGH PEOPLE
		if game_states['people_in_game'] <= 1 or game_states['pot'] <= 0:
			if game_states['people_in_game'] == 1:
				for plyr in game:
					if plyr:
						plyr.money = plyr.money + game_states['pot']
						break
			game_over()
		else:
			#CHECK THAT THE CURRENT TURN IS AN ACTUAL PLAYER
			count = 0
			while not game[game_states['turn']] and count < len(game):
				print "SOMETHING BROKE BEGINNING OF GAME LOOP"
				game_states['turn'] += 1
				if game_states['turn'] >= len(game):
					game_states['turn'] = 0
				count += 1

			if not game_states['waiting_for_bet']:
				if len(deck) < 3:
					deck = build_deck()
					broadcast("[SHUF]")
				game_states['current_cards'] = (deck.popleft(), deck.popleft())
				broadcast("[CAR1|%d|%d|%s|%s]" % (game[game_states['turn']].game_pos, game_states['min_bet'], game_states['current_cards'][0], game_states['current_cards'][1]))
				game_states['waiting_for_bet'] = True
				game_states['time_of_skip'] = int(time.time()) + bet_timeout
			elif int(time.time()) >= game_states['time_of_skip']:
				print "TOOK TOO LONG TO BET, KICKING: %d in game" % game_states['people_in_game']
				plr = game[game_states['turn']]

				if plr:
					plr.kick(1)

				next_turn()
				game_states['waiting_for_bet'] = False
	elif (not game_states['time_of_start'] < float("inf")) and (game_states['people_in_lobby'] >= min_game):
		print "Commencing Count Down: %d seconds" % start_timeout
		game_states['time_of_start'] = int(time.time()) + start_timeout
	elif game_states['time_of_start'] < int(time.time()):
		game_start()
