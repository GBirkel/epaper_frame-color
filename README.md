# Fancy e-paper photo frame

### A project to build a nice 10.3-inch grayscale e-paper picture frame that updates once a day.

![Video of the frame in action, with cat for size](https://github.com/user-attachments/assets/2f5732ef-21fd-4f81-a468-279e1d1b35e0)

For years I've been intrigued by the unique aesthetics of e-paper displays.  A changeable surface that doesn't emit any light, and can display a static image without power?  Wouldn't this be great for showing art?

I'm a pretty decent programmer, but when it comes to hardware I'm a novice.  I own a soldering iron but I'm lousy at soldering.  This project went through a few iterations where I tried soldering wires directly onto things and the result was lumpy wires and burned spots on the components.  Eventually I hit on a design that didn't use any soldering at all, just some joining of wires with a crimping tool.  My squinty eyeballs and toasted fingers were grateful.

The software is in better shape.  Driving the e-paper display directly from Python on a Raspberry Pi is complicated, so I went with a sneaky approach:  I modified the freeware demo code published by the display manufacturer.  It's written in C, and all my version does is load an image from storage and send it to the display.

<a data-flickr-embed="true" href="https://www.flickr.com/photos/57897385@N07/54371918833/in/dateposted/" title="2025-03-06-174705-IMG_E6105"><img src="https://live.staticflickr.com/65535/54371918833_9c262918cf_z.jpg" style="width:70%;max-width:512px;" alt="2025-03-06-174705-IMG_E6105"/></a>

All the rest of the code is in Python, and I designed it to do the following:

* When the Raspberry Pi powers up, it checks to see if it's on battery power, or is charging from the USB-C cable.
* It picks one out of the 50% least-recently displayed images from a database on disk.
* It converts the image to Bitmap (BMP) format.
* It calls the C program to display the image, also passing along the current charge percentage of the battery, which is overlaid onto the image.
* If it's on battery power, it sets the PiSugar 3 "wake up" timer to a configured interval, makes sure the wifi driver is off, then powers everything back down.
* If it's charging, it turns on the wifi chip, so the device joins any nearby wifi networks it's already aware of.  Then it goes idle, staying on until someone manually shuts it down (or unplugs the cable and re-runs the Python script)

The history of what image was displayed, and when, and the battery state at the time, is written into the database.

Since I'm using the C program to drive the display, there is no Python display driver.  I'm also driving the PiSugar 3 directly with bus commands, so there's no need to use the PiSugar 3 driver or interface service either.

There are two support scripts included as well:

* `png_inventory.py` scans through a collection of image folders for PNG files, and adds any that are new to the database.
* `register_service.py` can be used to register the script to be automatically launched when the Raspberry Pi is powered up, and to unregister it if necessary.

<a data-flickr-embed="true" href="https://www.flickr.com/photos/57897385@N07/54408811594/in/dateposted/" title="An e-paper frame showing a rather obscure reference"><img src="https://live.staticflickr.com/65535/54408811594_48a7f047ac_z.jpg" style="width:70%;max-width:512px;" alt="An e-paper frame showing a rather obscure reference"/></a>

### Future plans:

There are two additional things I might add here, depending on the direction I want to go:

* Add a web server on the device that launches when it's charging, and can be used to manage the database of images, including uploading new ones and scheduling an image playlist.
* Add a process that runs when wifi is connected, fetching a set of new images and/or an image playlist from a predefined web location.

For now, I just have over a thousand images dumped directly onto the microSD card.  It'll take three years or so to run through them, so there's no hurry to decide which of the above approaches to take...

The following sections give a pretty thorough walkthrough of how this frame was assembled, wired, and programmed:

## [Materials List](documentation/materials.md)

## [Construction And Wiring](documentation/construction.md)

## [Software](documentation/software.md)

Hopefully this will inspire your own e-paper project!  If so, I'd love to hear about it.

Happy hacking!