---
title:  "Flight test: follow solution"
date:   2023-03-12 14:07:10 +0100
categories: videos
classes: wide
header:
  teaser: /assets/images/video-field-test-follow.png
  overlay_image: /assets/images/video-field-test-follow.png
  overlay_color: "#000"
  overlay_filter: "0.3"
excerpt: ""
---
## Recorded test flight
This video tests the follow control solution. The companion computer
is running the follow program, and validates whether it can
keep track of and follow a moving target during a non-simulated flight. The setup will be
identical to the third test in section 4.4.2, without needing a wireless telemetry connection.
The telemetry radio is, therefore, free to be used, for example, to track the vehicle’s path
through the QGroundControl application on a secondary, offboard computer. The control
application will be started with the following command:

<p style="text-align: center;">dronecontrol follow -s /dev/serial0:921600</p>

This video shows the process of getting the vehicle to takeoff (T key), activating offboard
flight mode (O key), and starting movement tracking of the detected figure.

{% include video id="SkKy3LUfDCk" provider="youtube" %}