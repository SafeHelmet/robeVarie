from machine import Pin, I2C
import time
import math

# Indirizzo I2C del GY-521
GY521_ADDRESS = 0x68

# Registri del GY-521
PWR_MGMT_1 = 0x6B
ACCEL_XOUT_H = 0x3B
FS_SEL = 0x1C

# Soglia indicativa (in g e m/s²)
SOGLIA_INDICATIVA_G = 5  # Soglia iniziale indicativa in g
SOGLIA_INDICATIVA_MS2 = SOGLIA_INDICATIVA_G * 9.81

# Costanti per il calcolo statistico
FINESTRA_STATISTICA = 3  # Numero di campioni per il calcolo statistico
buffer_stat = []

# Funzione per inizializzare il GY-521
def init_gy521(i2c):
    i2c.writeto_mem(GY521_ADDRESS, PWR_MGMT_1, b'\x00')  # Imposta il sensore in modalità attiva
    i2c.writeto_mem(GY521_ADDRESS, FS_SEL, b'\x18')      # Imposta il range a ±16g

# Funzione per leggere i dati dell'accelerometro
def leggi_accelerometro(i2c):
    try:
        data = i2c.readfrom_mem(GY521_ADDRESS, ACCEL_XOUT_H, 6)
        
        # Assicurati che siano letti 6 byte
        if len(data) != 6:
            raise ValueError("Errore nella lettura dei dati dall'accelerometro.")
        
        # Funzione per combinare i byte MSB e LSB in un valore a 16 bit
        def converti_bytes(msb, lsb):
            valore = (msb << 8) | lsb
            if valore & 0x8000:
                valore -= 0x10000
            return valore
        
        accel_x = converti_bytes(data[0], data[1]) / 2048.0  # Converti in g
        accel_y = converti_bytes(data[2], data[3]) / 2048.0
        accel_z = converti_bytes(data[4], data[5]) / 2048.0
        return accel_x, accel_y, accel_z
    except Exception as e:
        print("Errore nella lettura:", e)
        return 0, 0, 0

# Calcolo modulo dell'accelerazione totale
def calcola_modulo(accel_x, accel_y, accel_z):
    return math.sqrt(accel_x**2 + accel_y**2 + accel_z**2)

# Funzione per salvare i dati in un file CSV
def salva_dati_csv(timestamp, accel_x, accel_y, accel_z, modulo, media, varianza, dev_std, modulo_max, modulo_min):
    try:
        with open("dataset_urti.csv", "a") as file:
            # Aggiunge i dati in formato tabellare
            file.write(f"{timestamp},{accel_x:.2f},{accel_y:.2f},{accel_z:.2f},{modulo:.2f},{media:.2f},{varianza:.2f},{dev_std:.2f},{modulo_max:.2f},{modulo_min:.2f}\n")
    except Exception as e:
        print("Errore durante il salvataggio:", e)

# Calcolo delle statistiche sui dati
def calcola_statistiche(buffer):
    n = len(buffer)
    if n == 0:
        return 0, 0, 0, 0
    media = sum(buffer) / n
    varianza = sum((x - media)**2 for x in buffer) / n
    dev_std = math.sqrt(varianza)
    modulo_max = max(buffer)
    modulo_min = min(buffer)
    return media, varianza, dev_std, modulo_max, modulo_min

# Funzione principale per la raccolta dati e crash detection
def raccolta_dati_e_crash_detection(i2c):
    global buffer_stat
    buffer_stat = []
    
    init_gy521(i2c)
    print("Sistema di raccolta dati avviato...")
    
    while True:
        try:
            # Leggi accelerazioni
            accel_x, accel_y, accel_z = leggi_accelerometro(i2c)
            modulo = calcola_modulo(accel_x, accel_y, accel_z)
            # VOLENDO SI POTREBBE FARE modulo * 9.81 -> m/s2
            
            # Aggiorna il buffer statistico
            buffer_stat.append(modulo)
            if len(buffer_stat) > FINESTRA_STATISTICA:
                buffer_stat.pop(0)
            
            # Calcola statistiche
            media, varianza, dev_std, modulo_max, modulo_min = calcola_statistiche(buffer_stat)
            
            # Ottieni il timestamp
            timestamp = time.ticks_ms()
            
            # Salva i dati nel file CSV
            # salva_dati_csv(timestamp, accel_x, accel_y, accel_z, modulo, media, varianza, dev_std, modulo_max, modulo_min)
            
            # Stampa informazioni utili
            print(f"T: {timestamp} ms | X: {accel_x:.2f} g, Y: {accel_y:.2f} g, Z: {accel_z:.2f} g | Modulo: {modulo:.2f} g")
            print(f"Media: {media:.2f}, Varianza: {varianza:.2f}, Dev standard: {dev_std:.2f}, Max: {modulo_max:.2f}, Min: {modulo_min:.2f}")
            
            # Crash detection basata sulla soglia indicativa
            if modulo > SOGLIA_INDICATIVA_G:
                print(f"Urto rilevato! Modulo: {modulo:.2f} g")
            
            time.sleep(0.05)  # Frequenza di campionamento: 20 Hz
        
        except OSError as e:
            print("Errore di comunicazione con il sensore:", e)
            time.sleep(1)

# Configurazione hardware e avvio
try:
    i2c = I2C(1, scl=Pin(22), sda=Pin(21))
    # Inizia la raccolta dati
    raccolta_dati_e_crash_detection(i2c)
except Exception as e:
    print("Errore durante l'inizializzazione:", e)
