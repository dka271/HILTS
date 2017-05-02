#pip3 install --upgrade google-api-python-client
#pip3 install --upgrade google-cloud-speech
#sudo apt-get install sox
#Set environment variable GOOGLE_APPLICATION_CREDENTIALS="/full/path/to/
#your/client_secret.json" in /etc/profile and reboot
#change to default audio in alsamixer
from oauth2client.client import GoogleCredentials
from googleapiclient.discovery import build
from google.cloud import speech
import subprocess

#Authentication for Google API
print("Authenticating to Google API")
credentials = GoogleCredentials.get_application_default()
service = build('speech', 'v1beta1', credentials=credentials)

#Creating an instance of the client
print("Creating client")
client = speech.Client()

#Recording raw audio
print("Recording")
subprocess.call(["rec", "soundTest1.wav", "trim", "0", "5"])

#Transcribing with Google Speech API
print("Streaming to Google Speech API")
with open('/home/pi/Desktop/HILTS/ActualFiles/soundTest1.wav', 'rb') as stream:
   sample = client.sample(stream=stream, encoding=speech.Encoding.LINEAR16, sample_rate_hertz=48000)
   results = sample.streaming_recognize(language_code='en-US')
   
   for result in results:
      for alternative in result.alternatives:
         print('=' * 20)
         print('transcript: ' + alternative.transcript)
         print('confidence: ' + str(alternative.confidence))
