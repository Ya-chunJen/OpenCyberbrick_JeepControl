import machine # type: ignore
import neopixel # type: ignore
import time

class JeepLed:
    """控制LED灯的类"""
    def __init__(self, pin=0, num_leds=2):
        self.pin = pin
        self.num_leds = num_leds
        self.np = neopixel.NeoPixel(machine.Pin(self.pin), self.num_leds)

        # 常用颜色定义
        self.RED = (255, 0, 0)
        self.GREEN = (0, 255, 0)
        self.BLUE = (0, 0, 255)
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)  # 熄灭
        
        # 初始化时点亮所有LED为白色，然后熄灭
        self.set_all(self.WHITE)
        time.sleep(1)
        self.clear_all()

    def set_all(self, color):
        """设置所有LED为同一颜色"""
        for i in range(self.num_leds):
            self.np[i] = color
        self.np.write()
    
    def clear_all(self):
        """关闭所有LED灯"""
        self.set_all(self.BLACK)
    
    def single_led(self, index, color):
        """点亮单个LED
        Args:
            index: LED索引(0到NUM_LEDS-1)
            color: LED颜色
        """
        if 0 <= index < self.num_leds:
            self.np[index] = color
            self.np.write()

if __name__ == "__main__":
    jeepled = JeepLed(pin=0, num_leds=2)
    while True:
        command = input("Enter command (on、off、color_RGB): ")
        command_list = command.split(",")
        if command_list[0] == "on":
            jeepled.set_all(jeepled.WHITE)
        elif command_list[0] == "off":
            jeepled.clear_all()
        else:
            jeepled.set_all((int(command_list[0]), int(command_list[1]), int(command_list[2])))