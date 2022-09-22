# HyperPixel Dress

## Setup Notes

### Raspberry Pi 4

#### Hardware

* Connect Pi Camera to Raspberry Pi 4
* Connect HyperPixel to Raspberry pi 4

#### Operating System Setup

* Download the [Raspberry Pi Image](https://www.raspberrypi.com/software/)
* Burn Raspberri Pi OS Lite (Legacy) (Buster) to a micro SD card
* Connect keyboard, mouse, and monitor (e.g. HDMI)
  * Adjust *boot/config.txt* as needed to support your monitor
  * Note: if you do not have a keyboard, mouse, and monitor, you can do an [Ethernet headless setup](https://nrsyed.com/2021/06/02/raspberry-pi-headless-setup-via-ethernet-and-how-to-share-the-host-pcs-internet-connection/)
* Login with default username (pi) and password (raspberry)
* Run config:

```
sudo raspi-config
```

* Configure the following:
  * Connect to WiFi (can disable WiFi after we install everything)
  * Change password (recommended)
  * Enable camera interface (if using Pi Cam)
  * Enable SSH
  * Enable I2C
  * Localization: 
    * Remove en_GB.UTF-8 and add en_US.UTF-8
    * Set default to en_US.UTF-8
  * Set timezone
  * Set keyboard to Generic 105-key, English (US)
  * Set Wireless LAN country to US
  * Save and reboot

#### Install Dependencies

Install dependencies:

```
sudo apt update
sudo apt install -y mc git python3-pip libsdl2-ttf-2.0-0 libsdl2-image-2.0-0 libsdl2-2.0-0 i2c-tools
```

#### Install HyperPixel 2" Round drivers

Install display driver:

```
mkdir -p ~/Projects/GitHub
cd ~/Projects/GitHub
git clone https://github.com/pimoroni/hyperpixel2r
cd hyperpixel2r
sudo ./install.sh
```

Disable the default touch driver for the HyperPixel

```
sudo nano /boot/config.txt
```

Scroll down and change the dtoverlay line to the following:

```
dtoverlay=hyperpixel2r:disable-touch
```

At the bottom, add the following:

```
# Force 640x480 video for Pygame / HyperPixel2r
hdmi_force_hotplug=1
hdmi_mode=1
hdmi_group=1
```

Save and exit. Shut down:

```
sudo shutdown now
```

Unplug your primary monitor! It will no longer work (and a DSI monitor might interfere with the HyperPixel). Turn your Pi back on.

Upgrade pip and install Python packages:

```
python3 -m pip install --upgrade pip
sudo python3 -m pip install hyperpixel2r pygame
```

#### Test HyperPixel

Create a place to store the tests:

```
mkdir -p ~/Projects/HyperPixel
cd ~/Projects/HyperPixel
nano pygame-display-test.py
```

Copy the code from *tests/pygame-display-test.py* into *~/Projects/HyperPixel/pygame-display-test.py*. Run it with:

```
sudo python3 pygame-display-test.py
```

You should see "PyGame Draw Test" printed on the screen.
