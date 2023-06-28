---
title: The project
permalink: /description/
---


The project outlined here is a comprehensive exploration of the tools available for designing and implementing control solutions for the PX4 open-source autopilot platform. The goal is to demonstrate how these tools can be integrated with computer vision mechanisms to achieve vision-based self-guided unmanned aerial vehicles (UAVs). To achieve this objective, a simple application named DroneVisionControl has been developed. It aims to serve as a foundation for the investigation into the PX4 ecosystem and methods of integrating the necessary hardware and software for UAV control. For the computer vision detection mechanisms, the ready-to-use Mediapipe suite of libraries for real-time image analyses on hand-held devices has been employed to reduce the project’s complexity. Two primary architectures for integrating software and hardware in vision-based scenarios have been proposed, with one scenario involving offboard vision modules and the other integrating onboard camera and vision computation.

The first scenario involves a proof-of-concept control mechanism that translates hand gestures executed in front of an independent camera to flight commands, thereby controlling the vehicle’s movement. This mechanism functions as a landing platform to begin development and test the most basic integration between the tools employed. The second scenario builds upon the first to integrate the camera and vision computation onboard the vehicle to develop a tracking and following control solution. This mechanism will track and follow a person standing in the drone’s field of view, mirroring their movements in a 3D environment. 

A dedicated development environment was employed to further the development of these control mechanisms. This environment facilitated the design process by allowing a gradual adaptation of the software to match the hardware requirements, starting from a purely simulated flight controller and progressing towards actual flight tests in an unmanned vehicle. The critical component of this environment is the integration with the AirSim simulation engine. Built upon the powerful 3D computer graphics game engine Unreal, it provides a platform that ensures secure and comprehensive testing of control solutions that are still a work in progress and not entirely reliable.

For this project, all the code has been implemented in Python, running on a companion
computer separate from the flight controller board. This deliberate approach ensures that
the control solutions remain independent of the hardware components and are not tied
to any particular flight stack. Consequently, the results can be applied to any autopilot
platform that offers exposed APIs and are not limited to the PX4 ecosystem.

In conclusion, this work offers a thorough investigation into the development of vision-
based self-guided UAVs, presenting a range of tools and techniques that can be utilized to
accomplish this objective.