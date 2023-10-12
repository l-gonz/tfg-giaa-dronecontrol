---
title:  "Flight test: offboard config"
date:   2023-03-12 14:07:10 +0100
categories: videos
classes: wide
header:
  teaser: /assets/images/video-field-test-offboard.png
  overlay_image: /assets/images/video-field-test-offboard.png
  overlay_color: "#000"
  overlay_filter: "0.3"
excerpt: ""
---
## Recorded test flight
Test of the offboard configuration by running the command:
<p style="text-align: center;">dronecontrol tools test-camera -r COM&lt;X&gt;:57600</p>

The video displays the output on the computer's terminal window, where the connection process and the sent velocity commands are shown, and the output on the camera from the offboard computer.
After successfully connecting to the vehicle, the T and L keys in the computer keyboard can be used for takeoff and landing, respectively. The O key can be used to set the autopilot in offboard flight mode to enable it to receive velocity commands.
Afterwards, the WASD keys can be used to control the forward and sideways velocity of the vehicle and the QE keys to control its yaw velocity.

{% include video id="kCUfz9rsJ_k" provider="youtube" %}