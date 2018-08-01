#!/usr/bin/python3
# -*- coding: utf-8 -

from pynput import keyboard
import schedule
import time
import datetime
import logging
import threading
#from RPi.GPIO import GPIO
from RPiSim.GPIO import GPIO


def listen_keyboard(stop_event):
    def on_press(key):
        if key == keyboard.Key.f1:
            try:
                logging.info("Enclenchement manuel chauffage zone 1")
                GPIO.output(4,GPIO.HIGH)
            except:
                logging.error("Erreur de communication avec GPIO ?")

        if key == keyboard.Key.f2:
            try:
                logging.info("Enclenchement manuel chauffage zone 2")
                GPIO.output(5,GPIO.HIGH)
            except:
                logging.error("Erreur de communication avec GPIO ?")

        if key == keyboard.Key.f4:
            logging.info("Activation du programme pour la routine volet")
            stop_event.clear()
            shutter_thread = threading.Thread(name="volet", target=routine_volet, args=(stop_event,))
            shutter_thread.start()
        if key == keyboard.Key.f5:
            logging.info("Arrêt du programme pour la routine volet")
            stop_event.set()

    def on_release(key):
        if key == keyboard.Key.f1:
            # Délai avant d'arrêter le chauffage
            time.sleep(5)
            logging.info("Arrêt procédure manuelle chauffage zone 1")
            GPIO.output(4,GPIO.LOW)
        if key == keyboard.Key.f2:
            # Délai avant d'arrêter le chauffage
            time.sleep(5)
            logging.info("Arrêt procédure manuelle chauffage zone 2")
            GPIO.output(5,GPIO.LOW)

    with keyboard.Listener(on_press=on_press,on_release=on_release) as listener:
        listener.join()

def routine_volet(stop_event):
    def ouverture():
        logging.info("Ouverture volet")
        GPIO.output(6,GPIO.HIGH)
        #time.sleep(30) # durée d'ouverture
        time.sleep(5) # pour les tests
        GPIO.output(6,GPIO.LOW)
        return
    def fermeture():
        logging.info("Fermeture volet")
        GPIO.output(7,GPIO.HIGH)
        #time.sleep(30) # durée d'ouverture
        time.sleep(5) # pour les tests
        GPIO.output(7,GPIO.LOW)
        return

    my_sched = schedule.Scheduler()
    # Ouvrir le volet tous les jours à 11h
    #my_sched.every().day.at("11:00").do(ouverture)
    # Fermer le volet tous les jours à 19h
    #my_sched.every().day.at("19:00").do(fermeture)
    my_sched.every(10).seconds.do(ouverture)

    while True:
        if not stop_event.is_set():
            my_sched.run_pending()
            time.sleep(0.5)
        else:
            my_sched.clear()
            return

def routine_chauffage():
    def job():
        logging.info("Enclenchement chauffage zones 1 et 2 pour 1h")
        GPIO.output(4,GPIO.HIGH)
        GPIO.output(5,GPIO.HIGH)
        # Durée de la procédure en secondes : 7200 (2h)
        # Pour les tests 5 sec
        time.sleep(100)
        GPIO.output(4,GPIO.LOW)
        GPIO.output(5,GPIO.LOW)
        return

    #TODO : deux routines différentes → semaine/week-end
    my_sched = schedule.Scheduler()
    my_sched.every(500).seconds.do(job)
    #Enclencher le chauffage tous les jours à 5h30
    #my_sched.every().day.at("05:30").do(job)

    while True:
        my_sched.run_pending()
        time.sleep(1)

if __name__ == "__main__":

    logging.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s', level=logging.INFO)

    '''
    # Zone 1
    Type : Salon
    Broche GPIO : 4
    Horaires chauffage :
    - Semaine : 5h30-7h30
    - Week-end : 7h30-9h30

    # Zone 2
    Type : Salle de bains
    Broche GPIO : 5
    Horaires chauffage :
    - Semaine : 5h30-7h30 puis 19h00-21h00
    - Week-end : 7h30-9h30

    # Routine volet
    - ouverture : 11h00 / Broche GPIO : 6
    - fermeture : 19h00 / Broche GPIO : 7
    '''

    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(4, GPIO.OUT, initial = GPIO.LOW)
    GPIO.setup(5, GPIO.OUT, initial = GPIO.LOW)
    GPIO.setup(6, GPIO.OUT, initial = GPIO.LOW)
    GPIO.setup(7, GPIO.OUT, initial = GPIO.LOW)

    stop_event = threading.Event()
    heating_thread = threading.Thread(target=routine_chauffage, name="heating")
    keyboard_thread = threading.Thread(target=listen_keyboard, name="keyboard", args=(stop_event,))
    heating_thread.start()
    logging.info("Routine chauffage enclenchée")
    keyboard_thread.start()
    logging.info("Programme d'écoute du clavier pour instructions manuelles enclenché")
