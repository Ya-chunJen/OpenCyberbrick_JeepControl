import network # type: ignore
import ujson # type: ignore

wlan_sta = network.WLAN(network.STA_IF)
wlan_sta.active(True)
wlan_mac = wlan_sta.config('mac')
try:
    with open("wificonfig.json", 'r') as f:
        wificonfig = ujson.load(f)
except:
    wificonfig = {"ssid": "xx", "password": "xxxxxxx"}
ssid = wificonfig["ssid"]
password = wificonfig["password"]
wlan_sta.connect(ssid,password)
print(f"WIFI信息: {wlan_sta.ifconfig()}")