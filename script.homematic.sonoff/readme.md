<h1>Sonoff WLAN Multichannel Switcher</h1>

Switch your illumination or devices at home with your Kodi remote. All you need is a Sonoff WLAN (multichannel) switch device from Itead in your home automation equipment. Interesting? Visit <b>itead.cc</b> to see more.

It's recommended to flash or update your devices with TASMOTA firmware. You can control your devices with simple HTTP commands within a web browser after that. Additional you have the ability to setup your device(s) via webinterface.

- show status:

        http://<ip-of-your-device>/cm?cmnd=power<channel number>
        
- power on:

        http://<ip-of-your-device>/cm?cmnd=power<channel number>%20On
        
- power off:

        http://<ip-of-your-device>/cm?cmnd=power<channel number>%20Off
        
- toogle power:

        http://<ip-of-your-device>/cm?cmnd=power<channel number>%20toggle                