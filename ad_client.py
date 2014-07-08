#!/usr/bin/env python 

import sys
import socket
import select
import textwrap
import time
import getopt
from collections import deque
from random import choice
sys.path.insert(0, 'pgu-depend')
import pygame
from pygame.locals import *
from pgu import gui
from pgu import html

class Player:
	def __init__(self, name, pos, money):
		self.name = name
		self.pos = pos
		self.money = money

class custom_app(gui.Desktop):
	def __init__(self, name, manual, ai, **params):
		super(custom_app, self).__init__(**params)
		self.name = name
		self.manual = manual
		self.ai = ai
		self.game_pos = -1
		self.money = 0
		self.waiting_on_bet = False
		self.HL = False
		self.bet_type = ''
		self.face_conversion = ["Ace", "2", "3", "4", "5", "6", "7", "8", "9", "10", "Jack", "Queen", "King"]
		self.current_deck = [8 for x in range(0, 13)]
		self.current_msg = ''
		self.messages = deque()
		self.max_msg_len = 80
		self.players = []
		self.playing = False

	"""def loop(self):
		readable, writable, exceptional = select.select([s], [s], [s], .01)
		if len(readable):
			data = s.recv(size)
			if data:
				self.add_msg(data)
				self.process_msgs()
			else:
				print "SERVER SHUTDOWN"
				sys.exit()
		super(custom_app, self).loop()"""
		
	def run(self, widget=None, screen=None, delay=10):
		self.init(widget,screen)
		while not self._quit:
			self.loop()
			pygame.time.wait(delay)
			# SERVER CODE GOES HERE
			readable, writable, exceptional = select.select([s], [s], [s])
			if len(readable):
				data = s.recv(size)
				if data:
					self.add_msg(data)
					self.process_msgs()
				else:
					print "SERVER SHUTDOWN"
					sys.exit()


	def stringify_cards(self, cards):
		for i in range(0, len(cards)):
			face = self.face_conversion[int(cards[i]) % 13]
			suit = int(cards[i]) / 13
			if suit == 0:
				suit = "Clubs"
			elif suit == 1:
				suit = "Diamonds"
			elif suit == 2:
				suit = "Hearts"
			elif suit == 3:
				suit = "Spades"
			cards[i] = "%s of %s" % (face, suit)
		return tuple(cards)

	def prompt_bet(self, params):
		high_low = False
		self.waiting_on_bet = True
		if self.manual:
			display_text(cons_lines, "You got the %s and the %s." % self.stringify_cards([params[2], params[3]]))
		if self.get_cardface(params[2]) == self.get_cardface(params[3]):
			self.HL = True
			if self.manual:
				display_text(cons_lines, "Please enter 'H' or 'L' for high or low bet:")
		else:
			if self.manual:
				display_text(cons_lines, "Please enter how much you want to bet:")

	def bet(self, card1, card2, minbet):
		#time.sleep(.5)
		card1 = self.get_cardface(card1)
		card2 = self.get_cardface(card2)
		if self.HL:
			if self.ai:
				card_count = 0
				for cnt in self.current_deck:
					card_count += cnt

				hi_prob = 0
				low_prob = 0
				bad_prob = self.current_deck[card1] / float(card_count)
				for card in range(0, card1):
					low_prob += self.current_deck[card]
				for card in range(card1+1, 13):
					hi_prob += self.current_deck[card]

				hi_prob = (hi_prob / float(card_count)) - bad_prob
				low_prob = low_prob / float(card_count) - bad_prob

				if hi_prob > low_prob:
					hl = 'H'
					if hi_prob <= 0:
						bet = minbet
					else:
						bet = int(hi_prob * self.money)
				else:
					hl = 'L'
					if low_prob <= 0:
						bet = minbet
					else:
						bet = int(low_prob * self.money)
			else:
				hl = choice(('H', 'L'))
				bet = minbet
		else:
			hl = 'B'
			if self.ai:
				card_count = 0
				for cnt in self.current_deck:
					card_count += cnt

				good_prob = 0
				for card in range(min(card1, card2) + 1, max(card1, card2)):
					good_prob += self.current_deck[card]

				good_prob = good_prob / float(card_count)

				if good_prob > 0.7:
					#print "UH OH: good_prob = %f | card_count = %d" % (good_prob, card_count)
					#print self.current_deck
					#raw_input()
					good_prob = 0.7

				#bet = int(good_prob * self.pot)
				bet = int(good_prob * self.money)
			else:
				bet = minbet
		if bet < minbet:
			bet = minbet
		elif bet > self.money:
			bet = self.money
		elif bet > self.pot:
			bet = self.pot
		s.send("[BETS|%d|%c]" % (bet, hl))
		self.waiting_on_bet = False
		self.HL = False

	def get_cardface(self, card):
		return int(card) % 13

	def add_msg(self, msg):
		for c in msg:
			if c == '[':
				if self.current_msg != '':
					print "ERROR: Invalid character '[' inside message: " + self.current_msg
					self.current_msg = ''
					break
				else:
					self.current_msg = '['
			elif c == ']':
				if (not self.current_msg) or (self.current_msg[0] != '[') or (len(self.current_msg) < 5):
					print "ERROR: Incorrect Message Format1: msg: %s%c" % (self.current_msg, c)
					self.current_msg = ''
					break
				else:
					self.messages.append(self.current_msg + ']')
					self.current_msg = ''
			else:
				self.current_msg += c
				if self.current_msg[0] != '[':
					print "ERROR: Incorrect Message Format2: msg: %s%c" % (self.current_msg, c)
					self.current_msg = ''
					break

	def process_msgs(self):
		for d in self.messages:
			print "RECEIVED MESSAGE: '%s'" % d
			cmd = d[1:5]
			params = d.strip('\r\n').split('|')
			del params[0]
			
			if params != []:
				params[-1] = params[-1][0:-1]

			if d == '':
				break
			if cmd == "JOIN":
				print "RECEIVED INCORRECT JOIN MSG"
				self.name = d[1:].split("|")[1]
			elif cmd == "PLYR":
				if params[0] == self.name:
					self.game_pos = int(params[1])
					self.money = int(params[2])
					self.playing = True
					display_text(cons_lines, "You are starting with %s money" % params[2])
					display_text(cons_lines, "----------------------------------")
				else:
					self.players.append(Player(params[0], int(params[1]), int(params[2])))
			elif cmd == "CAR1" and self.playing:
				if int(params[0]) == self.game_pos:
					self.prompt_bet(params)
					if not self.manual:
						self.current_deck[self.get_cardface(params[2])] -= 1
						self.current_deck[self.get_cardface(params[3])] -= 1
						if self.current_deck[self.get_cardface(params[2])] < 0:
							self.current_deck[self.get_cardface(params[2])] = 0
						if self.current_deck[self.get_cardface(params[3])] < 0:
							self.current_deck[self.get_cardface(params[3])] = 0
						self.bet(params[2], params[3], int(params[1]))
			elif cmd == "CAR3" and self.playing:
				self.current_deck[self.get_cardface(params[1])] -= 1
				if self.current_deck[self.get_cardface(params[1])] < 0:
					self.current_deck[self.get_cardface(params[1])] = 0
				name_suffix = "ERROR"
				name = "ERROR"
				plyr = self
				if int(params[0]) == self.game_pos:
					name_suffix = "were"
					name = "you"
					plyr = self
					display_text(cons_lines, "")
				else:
					for p in self.players:
						if p:
							if p.pos == int(params[0]):
								name_suffix = "was"
								name = "%s" % p.name
								plyr = p
								break

				plyr.money = int(params[4])

				if self.manual:
					display_text(cons_lines, "%s %s dealt the %s" % (name, name_suffix, self.stringify_cards([params[1]])))
				if int(params[2]) > 0:
					if self.manual:
						display_text(cons_lines, "%s won - Current Money: %s - Current Pot: %s" % (name, params[4], params[3]))
				elif int(params[2]) < 0:
					if self.manual:
						display_text(cons_lines, "%s lost - Current Money: %s - Current Pot: %s" % (name, params[4], params[3]))
				if self.manual:
					display_text(cons_lines, "----------------------------------")
				plyr.money = int(params[4])
				self.pot = int(params[3])
			elif cmd == "CHAT":
				display_text(chat_lines, "%s: %s" % (params[0], params[1]))
				display_text(chat_lines, "----------------------------------")
			elif cmd == "KICK":
				if int(params[0]) == self.game_pos or int(params[0]) == -1:
					display_text(cons_lines, "YOU WERE KICKED...See Ya.")
					time.sleep(5)
					sys.exit()
			elif cmd == "STRT":
				display_text(cons_lines, "A GAME IS STARTING! You had to pay an ante of %s. The pot is %s." % (params[0], params[1]))
				self.pot = int(params[1])
			elif cmd == "GMOV":
				display_text(cons_lines, "GAME OVER!")
				display_text(cons_lines, "YOU GOT %d DOLLAS" % self.money)
				display_text(cons_lines, "----------------------------------")
				self.game_pos = -1
				self.lobby_pos = int(params[0])
				self.waiting_on_bet = False
				self.playing = False
				self.players = []
				self.money = int(params[1])
				print "I GOT %d DOLLAS" % self.money
			elif cmd == "STRK":
				if int(params[1]) == 4:
					print "You entered an invalid bet"
			elif cmd == "SHUF":
				self.current_deck = [8 for x in range(0, 13)]
			else:
				if self.playing:
					print "RECEIVED UNKNOWN MESSAGE TYPE: %s" % cmd
		self.messages = deque()
		cmd = ''
def display_text(disp, text, color=None):
	text_lines = textwrap.wrap(text, width=38)
	for l in text_lines:
		#lin = html.HTML("""<span style='font-weight: bold'>""" + l + """</span>""")
		disp.tr()
		disp.td(gui.Label(str(l)), align=-1)
		#disp.td(lin, align=-1)

def cons_submit(_event):
	global app
	e = _event
	if e.key == K_RETURN:
		val = cons_in.value
		cons_in.value = ''
		cons_in.focus()
		display_text(cons_lines, val)
		if app.waiting_on_bet:
			if app.HL:
				if val != 'H' and val != 'L':
					display_text(cons_lines, "ERROR: You must enter an 'H' or an 'L'")
				else:
					app.bet_type = val
					app.HL = False
					display_text(cons_lines, "Please enter how much you want to bet:")
			else:
				# NEED TO VALIDATE BET HERE
				app.waiting_on_bet = False
				if app.bet_type == '':
					app.bet_type = 'B'
				s.send("[BETS|%s|%c]" % (val, app.bet_type))
				app.bet_type = ''
		

def chat_submit(_event):
	e = _event
	if e.key == K_RETURN:
		val = chat_in.value
		chat_in.value = ''
		chat_in.focus()
		if val is not '':
			s.send("[CHAT|%s]" % val)

###########################################################################
###########################################################################
host = ''
port = 0
manual = False
ai = False

try:
	opts, args = getopt.getopt(sys.argv[1:],"s:p:ma")
except getopt.GetoptError:
	print 'Invalid commandline argument format'
	sys.exit(2)

for opt, arg in opts:
	if opt == '-s':
		host = arg
	elif opt == '-p':
		port = int(arg)
	elif opt == '-m':
		manual = True
	elif opt == '-a':
		ai = True
		
if not host:
	host = raw_input("Enter the host address, or nothing for localhost > ")
	if host == '':
		host = 'localhost'

if not port:
	port = raw_input("Enter the host port, or nothing for default > ")
	if port == '':
		port = 36729
	else:
		port = int(port)

size = 1024 
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
s.connect((host,port))

name = raw_input("Enter your username > ")
if name == '':
	name = 'GUEST'
s.send("[JOIN|%s]" % name)

no_name = True
while no_name:
	data = s.recv(size)
	data = data.split(']')
	for d in data:
		print "RECEIVED MESSAGE: '%s'" % d
		if d == '':
			no_name = False
			break
		if d[1:5] == "JOIN":
			name = d[1:].split("|")[1]
			no_name = False
			break



#########################################################################
# BUILDING INTERFACE HERE

app = custom_app(name, manual, ai)
app.connect(gui.QUIT,app.quit,None)

main = gui.Container(width=1010, height=520) #, background=(220, 220, 220) )
#main = contt(width=710, height=410)

main.add(gui.Label("Console", cls="h1"), 10, 10)
main.add(gui.Label("Chat", cls="h1"), 540, 10)


cons_in = gui.Input(size=48)
chat_in = gui.Input(size=48)

cons_in.connect(gui.KEYDOWN,cons_submit)
chat_in.connect(gui.KEYDOWN,chat_submit)

cons_out_T = gui.Table(width=450,height=450)
chat_out_T = gui.Table(width=450,height=450)
main.add(cons_out_T, 10, 50)
main.add(chat_out_T, 540, 50)

cons_out_T.tr()
cons_lines = gui.Table()
cons_out = gui.ScrollArea(cons_lines,450,450, font="monospace")
cons_out_T.td(cons_out)

cons_out_T.tr()
cons_out_T.td(cons_in)

cons_out_T.tr()

class Hack(gui.Spacer):
	def __init__(self, width, height, target):
		super(Hack, self).__init__(width, height)
		self.target = target
	def resize(self,width=None,height=None):
		self.target.set_vertical_scroll(65535)
		self.target.set_horizontal_scroll(0)
		return 1,1

cons_out_T.td(Hack(1,1, cons_out))

chat_out_T.tr()
chat_lines = gui.Table()
chat_out = gui.ScrollArea(chat_lines,450,450)
chat_out_T.td(chat_out)

chat_out_T.tr()

chat_out_T.td(chat_in)

chat_out_T.tr()

chat_out_T.td(Hack(1,1, chat_out))

app.run(main)

s.shutdown(socket.SHUT_RDWR)
s.close()
print "BYE"
