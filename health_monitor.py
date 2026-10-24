import time
from cache import is_alive

def monitor(stop_event=None):
    offline_alert_sent = False

    while stop_event is None or not stop_event.is_set():
        if is_alive():
            offline_alert_sent = False
        elif not offline_alert_sent:
            print("Bot offline detected")
            offline_alert_sent = True

        if stop_event is None:
            time.sleep(600) #sleep for 10 minutes
        elif stop_event.wait(600):
            break
