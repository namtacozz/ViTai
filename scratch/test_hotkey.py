from pynput import keyboard
import time

def on_activate():
    print('Activated!')

h = keyboard.GlobalHotKeys({'<alt>+q': on_activate})
h.start()
time.sleep(3)
h.stop()
