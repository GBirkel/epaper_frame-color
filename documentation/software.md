# Fancy e-paper photo frame

### A project to build a nice 10.3-inch grayscale e-paper picture frame that updates once a day.

* [Overview](../README.md)
* [Materials List](materials.md)
* [Construction And Wiring](construction.md)
* [Software](software.md)

# Software:

This section assumes you've already got your Raspberry Pi booting in to an OS on the media card, and can `ssh` into it.  Check the [Construction](construction.md) section for details on using the [Raspberry Pi OS imager](https://www.raspberrypi.com/software/).

Here's a list of commands I entered to customize the system and get it ready.  You may not need all of these.

### Generally a good idea to install any recent updates:
```sh
sudo apt-get upgrade
```

### Set up an `.ssh` folder for storing authorized keys:
For when you didn't set it up using the [Pi OS imager](https://www.raspberrypi.com/software/) app.
```sh
mkdir .ssh
chmod 700 .ssh
cd .ssh
touch authorized_keys
```

### Set up a local file server you can connect to from Windows or Mac:
```sh
sudo apt-get install samba samba-common-bin
sudo nano /etc/samba/smb.conf
```
In the editor, change the configuration file to make home directories writable, then save it.
```sh
sudo smbpasswd -a garote
sudo /etc/init.d/smbd restart
```
Swap `garote` for your username, of course.

At this point, if your computer is on the same wifi network, the Pi will magically appear as a file server in the network section.  Log in using your admin credentials.

### Installing and updating the PiSugar driver:
```sh
wget https://cdn.pisugar.com/release/pisugar-power-manager.sh
bash pisugar-power-manager.sh -c release
rm pisugar-power-manager.sh
curl https://cdn.pisugar.com/release/PiSugarUpdate.sh | sudo bash
```
You might want to set `auto_power_on` to `true`:
```sh
sudo pico /etc/pisugar-server/config.json
```
Once this was installed, I could immediately get to the PiSugar administrator interface at `http://pictureframe.local:8421/#/` .

### Turn on the Raspberry Pi SPI interface
```sh
sudo raspi-config
```
In the UI that appears, select:

* 3: Interface Options
* I4: SPI
* Yes

You'll need to restart the Pi after this to make the change stick.
```sh
sudo shutdown -r now
```

### Download, build, and run the e-paper display tests

Not strictly necessary but a good sanity check to make sure you have the display wired up right.

```sh
git clone https://github.com/waveshare/IT8951-ePaper.git
cd IT8951-ePaper/Raspberry/
sudo make clean
sudo make -j4
sudo ./epd -1.23 1
```

Note the last two numbers in that command that runs the program.  You may need a number different than `-1.23`.  See the `config.xml` section below for details.

### Get, build, and configure the software in this repo

There's stuff online about installing the Python RPi.GPIO Library, and how it can be tricky to get the right version to drive your display.  We're going to ignore all that, because we're going to be driving the display with a C program based heavily on the above demo code.

Clone this repository:

```sh
cd ~/Documents/
git clone https://github.com/GBirkel/epaper_frame.git
cd epaper_frame
```

Now build the C program:

```sh
cd IT8951_Utility
sudo make clear
sudo make -j4
cd ..
```

Now you need to customize the configuration file.

First run this, and note the output:

```sh
pwd
```

Then you can begin editing the file.

```sh
nano config.xml
```

You can also just connect to the file server from your computer and open the file in any editor you like, of course.

The file will look like this:

```xml
<?xml version="1.0"?>
<epaper>
    <installpath>/home/garote/Documents/epaper_frame/</installpath>
    <library>/home/garote/Pictures/frame/</library>
    <displaynumber>-1.23</displaynumber>
    <interval>86200</interval>
</epaper>
```

You need to edit the `installpath` section to match the full path of the folder you placed this code into.  The results of the `pwd` command above are what you'd put here.

Next is the `library` section.  This points to the folder on the drive where you intend to store all the images to send to the display.  (I made a subfolder in the standard `Pictures` folder and used that.)

The `displaynumber` section is where you put the display version number.  This can be found prited on a label attached somewhere on the ribbon cable assembly for the display.  For example, mine was here:

<a data-flickr-embed="true" href="https://www.flickr.com/photos/57897385@N07/54371888924/in/dateposted/" title="2025-02-17-180139-IMG_6001"><img src="https://live.staticflickr.com/65535/54371888924_c90ceda52a_z.jpg" style="width:70%;max-width:512px;" alt="2025-02-17-180139-IMG_6001"/></a>

Yours may be different, and possibly in a different place.

The `interval` value is the time in seconds that the frame should wait before powering itself up again.  By default it's set to just under 24 hours, to account for the time the program needs to run.

### Loading in pictures

Once you have a location set up for storing your pictures (`/home/garote/Pictures/frame/` in the above configuration), make one or more subfolders in there, and start adding pictures into the subfolders.  They should all be in the following format:

* PNG format
* Height: 1404 pixels
* Width: 1872 pixels

Beyond that, if you want greater control over exactly how the images are rendered, you may wish to convert them in advance to the following:

* Grayscale
* 16 shades of gray (black and white included)

There are various ways to do this conversion, including different kinds of dithering you can apply.  Left as an exercise to the reader!  (I used automated Photoshop actions.)

### Running the setup script

Once you've got a bunch of pictures in your subfolders, the program needs to index them.  The idea is, we do this once after adding pictures, so the program doesn't need to waste power re-indexing every time it starts.

```sh
cd ~/Documents/epaper_frame/
sudo python3 png_inventory.py
```

Expect a bunch of output that looks like this:

```
Opening local database: /home/garote/Documents/epaper_frame/images.db
Creating tables if needed
Fetching all image groups from database
Fetching all image groups from database
Group: cyclists (1)
Updating existing image cyclists/_8c8956f7-d280-40a9-9c72-ac585a27ae6c.png
Updating existing image cyclists/_4b9650ed-33f4-450c-b264-2b3bcd822cb4.png
Updating existing image cyclists/_bf04e2f1-4e0f-4949-a792-ede9af62d208.png
....
Updating existing image gibberish/_7af90056-170f-4fa7-a26b-0de1e9f81611.png
Updating existing image gibberish/_fbc3779c-72a0-4d37-9a59-d03d0801ea50.png
Fetching all image groups from database
Fetching all images from database
1111 images total, 0 new as of this scan.
```

### Enabling the service

Your last task is to run the script that registers the program as a service, so it launches when the Pi is powered on:

```sh
sudo python3 register_service.py
```

If you ever need to unregister it, just do this:

```sh
sudo python3 register_service.py -u
```

### A first run

To get the startup-shutdown cycle running, unplug the frame from external power (so the PiSugar is drawing from battery), then run the image cycling script once manually:

```sh
sudo ./cycle_image.py
```

After this first run finished, you'll be disconnected from your shell connection as the Pi powers down.

Return to:

# [Overview](../README.md)

