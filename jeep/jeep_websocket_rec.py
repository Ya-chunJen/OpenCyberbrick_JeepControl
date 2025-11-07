import network # type: ignore
import usocket as socket # type: ignore
import uselect as select # type: ignore
from time import sleep, ticks_ms # type: ignore
import gc
import ubinascii # type: ignore

from jeep_action import JeepAction  # 提前导入避免循环引用问题
jeep_action = JeepAction()

wlan_sta = network.WLAN(network.STA_IF)
wlan_sta.active(True)
wlan_mac = wlan_sta.config('mac')
print("本机Mac地址：",ubinascii.hexlify(wlan_mac).decode())
ap = network.WLAN(network.AP_IF)
ap.active(True)

# 设置为热点模式
def apmodel(model=1):
    # model: 1-为开启热点模式，0为关闭热点模式。
    ap.config(ssid="esp"+ubinascii.hexlify(wlan_mac).decode(),password="12345678")  # type: ignore
    if model:
        print("开启热点模式")
        ap.active(True)
        print(ap.ifconfig()) # type: ignore
    else:
        print("关闭热点模式")
        ap.active(False)


def ws_handshake(sock, data):
    """处理WebSocket握手"""
    if b'Sec-WebSocket-Key:' in data:
        lines = data.decode().split('\r\n')
        key = None
        for line in lines:
            if line.startswith('Sec-WebSocket-Key:'):
                key = line.split(': ')[1]
                break
        
        if key:
            import uhashlib # type: ignore
            magic = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
            accept_key = ubinascii.b2a_base64(uhashlib.sha1((key + magic).encode()).digest()).decode().strip()
            
            response = (
                "HTTP/1.1 101 Switching Protocols\r\n"
                "Upgrade: websocket\r\n"
                "Connection: Upgrade\r\n"
                "Sec-WebSocket-Accept: " + accept_key + "\r\n\r\n"
            )
            sock.send(response.encode())
            return True
    return False

def ws_send(sock, message):
    """发送WebSocket消息"""
    try:
        msg_bytes = message.encode('utf-8')
        frame = bytearray([0x81])  # 文本帧
        
        if len(msg_bytes) < 126:
            frame.append(len(msg_bytes))
        else:
            frame.append(126)
            frame.extend(len(msg_bytes).to_bytes(2, 'big'))
        
        frame.extend(msg_bytes)
        sock.send(bytes(frame))
        return True
    except Exception as e:
        print(f"发送错误: {e}")
        return False

def ws_receive(data):
    """解析WebSocket消息"""
    # 检查是否是握手响应（包含HTTP头）
    if b'\r\n\r\n' in data:
        # print("检测到握手响应，跳过...")
        header_end = data.find(b'\r\n\r\n') + 4  # 找到HTTP头结束位置
        data = data[header_end:]  # 提取纯WebSocket数据帧部分
        
    if len(data) < 2:
        return None, data
    
    # 检查操作码
    opcode = data[0] & 0x0F
    if opcode != 0x01:  # 非文本帧
        return None, data[2:]
    
    masked = data[1] & 0x80
    payload_len = data[1] & 0x7F
    
    idx = 2
    if payload_len == 126:
        if len(data) < 4:
            return None, data
        payload_len = int.from_bytes(data[2:4], 'big')
        idx = 4
    elif payload_len == 127:
        return None, data  # 不支持超长消息
    
    if masked:
        if len(data) < idx + 4 + payload_len:
            return None, data
        mask = data[idx:idx+4]
        idx += 4
    else:
        if len(data) < idx + payload_len:
            return None, data
    
    payload = data[idx:idx+payload_len]
    
    if masked:
        payload = bytearray(payload)
        for i in range(len(payload)):
            payload[i] ^= mask[i % 4]
        payload = bytes(payload)
    
    try:
        return payload.decode('utf-8'), data[idx+payload_len:]
    except:
        return None, data[idx+payload_len:]

def handle_command(message):
    """处理客户端命令"""
    cmd = message.strip().lower()
    try:
        cmd_type = cmd.split(":")[0]
        cmd_detail = cmd.split(":")[1]
        if cmd_type == "control":
            jeep_action._message2action(cmd_detail)
            return "OK"
        elif cmd_type == "wifi":
            return "OK"
        elif cmd_type == "wifistatus":
            return "OK"
    except:
        return "ERROR"
def start_websocket_server():
    """启动WebSocket服务器"""
    apmodel()
    # 创建服务器socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("0.0.0.0", 8080))
    server_socket.listen(3)  # 减少并发连接数
    
    print(f"🚀 WebSocket服务器已启动: ws://{ap.ifconfig()[0]}:8080 或 ws://{wlan_sta.ifconfig()[0]}:8080")
    
    # 使用poll处理多客户端
    poll = select.poll()
    poll.register(server_socket, select.POLLIN)
    
    clients = {}  # sock -> buffer
    client_ids = {}  # sock -> id
    next_client_id = 1
    
    try:
        while True:
            # 处理事件，设置超时避免忙等待
            events = poll.poll(1000)  # 1秒超时
            for sock, event in events:
                if sock is server_socket:
                    # 新客户端连接
                    client_sock, addr = server_socket.accept()
                    client_id = next_client_id
                    next_client_id += 1
                    clients[client_sock] = b''
                    client_ids[client_sock] = client_id
                    poll.register(client_sock, select.POLLIN)  
                    print(f"✅ 客户端 #{client_id} 连接: {addr}")
                    
                else:
                    # 处理客户端数据
                    try:
                        data = sock.recv(256)  # 减小缓冲区
                        if data:
                            clients[sock] += data                     
                            # 检查是否是WebSocket握手
                            if b'GET' in clients[sock] and b'Upgrade: websocket' in clients[sock]:
                                if ws_handshake(sock, clients[sock]):
                                    client_id = client_ids[sock]
                                    print(f"🔗 客户端 #{client_id} 握手成功")
                                    ws_send(sock, f"连接成功! 你是客户端 #{client_id}")
                                    clients[sock] = b''  # 清空缓冲区
                                else:
                                    # 发送普通HTTP响应
                                    sock.send(b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\n")
                                    sock.close()
                                    poll.unregister(sock)
                                    del clients[sock]
                                    del client_ids[sock]
                            else:
                                # 处理WebSocket数据
                                while True:
                                    msg, remaining = ws_receive(clients[sock])
                                    if msg is None:
                                        break                                   
                                    client_id = client_ids[sock]
                                    print(f"📥 客户端 #{client_id}: {msg}")                                    
                                    # 处理命令并回复
                                    response = handle_command(msg)
                                    ws_send(sock, response)
                                    print(f"📤 服务端: {response}")                                   
                                    clients[sock] = remaining
                                    gc.collect()  # 及时回收内存                       
                        else:
                            # 客户端断开连接
                            client_id = client_ids.get(sock, '未知')
                            print(f"❌ 客户端 #{client_id} 断开连接")
                            poll.unregister(sock)
                            sock.close()
                            if sock in clients:
                                del clients[sock]
                            if sock in client_ids:
                                del client_ids[sock]
                                
                    except Exception as e:
                        # 客户端错误
                        client_id = client_ids.get(sock, '未知')
                        print(f"⚠️ 客户端 #{client_id} 错误: {e}")
                        poll.unregister(sock)
                        try:
                            sock.close()
                        except:
                            pass
                        if sock in clients:
                            del clients[sock]
                        if sock in client_ids:
                            del client_ids[sock]
            
            # 定期内存回收
            if ticks_ms() % 5000 < 100:  # 每5秒左右回收一次
                gc.collect()
                
    except KeyboardInterrupt:
        print("\n🛑 服务器被用户停止")
    except Exception as e:
        print(f"💥 服务器错误: {e}")
    finally:
        # 清理资源
        for sock in list(clients.keys()):
            try:
                poll.unregister(sock)
                sock.close()
            except:
                pass
        server_socket.close()
        print("🧹 服务器已关闭")

# 启动服务器
if __name__ == "__main__":
    start_websocket_server()

