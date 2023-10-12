---
title:  "Flight test: hand solution"
date:   2023-03-12 14:07:10 +0100
categories: videos
classes: wide
header:
  teaser: /assets/images/video-field-test-hand.png
  overlay_image: /assets/images/video-field-test-hand.png
  overlay_color: "#000"
  overlay_filter: "0.3"
excerpt: ""
---
## Recorded test flight
The hand-gesture guidance system runs on an offboard computer with more available processing resources and no dependence on battery-supplied power to work.
The setup will be identical to the [offboard](flight-test-offboard) test flight with the telemetry radio as the serial link and the onboard companion computer turned off.
Once the autopilot board is powered up, the control solution can be started with the following command, 
where <device> is the COM port or TTY device the telemetry radio is attached to, depending on the platform:

<p style="text-align: center;">dronecontrol hand -s &lt;device&gt;:57600</p>

After the pilot connects, the image from the computer's webcam will appear on the screen with an outline over any detected hand.
An open palm should be shown to the camera to start controlling the vehicle.
Then, a closed fist will make the drone take off, and pointing up with the index finger will start the offboard flight mode.
Afterwards, moving the index finger right or left will make the vehicle mirror the movement, 
and moving the thumb right or left will make the vehicle move forward and backwards, respectively.
At any point during the test, an open hand will make the drone hover at its current place, as will losing sight of the controlling hand.

{% include video id="cYMIRNmaZ2s" provider="youtube" %}