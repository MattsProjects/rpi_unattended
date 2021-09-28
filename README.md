# RPi_unattended
Originally started in 2015, this was a fun exploratory project to create a ground-up fault-tolerant (HW &amp; SW) platform for unattended RPi projects. Includes sample use-case of displaying a weather forecast on a PiTFT 2.8" screen

# Background
I've always been fascinated by the ability of satellites, space probes, mars rovers, etc. to be controlled, recovered, and re-programmed completely remotely.
With this project, I set out to understand some of the requirements that these platforms must meet for that to be possible.
It's really amazing what bases need to be covered when you can't just "unplug it and plug it in again" :-)

# Core Features / Objectives
- Operate completely unattended 24/7/365.
- Recover gracefully from any software crashes via watchdog
- Operate in a low-power 'deep sleep' mode for extended periods of main power loss (up to 1 month)
- Resume normal operation when main power is available again
- Recover gracefully from network connection loss
- Provide failsafe keyboard-less & mouse-less full access for on-site service
- Provide onsite physical 'kill switch' for reboot/shutdown
- Automatically notify admin via email of bootup, shutdown, main power lost, and other significant events

# Dependencies
- PiJuice battery hat (originally started with Pimodules' UPSPico)
- pywapi (however this is now obsolete, and a new weather api is needed, perhaps owm...)
- PiTFT 2.8"
- Some other software (mutt, logger, etc.)

# Plans
- Bring project to a more modern platform (originally built on an Rpi2b)
- Clean up code and centralization of user configuration (into a json or yaml file)
- Update the weather applications api to something current.
