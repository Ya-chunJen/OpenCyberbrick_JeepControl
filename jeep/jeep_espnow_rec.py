import network # type: ignore
import espnow # type: ignore
import utime # type: ignore

# 导入业务包
from jeep_action import JeepAction  # 提前导入避免循环引用问题

class EspNowReceiver:
    """
    ESP-NOW接收器类，用于接收控制指令信息。
    """
    def __init__(self, sender_mac: bytes,channel_number:int = 1):
        """
        初始化ESP-NOW接收器
        :param sender_mac: 发送端的MAC地址（6字节bytes）
        """
        # 网络初始化
        self.channel_number = channel_number
        self._init_wifi()
        
        # ESP-NOW初始化
        self.espnow = espnow.ESPNow() # type: ignore
        self.espnow.active(True)

        # 添加对等设备
        try:
            self.espnow.add_peer(sender_mac)
        except OSError as e:
            if e.args[0] == -12395:  # ESP_ERR_ESPNOW_EXIST
                self.espnow.del_peer(sender_mac)
                self.espnow.add_peer(sender_mac)
            else:
                raise

        # 吉普车控制器实例化
        self.jeep_action = JeepAction()

    def _init_wifi(self):
        """初始化WiFi网络配置"""
        # 先配置AP模式固定信道
        ap = network.WLAN(network.AP_IF)
        ap.active(True)
        ap.config(channel=self.channel_number)
        
        # 再初始化STA模式
        sta = network.WLAN(network.STA_IF)
        sta.active(True)
        sta.disconnect()

    def start_receiving(self):
        """开始接收并处理ESP-NOW消息"""
        print("ESP-NOW接收器已启动，等待指令...")
        while True:
            try:
                _, msg = self.espnow.recv()
                if msg:
                    self.jeep_action._message2action(msg.decode().strip())
            except OSError as e:
                print(f"接收错误: {e}")
                utime.sleep_ms(100)


if __name__ == "__main__":
    # 发送端的MAC地址（替换为实际地址）
    SENDER_MAC = b'\x98=\xae\xeb\xa9\xf0'  # esp32遥控
    channel_number = 1
    
    # 创建接收器并启动
    receiver = EspNowReceiver(SENDER_MAC,channel_number)
    receiver.start_receiving()                     
