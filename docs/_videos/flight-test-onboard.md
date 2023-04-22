---
title:  "Flight test: onboard config"
date:   2023-03-12 14:07:10 +0100
categories: videos
classes: wide
header:
  teaser: /assets/images/video-field-test-onboard.png
  overlay_image: /assets/images/video-field-test-onboard.png
  overlay_color: "#000"
  overlay_filter: "0.3"
excerpt: ""
---
## Recorded test flight
This flight test is started with the main and secondary batteries attached, respectively, to the power module and to the Raspberry Pi.
The onboard computer is controlled with a remote desktop connection through WiFi.
By this connection, a terminal window can be opened on the desktop, and the following command run:

<p style="text-align: center;">dronecontrol tools test-camera -r /dev/serial0:921600 -p</p>

As opposed to the offboard flight test using the telemetry radio, in this test, the serial connection runs at a baudrate of 921600, which matches the configured baudrate on the \texttt{TELEM2} port of the Pixhawk board.
The "-p" option enables pose detection in the output images.

{% include video id="cC2J1kjHC9Q" provider="youtube" %}