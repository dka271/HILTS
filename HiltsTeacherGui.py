# Simple enough, just import everything from tkinter.
from cgitb import text
from tkinter import *
import socket   #for sockets import sys  #for exit
import sys
import threading

import pika
import time
import subprocess

import RPi.GPIO as GPIO

from oauth2client.client import GoogleCredentials
from googleapiclient.discovery import build
from google.cloud import speech

##########GOOGLE SPEECH API SETUP #########
#Authentication for Google API
print("Authenticating to Google API")
credentials = GoogleCredentials.get_application_default()
service = build('speech', 'v1beta1', credentials=credentials)

#Creating an instance of the client
print("Creating client")
client = speech.Client()
###########################################

####### GPIO SETUP ########################
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD) ## Use board pin numbering
GPIO.setup(7, GPIO.OUT) ## Setup GPIO Pin 7 to OUT (actually pin 4) (red)
GPIO.setup(11, GPIO.OUT) ## Setup GPIO Pin 11 to OUT (actually pin 17) (green)
GPIO.setup(15, GPIO.OUT) ## Setup GPIO Pin 15 to OUT (actually pin 22) (blue)
GPIO.output(7, False)
###### END SETUP ##########################

s = None
host = '';
port = 8888;
connectButton = None
startButton = None
questionBox = None
disconnectButton = None
transcriptArea = None
clearQuestionButton = None
languageDropdown = None
transcriptText = " "
x = 1
goThread = True
languageVar = 'en-US'

def updateQuestionBoxThread():
	global s
	global transcriptArea
	global host
	global port
	global questionBox
	global goThread
	# Bind socket to local host and port
	try:
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		s.bind((host, port))
	except socket.error as msg:
		sys.exit()

	# now keep talking with the client
	while goThread:
		d = s.recvfrom(1024)
		data = d[0]
		addr = d[1]

		if not data:
			break
		questionBox.text.config(state="normal")
		questionBox.text.insert(END, str(d[0].decode('utf-8')))
		questionBox.text.config(state="disabled")
		clearQuestionButton.config(state="normal")
		
		GPIO.output(7, True)
		
		#print('Message[' + str(addr[0]) + '] - ' + str(data.strip()))
	exit()

def getQueues():
	txt = subprocess.check_output(['sudo', '/usr/sbin/rabbitmqctl', 'list_queues', '-p', 'HILTS'], stderr = subprocess.STDOUT)

	lineList = txt.decode('utf-8').split('\n');

	lineList.pop(0)
	lineList.pop(-1)
	lineList.pop(-1)

	qList = [];
	for queue in lineList:
		qList.append(queue.split('\t')[0])
	
	return qList


def getGoogled():
	global x
	x = 1
	while goThread:
		#Recording raw audio
		#print("Recording")
		subprocess.call(["rec", "soundTest"+str(x)+".wav", "trim", "0", "10"])
		time.sleep(1)
		queryGThread = threading.Thread(target = getTextFromSpeech)
		queryGThread.daemon = True
		queryGThread.start()
		
		if x == 1: x = 2
		elif x == 2: x = 1
		
def getTextFromSpeech():
	global transcriptText
	global x
	global languageVar

	tempTrans = " "
	tempbool = True
	#Transcribing with Google Speech API
	#print("Streaming to Google Speech API")
	
	with open('/home/pi/Desktop/HILTS/ActualFiles/soundTest'+str(x)+'.wav', 'rb') as stream:
		
		sample = client.sample(stream=stream, encoding=speech.Encoding.LINEAR16, sample_rate_hertz=48000)
		
		results = sample.streaming_recognize(language_code=languageVar)
		
		for result in results:
			for alternative in result.alternatives:
				#print('=' * 20)
				#print('transcript: ' + alternative.transcript)
				#print('confidence: ' + str(alternative.confidence))
				if tempbool:
					tempTrans = alternative.transcript
					tempbool = False
		
		transcriptText = tempTrans

def updateTranscriptThread():
	global s
	global transcriptArea
	global host
	global port
	global questionBox
	global transcriptText
	global goThread
	
	creds = pika.PlainCredentials("t7", "7licious")
	params = pika.ConnectionParameters(str(host), 5672, virtual_host = "HILTS", credentials=creds)
	connection = pika.BlockingConnection(params)
	channel = connection.channel()

	#transcriptText = "Transcript Test Sentence. 12345679 abcdefg"

	channel.queue_declare(queue = 'teacher')

	while goThread:
		
		if(transcriptText  != " "):
			qList = getQueues()
			for item in qList:
				channel.queue_declare(queue = item)
			
			for item in qList:
				channel.basic_publish(exchange = '', routing_key = item, body = transcriptText)
			
			transcriptText = " "
		

	connection.close()
	exit()
	

def teacherCallback(ch, method, properties, body):
	global transcriptArea
	transcriptArea.text.config(state="normal")
	transcriptArea.text.insert(END, body.decode('utf-8') + '\n')
	transcriptArea.text.config(state="disabled")

def teacherDisplayThread():
	global host
	global port
	
	creds = pika.PlainCredentials("t7", "7licious")
	params = pika.ConnectionParameters(str(host), 5672, virtual_host = "HILTS", credentials=creds)
	connection = pika.BlockingConnection(params)
	channel = connection.channel()
	
	channel.basic_consume(teacherCallback, queue= 'teacher', no_ack=True)
	channel.start_consuming()

class scrollTxtArea:
	def __init__(self, root):
		frame = Frame(root)
		frame.pack()
		self.textPad(frame)
		return

	def textPad(self, frame):
		# add a frame and put a text area into it
		textPad = Frame(frame)
		self.text = Text(textPad, height=10, width=48)

		# add a vertical scroll bar to the text area
		scroll = Scrollbar(textPad)
		self.text.configure(yscrollcommand=scroll.set)

		# pack everything
		self.text.pack(side=LEFT)
		scroll.pack(side=RIGHT, fill=Y)
		textPad.pack(side=TOP)
		return
		
class scrollTxtAreaNew:
	def __init__(self, root):
		frame = Frame(root)
		frame.pack()
		self.textPad(frame)
		return

	def textPad(self, frame):
		# add a frame and put a text area into it
		textPad = Frame(frame)
		self.text = Text(textPad, height=5, width=48)

		# add a vertical scroll bar to the text area
		scroll = Scrollbar(textPad)
		self.text.configure(yscrollcommand=scroll.set)

		# pack everything
		self.text.pack(side=LEFT)
		scroll.pack(side=RIGHT, fill=Y)
		textPad.pack(side=TOP)
		return


def calculateChecksum(inJSONData):
	checksum = 0;
	checksum = sum(bytearray(inJSONData.replace(" ", ""), 'utf8'))
	checksumInsert = ":" + str(checksum) + "}"
	return inJSONData.replace(":}", checksumInsert)

# Here, we are creating our class, Window, and inheriting from the Frame
# class. Frame is a class from the tkinter module. (see Lib/tkinter/__init__)
class Window(Frame):
	# Define settings upon initialization. Here you can specify
	def __init__(self, master=None):
		# parameters that you want to send through the Frame class.
		Frame.__init__(self, master)

		# reference to the master widget, which is the tk window
		self.master = master

		# with that, we want to then run init_window, which doesn't yet exist
		self.init_window()

	# Creation of init_window
	def init_window(self):
		global connectButton
		global disconnectButton
		global clearQuestionButton
		global questionBox
		global transcriptArea
		global languageDropdown
		# changing the title of our master widget
		self.master.title("HILTS: Teacher")

		# allowing the widget to take the full space of the root window
		self.pack(fill=BOTH, expand=1)

		# creating a menu instance
		menu = Menu(self.master)
		self.master.config(menu=menu)

		# create the file object)
		file = Menu(menu)

		# adds a command to the menu option, calling it exit, and the
		# command it runs on event is client_exit
		file.add_command(label="Exit", command=self.client_exit)

		# added "file" to our menu
		menu.add_cascade(label="File", menu=file)

		# create the file object)
		edit = Menu(menu)

		# adds a command to the menu option, calling it exit, and the
		# command it runs on event is client_exit
		edit.add_command(label="Undo")

		# added "file" to our menu
		menu.add_cascade(label="Edit", menu=edit)

		connectButton = Button(self, text="Start", command=self.client_connect)
		disconnectButton = Button(self, text="Disconnect", command=self.client_disconnect)
		clearQuestionButton = Button(self, text="Clear Questions", command=self.client_clearQuestions)
		#questionBox = Text(root)
		questionBox = scrollTxtAreaNew(root)
		questionBox.text.config(state="disabled")
		
		transcriptArea = scrollTxtArea(root)
		transcriptArea.text.config(state="disabled")


		languageOptionList = ["English(US)", "Espanol(Mexico)", "Tiếng Việt", "français", "Deutsche", "中文（简体香港）", "日本語", "русский", "italiano"]
		langDropVar = StringVar()
		langDropVar.set("English(US)")  # default choice
		languageVar = "en-US"
		languageDropdown = OptionMenu(self, langDropVar, *languageOptionList, command=self.updateCurrentLanguage);

		# placing the button on my window
		connectButton.place(x=0, y=0)
		#questionBox.place(x=0, y=75)
		#questionBox.config(height=3, width=50)
		disconnectButton.place(x=60, y=0)
		clearQuestionButton.place(x=180, y=0)
		languageDropdown.place(x=180, y=30)

		disconnectButton.config(state="disabled")
		#questionBox.config(state="disabled")
		clearQuestionButton.config(state="disabled")

	def updateCurrentLanguage(self, value):
		global languageVar

		if (value == "English(US)"):
			languageVar = 'en-US'
		elif (value == "Espanol(Mexico)"):
			languageVar = 'es-MX'
		elif (value == "Tiếng Việt"):
			languageVar = 'vi-VN'
		elif (value == "français"):
			languageVar = 'fr-FR'
		elif (value == "Deutsche"):
			languageVar = 'de-DE'
		elif (value == "中文（简体香港）"):
			languageVar = 'cmn-Hans-CN'
		elif (value == "日本語"):
			languageVar = 'ja-JP'
		elif (value == "русский"):
			languageVar = 'ru-RU'
		elif (value == "italiano"):
			languageVar = 'it-IT'

	def client_exit(self):
		global goThread
		goThread = False
		exit()
		
	def client_clearQuestions(self):
		global questionBox
		global clearQuestionButton
		clearQuestionButton.config(state="disabled")
		questionBox.text.config(state="normal")
		questionBox.text.delete(1.0, 'end')
		questionBox.text.config(state="disabled")
		
		GPIO.output(7, False)
		

	def client_disconnect(self):
		global connectButton
		global goThread
		connectButton.config(state="normal")
		goThread = False

	def client_connect(self):
		global s
		global host
		global port
		global connectButton
		global disconnectButton
		global goThread
		try:
			disconnectButton.config(state="normal")
			#questionBox.config(state="normal")
			goThread = True
			myThread = threading.Thread(target=updateTranscriptThread)
			myThread.daemon = True ###
			myThread.start()
			
			questionThread = threading.Thread(target = updateQuestionBoxThread)
			questionThread.daemon = True ###
			questionThread.start()
			
			teachThread = threading.Thread(target = teacherDisplayThread)
			teachThread.daemon = True ###
			teachThread.start()
			
			googleThread = threading.Thread(target = getGoogled)
			googleThread.daemon = True ###
			googleThread.start()
			
		except socket.error:
			print('Failed to create socket')
			sys.exit()

	def client_question(self):
		global s
		global host
		global port
		global connectButton
		global questionBox

		msg = questionBox.text.get()
		if (msg != ""):
			try:  # Set the whole string
				s.sendto(msg.encode(), (host, port))
				questionBox.text.config(state="normal")
				questionBox.text.delete(1.0, 'end')
				questionBox.text.config(state="disabled")
				# receive data from client (data, addr)
			except socket.error as  msg:
				print(b'Error Code : ' + str(msg[0]) + b' Message ' + msg[1])
				sys.exit()


# root window created. Here, that would be the only window, but
# you can later have windows within windows.
root = Tk()

root.geometry("400x300")

# creation of an instance
app = Window(root)

# mainloop
root.mainloop()
