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

DUREE_OUVERTURE_VOLET = 30
DUREE_FERMETURE_VOLET = 30
DUREE_ENCLENCHEMENT_CHAUFFAGE_MANUEL = 3600 #1h
DUREE_ENCLENCHEMENT_CHAUFFAGE_AUTO = 7200 #2h
HORAIRE_ENCLENCHEMENT_CHAUFFAGE_SEMAINE_ZONE_1 = "05:30"
HORAIRE_ENCLENCHEMENT_CHAUFFAGE_WE_ZONE_1 = "07:30"
HORAIRE_ENCLENCHEMENT_CHAUFFAGE_SEMAINE_ZONE_2_MATIN = "05:30"
HORAIRE_ENCLENCHEMENT_CHAUFFAGE_SEMAINE_ZONE_2_SOIR = "19:00"
HORAIRE_ENCLENCHEMENT_CHAUFFAGE_WE_ZONE_2 = "07:30"
HORAIRE_OUVERTURE_ROUTINE_VOLET = "11:00"
HORAIRE_FERMETURE_ROUTINE_VOLET = "19:00"
BROCHE_GPIO_CHAUFFAGE_ZONE_1 = 4
BROCHE_GPIO_CHAUFFAGE_ZONE_2 = 5
BROCHE_GPIO_OUVERTURE_VOLET = 6
BROCHE_GPIO_FERMETURE_VOLET = 7

def listen_keyboard(stop_event):
    def on_press(key):
        if key == keyboard.Key.f1:
            try:
                logging.info("Enclenchement manuel chauffage zone 1")
                heating_thread = threading.Thread(target=chauffage_manuel, args=(1,))
                heating_thread.start()
            except:
                logging.error("Erreur de communication avec GPIO ?")

        if key == keyboard.Key.f2:
            try:
                logging.info("Enclenchement manuel chauffage zone 2")
                heating_thread = threading.Thread(target=chauffage_manuel, args=(2,))
                heating_thread.start()
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

    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

def routine_volet(stop_event):
    def ouverture():
        logging.info("Ouverture volet")
        GPIO.output(BROCHE_GPIO_OUVERTURE_VOLET,GPIO.HIGH)
        time.sleep(DUREE_OUVERTURE_VOLET) # durée d'ouverture
        GPIO.output(BROCHE_GPIO_OUVERTURE_VOLET,GPIO.LOW)
        return
    def fermeture():
        logging.info("Fermeture volet")
        GPIO.output(BROCHE_GPIO_FERMETURE_VOLET,GPIO.HIGH)
        #time.sleep(30) # durée d'ouverture
        time.sleep(DUREE_FERMETURE_VOLET) # pour les tests
        GPIO.output(BROCHE_GPIO_FERMETURE_VOLET,GPIO.LOW)
        return

    my_sched = schedule.Scheduler()
    # Ouvrir le volet tous les jours à 11h
    my_sched.every().day.at(HORAIRE_OUVERTURE_ROUTINE_VOLET).do(ouverture).tag('routine-volet-ouverture')
    # Fermer le volet tous les jours à 19h
    my_sched.every().day.at(HORAIRE_FERMETURE_ROUTINE_VOLET).do(fermeture).tag('routine-volet-fermeture')
    #my_sched.every(10).seconds.do(ouverture)

    while True:
        if not stop_event.is_set():
            my_sched.run_pending()
            time.sleep(0.5)
        else:
            my_sched.clear()
            return

def routine_chauffage():
    def chauffage_auto(zone):
        # Vérifier jour de la semaine
        today = datetime.datetime.today()
        weekday = today.weekday() #0 (lundi) à 6 (dimanche)
        hour = today.hour
        if ( (weekday in range(4) and hour in [5,19]) or (weekday in [5,6] and hour == 7) ):
            logging.info("Enclenchement chauffage zone %s pour 2h", zone)
            if zone == 1:
                broche = BROCHE_GPIO_CHAUFFAGE_ZONE_1
            else:
                broche = BROCHE_GPIO_CHAUFFAGE_ZONE_2
            GPIO.output(broche,GPIO.HIGH)
            # Durée de la procédure en secondes : 7200 (2h)
            time.sleep(DUREE_ENCLENCHEMENT_CHAUFFAGE_AUTO)
            GPIO.output(broche,GPIO.LOW)
            return
        else:
            return

    #TODO : deux routines différentes → semaine/week-end
    my_sched = schedule.Scheduler()
    #Pour les tests
    #my_sched.every(10).seconds.do(job)
    #Enclencher le chauffage tous les jours à 5h30
    schedule.every().day.at(HORAIRE_ENCLENCHEMENT_CHAUFFAGE_SEMAINE_ZONE_1).do(chauffage_auto, 1)
    schedule.every().day.at(HORAIRE_ENCLENCHEMENT_CHAUFFAGE_SEMAINE_ZONE_2_MATIN).do(chauffage_auto, 2)
    schedule.every().day.at(HORAIRE_ENCLENCHEMENT_CHAUFFAGE_SEMAINE_ZONE_2_SOIR).do(chauffage_auto, 2)
    schedule.every().day.at(HORAIRE_ENCLENCHEMENT_CHAUFFAGE_WE_ZONE_1).do(chauffage_auto, 1)
    schedule.every().day.at(HORAIRE_ENCLENCHEMENT_CHAUFFAGE_WE_ZONE_2).do(chauffage_auto, 2)

    while True:
        my_sched.run_pending()
        time.sleep(1)

def chauffage_manuel(zone):
    if zone == 1:
        broche = BROCHE_GPIO_CHAUFFAGE_ZONE_1
    else:
        broche = BROCHE_GPIO_CHAUFFAGE_ZONE_2
    GPIO.output(broche,GPIO.HIGH)
    time.sleep(DUREE_ENCLENCHEMENT_CHAUFFAGE_MANUEL)
    GPIO.output(broche,GPIO.LOW)
    return


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
    GPIO.setup(BROCHE_GPIO_CHAUFFAGE_ZONE_1, GPIO.OUT, initial = GPIO.LOW) # Chauffage zone 1
    GPIO.setup(BROCHE_GPIO_CHAUFFAGE_ZONE_2, GPIO.OUT, initial = GPIO.LOW) # Chauffage zone 2
    GPIO.setup(BROCHE_GPIO_OUVERTURE_VOLET, GPIO.OUT, initial = GPIO.LOW) # Ouverture volet
    GPIO.setup(BROCHE_GPIO_FERMETURE_VOLET, GPIO.OUT, initial = GPIO.LOW) # Fermeture volet

    stop_event = threading.Event()
    heating_thread = threading.Thread(target=routine_chauffage, name="heating")
    keyboard_thread = threading.Thread(target=listen_keyboard, name="keyboard", args=(stop_event,))
    heating_thread.start()
    logging.info("Routine chauffage enclenchée")
    keyboard_thread.start()
    logging.info("Programme d'écoute du clavier pour instructions manuelles enclenché")
