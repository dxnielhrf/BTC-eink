# Zero BTC Screen

### Plattform

* Raspberry Pi Zero W
* Raspberry Pi 3b+
* Raspberry Pi 4
* Any other modern RPi

### Unterstützte displays

* Waveshare eInk types:
  * epd2in13v2
  * epd2in13g
  * epd2in13v3
  * epd2in13bv3
  * epd2in7
  * epd3in7
* inkyWhat (Red, Black, White)
* Virtual (picture)

## Installation

1. Schalte an SPI via `sudo raspi-config`
    ```
    Interfacing Options -> SPI
   ```
2. Erlaube System breaks
   ```
    mkdir -p ~/.config/pip
echo -e "[global]\nbreak-system-packages = true" >> ~/.config/pip/pip.conf
    ```

3. Install dependencies
    ```
    sudo apt update
    sudo apt-get install python3-pip python3-numpy git
    pip3 install RPi.GPIO spidev pillow
    ```

4. Install drivers for your display (you don't need to install both)
    1. WEnn du ein Waveshare display hast
    ```
    git clone https://github.com/waveshare/e-Paper.git ~/e-Paper
    pip3 install ~/e-Paper/RaspberryPi_JetsonNano/python/
    ```
    2. Wenn du ein Inky wHAT display hast
    ```
    pip3 install inky[rpi]
    ```
5. Download BTC-eink
    ```
    git clone https://github.com/dxnielhrf/BTC-eink.git ~/zero-btc-screen
    ```
6. RLass den Code laufen
    ```
    python3 ~/zero-btc-screen/main.py
    ```


## Screen configuration

The application supports multiple types of e-ink screens, and an additional "picture" screen.

Die displays können in der condifuration.cfg angepasst werden

```cfg
[base]
console_logs             : false
#logs_file                : /tmp/zero-btc-screen.log
dummy_data               : false
refresh_interval_minutes : 15
# Price pair from Coinbase e.g. BTC-EUR or ADA-GBP
currency                 : BTC-USD

# Enabled screens or devices
screens : [
#    epd2in13v2
    epd2in12g
#    epd2in13v3
#    epd2in13bv3
#    epd2in7
#    epd3in7
#    picture
#    inkyWhatRBW
  ]

# Configuration per screen
# This doesn't make any effect if screens are not enabled above
[epd2in12g]
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
    2. Kopiere und füge folgendes in die Service-Konfigurationsdatei ein und passe die Einstellungen an deine Umgebung an
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

Um die LEDs beim Raspberry pi 3b zu dekativieren musst du folgende Schritte befolgen:

    1. Öffne die config.txt
        ```
        sudo nano /boot/firmware/config.txt
       ```

    2. Ergänze ganz unten folgenden Abschnitt
        ```
        # Turn off Power LED
        dtparam=pwr_led_trigger=default-on
        dtparam=pwr_led_activelow=off
        # Turn off Activity LED
        dtparam=act_led_trigger=none
        dtparam=act_led_activelow=off
        # Turn off Ethernet ACT LED
        dtparam=eth_led0=14
        # Turn off Ethernet LNK LED
        dtparam=eth_led1=14
        YAML
       ```

    3. Abspeichern und Neustarten