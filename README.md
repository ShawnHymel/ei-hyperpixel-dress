# HyperPixel Dress

## Setup Notes

[Multiple Pi Zeros connected to a single Pi host guide](http://raspberryjamberlin.de/zero360-part-2-connecting-via-otg-a-cluster-of-raspberry-pi-zeros-to-a-pi-3/)

### Raspberry Pi 4

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
sudo apt install -y mc git python3-pip
```

#### Edge Impulse Setup

Install dependencies (we need the Edge Impulse tools to be in sudo):

```
sudo apt install -y libatlas-base-dev libportaudio0 libportaudio2 libportaudiocpp0 portaudio19-dev gcc g++ make build-essential nodejs sox gstreamer1.0-tools gstreamer1.0-plugins-good gstreamer1.0-plugins-base gstreamer1.0-plugins-base-apps python-pyaudio libopenjp2-7 python-opencv python3-picamera
sudo python3 -m pip install pyaudio
sudo python3 -m pip install edge_impulse_linux -i https://pypi.python.org/simple
```

Install node.js:

```
curl -sL https://deb.nodesource.com/setup_14.x | sudo -E bash -
sudo apt-get install -y nodejs
node -v
```

Verify node installation directory:

```
npm config get prefix
```

If it returns */usr/local/*, run the following commands to change npm's default directory:

```
mkdir ~/.npm-global
npm config set prefix '~/.npm-global'
echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.profile
```

Install CLI tools:

```
npm config set user root && sudo npm install edge-impulse-linux -g --unsafe-perm
```

Download model file. Sign in with your Edge Impulse credentials when prompted. Select the **MobileNet-SSD: Face Detection 320x320 RGB** project.

```
cd ~/Projects/HyperPixel/
sudo edge-impulse-linux-runner --clean --download mobilenet-ssd-face.eim
```

#### Test face detection with static inference

Copy *tests/ei-face-static-test.py* and *tests/static-features.txt* to the *~/Projects/HyperPixel/* directory:

```
wget https://raw.githubusercontent.com/ShawnHymel/ei-hyperpixel-dress/main/tests/ei-face-static-test.py
wget https://raw.githubusercontent.com/ShawnHymel/ei-hyperpixel-dress/main/tests/static-features.txt
```

Run the test with:

```
sudo python3 ei-face-static-test.py mobilenet-ssd-face.eim static-features.txt
```

#### Configure Network

Create a udev rule:

```
sudo nano /etc/udev/rules.d/90-pi0network.rules
```

Add the following (one line for each Pi Zero expected to be connected):

```
SUBSYSTEM=="net", ATTR{address}=="00:22:82:ff:ff:02", NAME="usbpi2"
SUBSYSTEM=="net", ATTR{address}=="00:22:82:ff:ff:03", NAME="usbpi3"
```


Create a static ethernet IP address by modifying the dhcpd.conf file:

```
sudo nano /etc/dhcpcd.conf
```

Add the following:

```
# Assign static IP addresses for the USB connected Pi Zeros
interface usbpi2
static ip_address=192.168.2.1/24

interface usbpi3
static ip_address=192.168.3.1/24
```

#### Configure to Run Server on Boot

Copy the contents of *server-ssd.py* to *~/Projects/HyperPixel/server-ssd.py*.

Test it by running the following while the server is running:

```
sudo python3 server-ssd.py
```

Exit by pressing *ctrl + c*.

Create a new systemd service file:

```
sudo nano /lib/systemd/system/facedress-server.service
```

Enter the following:

```
[Unit]
Description=Server that performs face detection and sends images to clients
After=multi-user.target network.target

[Service]
ExecStart=/usr/bin/python3 /home/pi/Projects/HyperPixel/server-ssd.py

[Install]
WantedBy=multi-user.target
```

Save and exit. Reload the service file, and tell Linux to run it on boot:

```
sudo systemctl daemon-reload
sudo systemctl enable facedress-server.service
```

Reboot:

```
sudo reboot
```

Some commands to help troubleshoot the systemd service:

```
systemctl status facedress-server.service
sudo systemctl stop facedress-server.service
sudo systemctl start facedress-server.service
```

### Raspberry Pi Zero W

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

Pick a value for `x` (must be 2 or higher). Use this value wherever you see `x`.

* Configure the following:
  * Connect to WiFi (can disable WiFi after we install everything)
  * Change password (recommended)
  * Change hostname (to something like `pi0-x` where `x` is 2, 3, etc.; must be unique from other Pis on the network)
  * Enable SSH
  * Enable I2C
  * Localization: 
    * Remove en_GB.UTF-8 and add en_US.UTF-8
    * Set default to en_US.UTF-8
  * Set timezone
  * Set keyboard to Generic 105-key, English (US)
  * Set Wireless LAN country to US
  * Save and reboot

#### Enable USB Ethernet Gadget

Modify config.txt:

```
sudo nano /boot/config.txt
```

Add the following at the bottom:

```
# Enable USB gadget
dtoverlay=dwc2
```

Save and exit. Modify cmdline.txt:

```
sudo nano /boot/cmdline.txt
```

Scroll to the end of the line. Add a space and append the following (change the 'x' to match your Pi Zero number!):

```
modules-load=dwc2,g_ether g_ether.host_addr=00:22:82:ff:ff:0x g_ether.dev_addr=00:22:82:ff:ff:1x
```

Save and exit. Create a static ethernet IP address by modifying the dhcpd.conf file:

```
sudo nano /etc/dhcpcd.conf
```

Add the following. Change `x` to the desired number for your Pi Zero (leave 1 for the Pi 4, so you should use 2+ for `x`).

```
# Assign static IP address to USB ethernet gadget--change x!
interface usb0
static ip_address=192.168.x.2/24
```

Save and exit. Shutdown:

```
sudo shutdown now
```

Remove all USB cables. Connect a micro USB cable from the OTG port to the Raspberry Pi 4.

**NOTE:** Only the USB 3.0 (blue) ports on the Pi 4 seem to be working to provide a network connection at this time.

You should be able to SSH into the Pi Zero from the Pi 4 (where `x` is the x you chose earlier):

```
ssh -p 22 pi@192.168.7.x
```

#### Install OpenCV

Install some dependencies:

```
sudo apt update
sudo apt install -y libatlas-base-dev libhdf5-dev libatlas-base-dev libjasper-dev libqtgui4 libqt4-test libsdl2-ttf-2.0-0 libsdl2-image-2.0-0 libsdl2-2.0-0 i2c-tools libopenjp2-7 git python3-pip python3-opencv
```

Run the following:

```
sudo python3 -m pip install opencv-python
```

This will take a while...like an hour or two. So, be patient.

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

Scroll down and change the HyperPixel dtoverlay line to the following:

```
dtoverlay=hyperpixel2r:disable-touch
```

At the bottom, add the following:

```
# Define framebuffer size for HyperPixel2r
framebuffer_width=480
framebuffer_height=480

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

#### Test HyperPixel with Static Image

Download an image and test script:

```
mkdir -p ~/Projects/HyperPixel/
cd ~/Projects/HyperPixel/
wget https://upload.wikimedia.org/wikipedia/commons/thumb/b/bd/Test.svg/620px-Test.svg.png -O image.png
wget https://raw.githubusercontent.com/ShawnHymel/ei-hyperpixel-dress/main/tests/img-display-test.py
```

Run it with:

```
sudo python3 img-display-test.py
```

You should see a test pattern appear on the HyperPixel screen. It's OK if it's a little stretched.

#### Configure to Run Client on Boot

Copy the contents of *client.py* to *~/Projects/HyperPixel/client.py*.

Test it by running the following while the server is running:

```
sudo python3 client.py
```

Create a new systemd service file:

```
sudo nano /lib/systemd/system/facedress-client.service
```

Enter the following:

```
[Unit]
Description=Client to display images received over USB ethernet
After=multi-user.target network.target

[Service]
ExecStart=/usr/bin/python3 /home/pi/Projects/HyperPixel/client.py

[Install]
WantedBy=multi-user.target
```

Save and exit. Reload the service file, and tell Linux to run it on boot:

```
sudo systemctl daemon-reload
sudo systemctl enable facedress-client.service
```

Reboot:

```
sudo reboot
```

Some commands to help troubleshoot the systemd service:

```
systemctl status facedress-client.service
sudo systemctl stop facedress-client.service
sudo systemctl start facedress-client.service
```
