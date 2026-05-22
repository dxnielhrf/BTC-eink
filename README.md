# Zero BTC Screen

### Plattform

| Modell | Getestet | Hinweis |
|---|---|---|
| Raspberry Pi Zero 2 W | ✓ | Empfohlen für Dauerbetrieb — kompakt, stromsparend |
| Raspberry Pi Zero W | ✓ | Funktioniert, langsamer bei PIL-Konvertierung |
| Raspberry Pi 3B+ | ✓ | |
| Raspberry Pi 4 | ✓ | |
| Raspberry Pi 5 | — | Sollte funktionieren, nicht explizit getestet |

Benötigt: SPI-fähiger Pi mit Raspbian/Raspberry Pi OS (Bookworm empfohlen).

### Unterstützte Displays

| Display | Typ | Farben | Treiber |
|---|---|---|---|
| Waveshare epd2in13g | 2,13" e-Paper | Schwarz, Weiß, Rot, Gelb (4-Farb-Spectra) | `epd2in13g` |
| Waveshare epd2in13g V2 | 2,13" e-Paper | Schwarz, Weiß, Rot, Gelb (4-Farb-Spectra) | `epd2in13gv2` |
| Waveshare epd2in13v2 | 2,13" e-Paper | Schwarz, Weiß | `epd2in13v2` |
| Waveshare epd2in13v3 | 2,13" e-Paper | Schwarz, Weiß | `epd2in13v3` |
| Waveshare epd2in13bv3 | 2,13" e-Paper | Schwarz, Weiß, Rot | `epd2in13bv3` |
| Waveshare epd2in7 | 2,7" e-Paper | Schwarz, Weiß | `epd2in7` |
| Waveshare epd3in7 | 3,7" e-Paper | Schwarz, Weiß (4 Graustufen) | `epd3in7` |
| Pimoroni inkyWhat | 4,2" e-Paper | Schwarz, Weiß, Rot | `inkyWhatRBW` |
| Virtuell (Bild) | PNG-Ausgabe | — | `picture` |

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
    sudo apt-get install python3-pip python3-numpy python3-systemd git
    pip3 install RPi.GPIO spidev pillow requests
    ```
    `python3-systemd` wird nur benötigt, wenn der Watchdog (`Type=notify` + `WatchdogSec`) im systemd-Service genutzt wird. Fehlt das Paket, läuft das Programm trotzdem, dann aber ohne Watchdog-Heartbeat.

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

## Konfiguration

Alle Einstellungen in `configuration.cfg` im Repo-Verzeichnis:

```cfg
[base]
console_logs             : false
#logs_file                : /tmp/zero-btc-screen.log
dummy_data               : false
refresh_interval_minutes : 30
# Preis-Paar von Coinbase z.B. BTC-EUR oder ADA-GBP
currency                 : BTC-USD

# Aktiviertes Display — nur eines gleichzeitig einkommentieren
screens : [
#    epd2in13v2
#    epd2in13g
    epd2in13gv2
#    epd2in13v3
#    epd2in13bv3
#    epd2in7
#    epd3in7
#    picture
#    inkyWhatRBW
  ]

# Darstellungsmodus pro Display: "candle" (Kerzendiagramm) oder "line" (Linienchart)
[epd2in13gv2]
mode : candle

[epd2in13g]
mode : candle

[epd2in13v2]
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

**Wichtige Parameter:**

| Parameter | Standard | Beschreibung |
|---|---|---|
| `refresh_interval_minutes` | 30 | Wie oft das Display aktualisiert wird |
| `currency` | BTC-USD | Coinbase-Handelspaar (z.B. `BTC-EUR`, `ETH-USD`) |
| `dummy_data` | false | `true` = keine echten API-Calls, für Tests |
| `console_logs` | false | `true` = Logs auch in der Konsole ausgeben |
| `mode` | candle | `candle` = Kerzendiagramm, `line` = Linienchart |

### Autostart

Um das Programm beim Hochfahren automatisch zu starten, hast du folgende Option:

1. Stelle sicher, dass Repo und Dependencies aktuell sind
    ```bash
    cd ~/zero-btc-screen
    git pull origin main
    sudo apt-get update && sudo apt-get install -y python3-systemd
    pip3 install requests
    ```

2. Erstelle eine neue Service-Konfigurationsdatei
    ```bash
    sudo nano /etc/systemd/system/btc-screen.service
    ```

3. Kopiere und füge Folgendes in die Service-Konfigurationsdatei ein und passe die Einstellungen an deine Umgebung an
       ```
        [Unit]
        Description=zero-btc-screen
        After=network.target

        [Service]
        Type=notify
        ExecStart=/usr/bin/python3 -u main.py
        WorkingDirectory=/home/pi/zero-btc-screen
        StandardOutput=inherit
        StandardError=inherit
        Restart=always
        RestartSec=10
        WatchdogSec=90
        User=pi

        [Install]
        WantedBy=multi-user.target
        ```

       **Hinweis zu `Type=notify` und `WatchdogSec`:**
       Das Programm sendet `READY=1` beim Start und danach alle 30 Sekunden einen `WATCHDOG=1`-Heartbeat über einen Hintergrund-Thread — unabhängig vom Display-Refresh-Intervall. `WatchdogSec=90` bedeutet: systemd killt + restartet automatisch, wenn 3 aufeinanderfolgende Pings ausbleiben (also ~90s Hänger). Fehlt `python3-systemd`, läuft das Programm trotzdem — nur ohne Watchdog.

4. Aktiviere den Service, damit er beim Neustart des RPi automatisch startet
    ```bash
    sudo systemctl enable btc-screen.service
    ```

5. Starte den Service
    ```bash
    sudo systemctl start btc-screen.service
    ```

    Logs live verfolgen:
    ```bash
    sudo journalctl -f -u btc-screen.service
    ```

       **Troubleshooting systemd/Watchdog:**
       - Service startet nicht mit `Type=notify` → `python3 -c "import systemd.daemon"` testen. Fehler = Paket fehlt. Fix: `sudo apt-get install python3-systemd` oder `Type=notify` → `Type=simple` + `WatchdogSec` entfernen.
       - Bei WLAN-Ausfall: Programm loggt `Fetch failed, retrying in Xs` mit exponentiellem Backoff (5s → 10s → ... → 5min). Kein Absturz, kein Kill durch systemd.
       - Display hängt im Busy-State: Treiber bricht nach 30s ab mit Warning in den Logs, Refresh-Loop läuft weiter.

### Powersave (Headless Pi Zero 2 W)

Für Dauerbetrieb ohne Monitor. Alle Punkte beeinflussen das Display-Bild **nicht**.

**1. HDMI dauerhaft ausschalten**

```bash
sudo nano /etc/systemd/system/hdmi-off.service
```
```ini
[Unit]
Description=Turn off HDMI output to save power
After=multi-user.target

[Service]
Type=oneshot
ExecStart=/usr/bin/vcgencmd display_power 0
RemainAfterExit=yes
ExecStop=/usr/bin/vcgencmd display_power 1

[Install]
WantedBy=multi-user.target
```
```bash
sudo systemctl enable --now hdmi-off.service
```
Ersparnis: ~25–30 mA.

**2. Bluetooth ausschalten**

```bash
echo "dtoverlay=disable-bt" | sudo tee -a /boot/firmware/config.txt
sudo systemctl disable hciuart bluetooth
```
Ersparnis: ~30 mA.

**3. WLAN Powersave**

```bash
sudo mkdir -p /etc/NetworkManager/conf.d
echo -e "[connection]\nwifi.powersave = 3" | sudo tee /etc/NetworkManager/conf.d/wifi-powersave.conf
sudo systemctl restart NetworkManager
```
Verify: `iw dev wlan0 get power_save` → `Power save: on`. Ersparnis: ~10–30 mA.

**4. ACT-LED ausschalten (Pi Zero 2 W)**

In `/boot/firmware/config.txt` am Ende ergänzen:
```
dtparam=act_led_trigger=none
dtparam=act_led_activelow=off
```
Ersparnis: ~5 mA.

**5. Was nicht empfohlen wird**

- `cpufreq-set -g powersave`: Pi Zero 2 W braucht Rechenleistung für PIL/Image-Convert beim Refresh. `ondemand` (Standard) ist optimal.
- `epd.sleep()` pro Refresh: Unterbricht Waveform-Settle-Phase → Schwarz wird Grau auf 4-Farb-Spectra-Panels. Nur `close()` ruft `sleep()` auf.

**Gesamtersparnis Pi Zero 2 W**

| Maßnahme | Ersparnis |
|---|---|
| HDMI aus | ~25 mA |
| Bluetooth aus | ~30 mA |
| WLAN Powersave | ~15 mA |
| LED aus | ~5 mA |
| **Gesamt** | **~75 mA** (~0.38 W statt ~0.75 W) |

Nach allen Änderungen neu starten:
```bash
sudo reboot
```
Verify:
```bash
vcgencmd display_power          # → display_power=0
iw dev wlan0 get power_save     # → Power save: on
sudo systemctl status hdmi-off btc-screen
```
