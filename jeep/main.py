def startespnow():
    # 使用espnow来接收消息，处理消息的方案。
    from jeep_espnow_rec import EspNowReceiver
    from machine import Pin # type: ignore # 导入Pin类以控制LED    
    # 发送端的MAC地址（替换为实际地址）
    SENDER_MAC = b'\x98=\xae\xeb\xa9\xf0'  # esp32遥控
    channel_number = 1

    # 创建接收器并启动
    receiver = EspNowReceiver(SENDER_MAC,channel_number)
    receiver.start_receiving()                     
def startwebsocket():
    # 使用网页服务器，websocket的方式来接收消息，处理消息的方案。
    import jeep_websocket_rec
    jeep_websocket_rec.start_websocket_server()

if __name__ == "__main__":
    #startespnow()
    startwebsocket()