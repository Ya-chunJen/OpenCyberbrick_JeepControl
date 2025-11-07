import utime # type: ignore

# 导入业务包
from jeep_motor import JeepMotor  # 提前导入避免循环引用问题
from jeep_servo import Servo  # 提前导入避免循环引用问题
from jeep_led import JeepLed  # 提前导入避免循环引用问题

class JeepAction:
    """
    整合吉普车的所有动作控制
    """
    def __init__(self):
        """
        初始化吉普车动作控制
        """
        # 吉普车控制器实例化
        self.jeepmotor = JeepMotor(14,12,13)
        self.speed = 900  # 初始速度设为900，范围400-1200
        self.jeepsteering = Servo(15)  # 假设舵机连接在GPIO15
        self.jeepled = JeepLed(2,2)  # 假设LED连接在GPIO2，2个LED灯

    def _message2action(self, message: str):
        """
        将接收到的消息转换为具体动作
        :param message: 接收到的消息，如stop|stop|-2|-2|-2|-2|'
        """
        print(f"收到指令: {message}")
        channle_list = message.split("|")
        channle_1 = channle_list[0] # 第一频道是左摇杆的方向，top是向上，bottom是向下，stop是停止，还有left和right
        channle_2 = channle_list[1] # 第二频道是右摇杆的方向，top是向上，bottom是向下，stop是停止，还有left和right
        channle_3 = channle_list[2] # 第三频道是左摇杆的按钮，-2是无变化状态，-1是按下动作，其他数字键释放之后会返回前次按下的时长。
        channle_4 = channle_list[3] # 第四频道是右摇杆的按钮，-2是无变化状态，-1是按下动作，其他数字键释放之后会返回前次按下的时长。
        channle_5 = channle_list[4] # 第五频道是蓝色按钮，-2是无变化状态，-1是按下动作，其他数字键释放之后会返回前次按下的时长。
        channle_6 = channle_list[5] # 第六频道是红色按钮，-2是无变化状态，-1是按下动作，其他数字键释放之后会返回前次按下的时长。

        if int(channle_6) == -1:
            # 加档，当红色按钮被按下时，速度增加100，最大值为1200，最小值为400。
            self.speed = self.speed + 100
            if self.speed >= 1200:
                self.speed = 1200

        if int(channle_5) == -1:
            # 减档，当蓝色按钮被按下时，速度减少100，最大值为1200，最小值为400。
            self.speed = self.speed - 100
            if self.speed <= 400:
                self.speed = 400

        # 根据摇杆状态执行对应的动作
        if channle_1 == "top":
            # 向前
            self.jeepmotor.forward(self.speed)
            self.jeepled.set_all(self.jeepled.GREEN)
        elif channle_1 == "bottom":
            # 向后
            self.jeepmotor.backward(self.speed)
            self.jeepled.set_all(self.jeepled.RED)
        elif channle_1 == "stop":
            # 左转
            self.jeepmotor.stop(self.speed)
        else:
            # 没有用到channle_1的其他状态，即左、右。
            pass

        if channle_2 == "left":
            # 向左转，舵机转到150度位置，点亮左侧LED
            self.jeepsteering.write_angle(150)
            self.jeepled.single_led(1,self.jeepled.WHITE)
        elif channle_2 == "right":
            # 向右转，舵机转到50度位置，点亮右侧LED
            self.jeepsteering.write_angle(50)
            self.jeepled.single_led(0,self.jeepled.WHITE)
        elif channle_2 == "stop":
            # 中立位置，舵机转到100度位置。
            self.jeepsteering.write_angle(100)
        else:
            pass

        if channle_4 == "-1":
            # 按下右摇杆按钮，用两个LED表演一段灯光秀
            for i in range(3):
                self.jeepled.set_all(self.jeepled.RED)
                utime.sleep_ms(200)
                self.jeepled.set_all(self.jeepled.GREEN)
                utime.sleep_ms(200)
                self.jeepled.set_all(self.jeepled.BLUE)
                utime.sleep_ms(200)

        if message == "stop|stop|-2|-2|-2|-2|":
            # 没有任何动作时，停止所有LED灯
            self.jeepled.clear_all()
        else:
            pass

if __name__ == "__main__":
    jeepaction = JeepAction()
    while True:
        message = input("请输入指令:") or "stop|stop|-2|-2|-2|-2"
        jeepaction._message2action(message)