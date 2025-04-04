import vosk
import json
import queue
import sounddevice as sd
from gpiozero import LED
from threading import Thread, Event

# Configuration
model_path = MODEL_PATH
sample_rate = 16000
words = ["start", "stop", "one", "two", "three", "four", "five", 
         "six", "seven", "eight", "nine", "zero", "point"]
MIN_CONFIDENCE = 0.9

# GPIO setup
fan = LED(24)

# Audio setup
audio_queue = queue.Queue()
stop_event = Event()

# Word to character mapping
WORD_MAP = {
    "zero": "0", "one": "1", "two": "2", "three": "3",
    "four": "4", "five": "5", "six": "6", "seven": "7",
    "eight": "8", "nine": "9", "point": "."
}

def audio_callback(indata, frames, time, status):
    audio_queue.put(bytes(indata))

def recognize():
    model = vosk.Model(model_path)
    recognizer = vosk.KaldiRecognizer(model, sample_rate, json.dumps(words))
    recognizer.SetWords(True)
    
    is_recording = False
    current_number = []

    with sd.RawInputStream(
        samplerate=sample_rate,
        blocksize=1600,
        dtype='int16',
        channels=1,
        callback=audio_callback
    ):
        while not stop_event.is_set():
            try:
                data = audio_queue.get(timeout=0.5)
                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    
                    if 'result' in result:
                        for word_info in result['result']:
                            if word_info['conf'] >= MIN_CONFIDENCE:
                                word = word_info['word']
                                
                                if not is_recording:
                                    if word == "start":
                                        is_recording = True
                                        current_number = []
                                        print("\nRecording started...")
                                else:
                                    if word == "stop":
                                        number_str = ''.join(current_number)
                                        print(f"\nFinal number: {number_str}")
                                        is_recording = False
                                        current_number = []
                                    elif word in WORD_MAP:
                                        current_number.append(WORD_MAP[word])
                                        print(f"Current: {''.join(current_number)}", end='\r')

            except queue.Empty:
                continue

def fan_control():
    while not stop_event.is_set():
        fan.on()

if __name__ == "__main__":
    try:
        recognizer_thread = Thread(target=recognize)
        fan_thread = Thread(target=fan_control)

        recognizer_thread.start()
        fan_thread.start()

        recognizer_thread.join()
        fan_thread.join()

    except KeyboardInterrupt:
        stop_event.set()
        fan.off()
        fan.close()
        print("\nStopped listening and turned off fan")
