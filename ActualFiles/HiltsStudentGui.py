# Simple enough, just import everything from tkinter.
from cgitb import text
from tkinter import *
import socket   #for sockets import sys  #for exit
import sys
import threading
import pika
import time

s = None
host = 'localhost';
port = 8888;
connectButton = None
startButton = None
questionButton = None
questionBox = None
entryBox = None
nameEntryBox = None
disconnectButton = None
transcriptArea = None

##PETES RABBIT MQ JANK i.e Trancript Receive#####

RabbitMQUserName = "t7"
RabbitMQPassword = "7licious"
virtualHost = "HILTS"
studentName = "pete"


def callback1(ch, method, properties, body):
    global transcriptArea
    transcriptArea.text.config(state="normal")
    transcriptArea.text.insert(END, body.decode('utf-8') + '\n')
    transcriptArea.text.config(state="disabled")
    # print("Transcript: %r" % body.decode('utf-8'))


##########################

def updateTranscriptThread():
    global s
    global transcriptArea
    global host
    global port
    global questionButton
    global studentName

    try:
        creds = pika.PlainCredentials("t7", "7licious")
        params = pika.ConnectionParameters(str(host), 5672, virtual_host="HILTS", credentials=creds)
        connection = pika.BlockingConnection(params)

    except pika.exceptions.AuthenticationError:
        print("Authentication Error")

    except pika.exceptions.ProbableAuthenticationError:
        print("Probable Authentication Error")

    except pika.exceptions.AMQPConnectionError:
        print("AMQP Exception Error")

    except:
        print("Error has occurred in attempting connection to Server")

    else:
        try:
            channel = connection.channel()
            channel.queue_declare(queue = ((str(studentName)).replace(" ", "")).lower())
            # print(((str(studentName)).replace(" ", "")).lower())

            # basic consume for each channel
            channel.basic_consume(callback1, queue=((str(studentName)).replace(" ", "")).lower(), no_ack=True)

            print(' [*] Waiting for Messages. To exit press CTRL+C')
            channel.start_consuming()

        except pika.exceptions.ChannelError:
            print("Channel Error has occurred")
        except:
            print("Error in Consumption!")


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
        global entryBox
        global nameEntryBox
        global disconnectButton
        global questionBox
        global questionButton
        global transcriptArea
        # changing the title of our master widget
        self.master.title("HILTS: Student")

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

        connectButton = Button(self, text="Connect", command=self.client_connect)
        questionButton = Button(self, text="Send Question", command=self.client_question)
        disconnectButton = Button(self, text="Disconnect", command=self.client_disconnect)
        entryBox = Entry(self)
        nameEntryBox = Entry(self)
        questionBox = Entry(self)
        ipAddressLabel = Label(self, text="IP:")
        nameLabel = Label(self, text="Name:")

        transcriptArea = scrollTxtArea(root)

        # placing the button on my window
        connectButton.place(x=0, y=0)
        entryBox.place(x=20, y=30)
        ipAddressLabel.place(x=0, y=30)
        nameEntryBox.place(x=210, y=30)
        nameLabel.place(x=160, y=30)
        questionButton.place(x=0, y=60)
        questionBox.place(x=120, y=60)
        #disconnectButton.place(x=100, y=0)

        disconnectButton.config(state="disabled")
        questionButton.config(state="disabled")
        questionBox.config(state="disabled")
        transcriptArea.text.config(state="disabled")

    def client_exit(self):
        exit()

    def client_disconnect(self):
        global connectButton
        global entryBox
        global nameEntryBox
        connectButton.config(state="normal")
        entryBox.config(state="normal")
        nameEntryBox.config(state="normal")

    def client_connect(self):
        global s
        global host
        global port
        global connectButton
        global entryBox
        global disconnectButton
        global nameEntryBox
        global studentName
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            temp = entryBox.get()
            tempName = nameEntryBox.get()
            if (temp == "" or tempName == ""):
                return
            host = entryBox.get()
            studentName = tempName
            entryBox.config(state="disabled")
            nameEntryBox.config(state="disabled")
            disconnectButton.config(state="normal")
            questionButton.config(state="normal")
            questionBox.config(state="normal")
            myThread = threading.Thread(target=updateTranscriptThread)
            myThread.daemon = True
            myThread.start()
        except socket.error:
            print('Failed to create socket')
            sys.exit()

    def client_question(self):
        global s
        global host
        global port
        global connectButton
        global questionButton
        global questionBox, studentName

        msg = questionBox.get()
        if (msg != ""):
            msg = studentName + ': "' + msg+ '"' + "\n"
            try:  # Set the whole string
                s.sendto(msg.encode(), (host, port))
                questionBox.delete(0, 'end')
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
