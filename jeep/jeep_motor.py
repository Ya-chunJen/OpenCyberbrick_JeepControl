# Jeep车马达驱动程序
from machine import Pin,PWM # type: ignore
import utime # type: ignore

class JeepMotor:
    def __init__(self,ENA_PIN=14,IN1_PIN=12,IN2_PIN=13) -> None:
        # 电机初始化，GPIO口分别是14、12、13，即D5、D6、D7。
        # 这里用一条控制逻辑，控制了两个马达。
        self.ENA = PWM(Pin(ENA_PIN)) # type: ignore
        self.ENA.freq(500)
        self.IN1 = Pin(IN1_PIN, Pin.OUT,value=0)
        self.IN2 = Pin(IN2_PIN, Pin.OUT,value=0)

    def motor(self,direction=0,speed=900):
        # direction为0是停转，为1是正转，为2是反转。
        speed = min(max(speed, 600), 1023)  # 确保速度在 600 到 1023 之间
        print(f"马达方向代码（0是停，1是正，2是反）：{direction}，速度：{speed}")
        if direction == 0:
            self.ENA.duty(0)
            self.IN1.off()
            self.IN2.off()
        elif direction == 1:
            self.ENA.duty(speed)
            self.IN1.off()
            self.IN2.on()
        elif direction == 2:
            self.ENA.duty(speed)
            self.IN1.on()
            self.IN2.off()

    def stop(self,speed=0):
        # 马达停止
        print(f"全部停止！")
        self.motor(0,speed)

    def forward(self,speed=900):
        # 向前
        print(f"向前，速度：{speed}。")
        self.motor(1,speed) 

    def backward(self,speed=900):
        # 向后
        print(f"向后，速度：{speed}。")
        self.motor(2,speed)

if __name__ == "__main__":
    # 测试代码
    jeepmotor = JeepMotor()

    jeepmotor.forward(800)
    utime.sleep(1)
    jeepmotor.stop()

    jeepmotor.backward(800)
    utime.sleep(1)
    jeepmotor.stop()

    print("测试结束。")