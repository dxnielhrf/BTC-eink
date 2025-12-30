# Zero BTC Screen

### Plattform

* Raspberry Pi Zero W
* Raspberry Pi 3b+
* Raspberry Pi 4
* Jeder andere moderne RPi

### Unterstützte Displays

* Waveshare eInk Typen:
  * epd2in13v2
  * epd2in13g
  * epd2in13v3
  * epd2in13bv3
  * epd2in7
  * epd3in7
* inkyWhat (Rot, Schwarz, Weiß)
* Virtuell (Bild)

## Installation

1. Aktiviere SPI über `sudo raspi-config`
    ```
    Interfacing Options -> SPI
    ```
2. Erlaube Systembrüche
   ```
    mkdir -p ~/.config/pip
    echo -e "[global]\nbreak-system-packages = true" >> ~/.config/pip/pip.conf
    ```

3. Installiere Abhängigkeiten
    ```
    sudo apt update
    sudo apt-get install python3-pip python3-numpy git
    pip3 install RPi.GPIO spidev pillow
    ```

4. Installiere Treiber für dein Display (du musst nicht beide installieren)
    1. Wenn du ein Waveshare-Display hast
    ```
    git clone https://github.com/waveshare/e-Paper.git ~/e-Paper
    pip3 install ~/e-Paper/RaspberryPi_JetsonNano/python/
    ```
    2. Wenn du ein Inky wHAT-Display hast
    ```
    pip3 install inky[rpi]
    ```
5. Lade BTC-eink herunter
    ```
    git clone https://github.com/dxnielhrf/BTC-eink.git ~/zero-btc-screen
    ```
6. Lass den Code laufen
    ```
    python3 ~/zero-btc-screen/main.py
    ```

## Bildschirmkonfiguration

Die Anwendung unterstützt mehrere Arten von e-Ink-Bildschirmen und einen zusätzlichen "Bild"-Bildschirm.

Die Displays können in der configuration.cfg angepasst werden.

```cfg
[base]
console_logs             : false
#logs_file                : /tmp/zero-btc-screen.log
dummy_data               : false
refresh_interval_minutes : 15
# Preis-Paar von Coinbase z.B. BTC-EUR oder ADA-GBP
currency                 : BTC-USD

# Aktivierte Bildschirme oder Geräte
screens : [
#    epd2in13v2
    epd2in13g
#    epd2in13v3
#    epd2in13bv3
#    epd2in7
#    epd3in7
#    picture
#    inkyWhatRBW
  ]

# Konfiguration pro Bildschirm
# Dies hat keine Auswirkungen, wenn die Bildschirme oben nicht aktiviert sind
[epd2in13g]
mode : candle

[epd2in13v2]
#mode : line
mode : candle

[epd2in13v3]
mode : candle

[epd2in13bv3]
mode : line

[epd2in7]
mode : candle

[epd3in7]
mode : candle

[picture]
filename : /home/pi/output.png
mode : candle

[inkyWhatRBW]
mode : candle
```

### Autostart

Um das Programm beim Hochfahren automatisch zu starten, hast du 2 Optionen:

1. Verwendung des Systemd-Service-Daemons
    1. Erstelle eine neue Service-Konfigurationsdatei
       ```
        sudo nano /etc/systemd/system/btc-screen.service
        ```
    2. Kopiere und füge Folgendes in die Service-Konfigurationsdatei ein und passe die Einstellungen an deine Umgebung an
       ```
        [Unit]
        Description=zero-btc-screen
        After=network.target
 
        [Service]
        ExecStart=/usr/bin/python3 -u main.py
        WorkingDirectory=/home/pi/zero-btc-screen
        StandardOutput=inherit
        StandardError=inherit
        Restart=always
        User=pi
 
        [Install]
        WantedBy=multi-user.target
        ```
    3. Aktiviere den Service, damit er beim Neustart des RPi automatisch startet
       ```
        sudo systemctl enable btc-screen.service
       ```
    4. Starte den Service und viel Spaß!
       ```
        sudo systemctl start btc-screen.service
       ```

       Falls du Probleme beheben musst, kannst du die Logging-Konfigurationen dieses Programms verwenden (siehe unten).
       Alternativ kannst du die Systemd-Service-Logs überprüfen.
       ```
        sudo journalctl -f -u btc-screen.service
       ```

### LEDs

Um die LEDs beim Raspberry Pi 3b zu deaktivieren, musst du folgende Schritte befolgen:

1. Öffne die config.txt
    ```
    sudo nano /boot/firmware/config.txt
    ```

2. Ergänze ganz unten folgenden Abschnitt
    ```
    # Power-LED ausschalten
    dtparam=pwr_led_trigger=default-on
    dtparam=pwr_led_activelow=off
    # Aktivitäts-LED ausschalten
    dtparam=act_led_trigger=none
    dtparam=act_led_activelow=off
    # Ethernet-ACT-LED ausschalten
    dtparam=eth_led0=14
    # Ethernet-LNK-LED ausschalten
    dtparam=eth_led1=14
    ```

3. Speichern und Neustarten.

