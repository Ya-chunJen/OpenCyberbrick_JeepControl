import network # type: ignore
import usocket as socket  # 引用socket模块 # type: ignore
import ure as re # type: ignore
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

def parse_query_string(query_string: str) -> dict:
    """
    手动解析类似 a=1&b=2 的查询字符串。
    """
    params = {}
    pairs = query_string.split('&')
    for pair in pairs:
        if '=' in pair:
            key, value = pair.split('=', 1)
            params[key] = value
        else:
            params[pair] = ''
    return params
def parse_http_request(raw_data: bytes) -> dict:
    """
    在 MicroPython 中解析 HTTP 请求数据并返回结构化字典。
    :param raw_data: 原始 HTTP 请求的字节数据
    :return: 结构化的字典(JSON兼容)
    """
    try:
        data_str = raw_data.decode('utf-8')
    except UnicodeDecodeError:
        raise ValueError("无法解码输入数据")

    lines = data_str.split('\r\n')

    if not lines:
        raise ValueError("无效的 HTTP 请求")

    # 解析第一行：方法、路径、版本
    request_line = lines[0].strip()
    parts = request_line.split(' ')
    if len(parts) != 3:
        raise ValueError("无效的请求行")
    method, full_path, http_version = parts

    # 提取路径和查询参数
    path = full_path
    query_params = {}
    if '?' in full_path:
        path, query_string = full_path.split('?', 1)
        query_params = parse_query_string(query_string)

    # 解析 headers
    headers = {}
    for i in range(1, len(lines)):
        line = lines[i]
        if line == '':
            break
        if ':' in line:
            key, value = line.split(':', 1)
            headers[key.strip()] = value.strip()

    result = {
        "method": method,
        "path": path,
        "query_params": query_params,
        "http_version": http_version,
        "headers": headers
    }
    return result
def runwebserver():
    apmodel(1)  # 开启热点模式
    s = socket.socket() # 创建socket对象
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # (重要)设置端口释放后立即就可以被再次使用
    s.bind(socket.getaddrinfo("0.0.0.0", 80)[0][-1])  # 绑定地址与端口
    s.listen(5)  # 开启监听（最大连接数5）
    print(f"接入热点后可从浏览器访问下面地址：\n热点网络IP地址: {ap.ifconfig()[0]}, WIFI网络IP地址: {wlan_sta.ifconfig()[0]}")
    while True:  # mian()函数中进行死循环，在这里保持监听浏览器请求与对应处理
        cl, client_addr = s.accept()  # 接收来自客户端的请求与客户端地址
        cl.settimeout(5.0)  # 设置超时时间为5秒
        try:
            request = cl.recv(1024)
            request_json = parse_http_request(request)
            print(request_json["path"], request_json["query_params"])
            if request_json["path"] == "/":
                # 修改响应头，添加对HTTPS的支持
                response = 'HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nAccess-Control-Allow-Origin: *\r\n\r\n'
                cl.sendall(response.encode('utf-8'))
            elif request_json["path"] == "/control":
                query_params = request_json.get("query_params", {})
                command:str = query_params.get("command","stop|stop|-2|-2|-2|-2|")
                jeep_action._message2action(command)
                # 修改响应头，添加对HTTPS的支持
                response = 'HTTP/1.1 200 OK\r\nAccess-Control-Allow-Origin: *\r\n\r\n'
                cl.sendall(response.encode('utf-8'))
            elif request_json["path"] == "/wifi":
                query_params = request_json.get("query_params", {})
                ssid:str = query_params.get("ssid")
                psd:str = query_params.get("psd")
                wlan_sta.connect(ssid,psd)
                # 修改响应头，添加对HTTPS的支持
                response = 'HTTP/1.1 200 OK\r\nAccess-Control-Allow-Origin: *\r\n\r\n'
                cl.sendall(response.encode('utf-8'))
            elif request_json["path"] == "/wifistatus":
                response = 'HTTP/1.1 200 OK\r\nAccess-Control-Allow-Origin: *\r\n\r\n' + f"热点网络IP地址: {ap.ifconfig()[0]}<br />WIFI网络IP地址: {wlan_sta.ifconfig()[0]}"
                cl.sendall(response.encode('utf-8'))
        except Exception as e:
            print("错误信息: ",e)
            import machine # type: ignore
            machine.reset()  # 内存不足时重启
        finally:
            cl.close()
            gc.collect()  # 清理内存碎片
if __name__ == '__main__':
    runwebserver()  # 运行main()函数，启动服务