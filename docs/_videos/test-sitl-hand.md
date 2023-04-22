---
title:  "Test SITL: hand solution"
date:   2023-03-12 14:07:10 +0100
categories: videos
classes: wide
header:
  teaser: /assets/images/video-hand-sitl.png
  overlay_image: /assets/images/video-hand-sitl.png
  overlay_color: "#000"
  overlay_filter: "0.3"
excerpt: ""
---
## Recorded simulation
A camera testing tool has been developed specifically for this test so that it is possible to establish a connection to PX4 SITL and process images without engaging any of the program's control modules.
The commands are then sent to PX4 through keyboard input.
For example, the key "T" will make the simulated vehicle take off.
THis video shows the image and text output of the program when the test camera tool is run with the hand detection feature activated.
On the left side, the detection algorithm tracks the joint of the hand present in the captured image and on the right side, the logged information shows when the connection is established and keyboard commands are sent to the simulator.

{% include video id="0cQcU64oAlE" provider="youtube" %}