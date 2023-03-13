---
# Feel free to add content and custom Front Matter to this file.
# To modify the layout, see https://jekyllrb.com/docs/themes/#overriding-theme-defaults

layout: splash
permalink: /
header:
  overlay_color: "#000"
  overlay_filter: "0.5"
  overlay_image: /assets/images/splash-page-drone-2.jpg
  caption: "Photo by [Ian Usher](https://unsplash.com/@iusher) on [Unsplash](https://unsplash.com/)"
excerpt: ""
intro: 
  - excerpt: 'The popular open-source platform PX4 aims to facilitate the programming of unmanned
  aerial vehicles and their integration with new sensors and actuators and make it approach
  able for the common developer. This thesis aims to demonstrate how this platform can be
  used to develop solutions that integrate computer vision techniques and use their input to
  control the movement of an aerial vehicle, while employing easily-available and affordable
  hardware with basic specifications. For this purpose, a viable solution is presented that
  allows a drone to use an onboard camera to identify and keep track of a person in its field
  of view to follow their movement.'
feature_row:
  - image_path: assets/images/unsplash-gallery-image-1-th.jpg
    image_caption: "Image courtesy of [Unsplash](https://unsplash.com/)"
    alt: "placeholder image 1"
    title: "Placeholder 1"
    excerpt: "This is some sample content that goes here with **Markdown** formatting."
  - image_path: /assets/images/unsplash-gallery-image-2-th.jpg
    alt: "placeholder image 2"
    title: "Placeholder 2"
    excerpt: "This is some sample content that goes here with **Markdown** formatting."
    url: "#test-link"
    btn_label: "Open"
    btn_class: "btn--primary"
  - image_path: /assets/images/unsplash-gallery-image-3-th.jpg
    title: "Placeholder 3"
    excerpt: "This is some sample content that goes here with **Markdown** formatting."
feature_row2:
  - image_path: /assets/images/video-hand-sitl.png
    alt: "Videos"
    title: "Videos"
    excerpt: 'A collection of recordings from project tests'
    url: "/videos/"
    btn_label: "Open"
    btn_class: "btn--primary"
feature_row3:
  - image_path: /assets/images/report-front-page.png
    alt: "Report front page"
    title: "Report"
    excerpt: 'Written report for the project'
    url: "/report/"
    btn_label: "Open"
    btn_class: "btn--primary"
feature_row4:
  - image_path: /assets/images/splash-page-github.jpg
    alt: "GitHub"
    title: "Repository"
    excerpt: 'Link to the project repository hosted on GitHub'
    url: "https://github.com/l-gonz/tfg-giaa-dronecontrol"
    btn_label: "Open"
    btn_class: "btn--primary"
---

{% include feature_row id="intro" type="center" %}

<!-- {% include feature_row %} -->

{% include feature_row id="feature_row2" type="left" %}

{% include feature_row id="feature_row3" type="right" %}

{% include feature_row id="feature_row4" type="center" %}
