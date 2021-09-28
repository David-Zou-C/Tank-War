
'''
服务端测试
'''

import socket
import datetime
import traceback
import struct
from threading import Thread
import sys
import pygame
from pygame.locals import *


class Server:
    '''
    服务器主类
    '''
    __user_cls = None

    @staticmethod
    def write_log(msg):
        cur_time = datetime.datetime.now()
        s = "[" + str(cur_time) + "]" + msg
        print(s)

    def __init__(self, ip, port):
        self.connections = []  # 所有连接的客户端
        self.playerGroup = []  # 所有在线的玩家ID
        self.write_log("服务器启动中，请稍候...")
        try:
            self.listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # 监听者，用于接收新的socket连接
            self.listener.bind((ip, port))  # 绑定ip、端口
            self.listener.listen(5)  # 最大等待数
        except:
            self.write_log('服务器启动失败，请检查ip端口是否被占用。详细原因：\n' + traceback.format_exc())
            return

        if self.__user_cls is None:
            self.write_log('服务器启动失败，未注册用户自定义类')
            return

        self.write_log(f'服务器启动成功：{ip}:{port}')

        t_wait = Thread(target=self.waitClient)
        t_wait.setDaemon(True)
        t_wait.start()

    def waitClient(self):
        while True:
            client, _ = self.listener.accept()  # 阻塞，等待客户端连接
            user = self.__user_cls(client, self.connections, self.playerGroup)
            self.connections.append(user)
            self.write_log('有新连接进入，当前连接数：{}'.format(len(self.connections)))

    @classmethod
    def register_cls(cls, sub_cls):
        """
        注册玩家的自定义类
        """
        if not issubclass(sub_cls, Connection):
            cls.write_log('注册用户自定义类失败，类型不匹配')
            return

        cls.__user_cls = sub_cls

    def sendOut(self, cmd):
        print(cmd)
        inp = cmd
        for i, soc in enumerate(self.connections):
            # 将输入指令打包
            if inp == 'load game':
                sendJson = {
                    'event type': 'load game',
                    'tank num': len(self.playerGroup),
                    'tank id': i
                }
                body = str(sendJson)
                body = body.encode(encoding='utf-8')
            else:
                body = inp.encode(encoding='utf-8')
            header = [1, len(body), 103]
            headPack = struct.pack('!3I', *header)
            sendPack = headPack + body

            soc.socket.send(sendPack)

class Connection:
    """
    连接类，每个socket连接都是一个connection
    """

    def __init__(self, socket, connections, playerGroup):
        # 客户端的socket
        self.socket = socket
        # 客户端池
        self.connections = connections
        # 在线玩家组
        self.playerGroup = playerGroup

        # 数据包头部大小
        self.headerSize = 12
        self.header_ver = 1  # 数据包头部信息的版本号
        self.header_cmd = 101  # 数据包头部信息的指令
        # 单独创建一个线程进行管理
        self.data_handler()

    def sendClient(self, data):
        # 消息正文
        body = data
        # 消息头部
        header = [self.header_ver, len(body), self.header_cmd]
        # 编码并打包
        headPack = struct.pack('!3I', *header)
        bodyPack = body.encode(encoding='utf-8')
        sendPack = headPack + bodyPack
        # 发送
        self.socket.send(sendPack)


    def data_handler(self):
        # 给每个连接创建一个独立的线程进行管理
        thread = Thread(target=self.recv_data)
        thread.setDaemon(True)
        thread.start()

    def recv_data(self):
        # 发送连接成功信息
        self.sendClient('You already connected!')
        # 接收数据
        try:
            while True:
                bytes = self.socket.recv(2048)  # 我们这里只做一个简单的服务端框架，不去做分包处理。所以每个数据包不要大于2048
                if len(bytes) == 0:
                    self.socket.close()
                    # 删除连接
                    self.connections.remove(self)
                    self.playerGroup.remove(self.playerID)
                    break
                # 处理数据
                if self.deal_data(bytes):
                    print("客户端发送断开连接请求，即将主动断开连接！")
                    self.socket.close()
                    # 删除连接
                    self.connections.remove(self)
                    self.playerGroup.remove(self.playerID)
                    break
        except:
            self.connections.remove(self)
            Server.write_log('有用户接收数据异常，已强制下线，详细原因：\n' + traceback.format_exc())

    def deal_data(self, bytes):
        """
        处理客户端的数据，需要子类实现
        """
        raise NotImplementedError


@Server.register_cls
class Player(Connection):
    """
    玩家类，我们的游戏中，每个连接都是一个Player对象
    """

    def __init__(self, *args):
        super().__init__(*args)
        self.dataBuffer = bytes()  # 数据包缓冲区
        self.login_state = False  # 登录状态
        self.nickname = None  # 昵称
        self.x = None  # 人物在地图上的坐标
        self.y = None
        self.playerID = None
        self.life = None
        self.skill = None
        self.position = None
        self.state = {
            'player id': None,
            'life': None,
            'skill': None,
            'position': None
        }

    def deal_data(self, bytes):
        """
        处理服务端发送的数据
        :param bytes:
        :return:
        """
        # 加入缓冲区
        self.dataBuffer += bytes
        # 判断是否小于数据包最小大小（数据包头部大小）
        if len(self.dataBuffer) < self.headerSize:
            # 如果小于头部大小，则退出处理，继续接收数据直到大于头部大小
            return
        # 如果大于头部大小，则首先从头部信息获取消息主体大小
        headerPack = struct.unpack('!3I', self.dataBuffer[:self.headerSize])  # 解码头部信息
        bodySize = headerPack[1]  # 获取消息主体大小
        # 判断缓冲区是否已经完整地接收到此数据包（头部+主体）
        if len(self.dataBuffer) >= self.headerSize+bodySize:
            # 如果已经完整地接收到了，则读取消息的正文内容
            body = self.dataBuffer[self.headerSize:self.headerSize+bodySize]
            # 读取完消息主体之后，丢弃此数据包
            self.dataBuffer = self.dataBuffer[self.headerSize+bodySize:]
            # 解码并处理消息
            str_data = body.decode('utf8')
            if str_data == "I quit":
                return True
            elif str_data == 'I Connected!':
                return
            elif 'My player id is' in str_data:
                self.playerID = str_data.split()[-1]
                if self.playerID not in self.playerGroup:
                    self.playerGroup.append(self.playerID)
            # print('\n客户端消息：', str_data)
            # print(str_data)
            # 重新编码并挨个发送给所有客户端
            for conn in self.connections:
                conn.sendClient(str_data)
        else:
            # 没有完整地接收到消息
            pass




FPS = 60

class StartGame:
    def __init__(self):

        # 通过图形界面输入并获取：IP地址、端口号
        self.ServerIP = None
        self.ServerPort = None

        pygame.init()

        # 屏幕尺寸
        self.screenSize = self.width, self.height = 1440, 900

        self.fps = FPS
        # 设置显示对象
        self.screen = pygame.display.set_mode(self.screenSize)

        # 定义刷新时间对象
        self.fClock = pygame.time.Clock()

        # 加载所有图片
        self.loadImage()


        # 界面进度
        self.ProgressRate = 1
        # 设置按键的对应值表
        self.setKey2text()

        # 文本对象
        self.myFont_IP = pygame.font.Font('fonts/arial.TTF', 55)
        self.myFont_Port = pygame.font.Font('fonts/arial.TTF', 55)
        self.myFont_PlayerNum = pygame.font.Font('fonts/arial.TTF', 50)

        self.PutIP = list('127.0.0.1')
        self.PutPort = list('1234')
        # 进度2的一些值
        self.choiceLoad = True
        self.choiceStart = False
        self.loaded = False

    def setKey2text(self):
        num1_Key = [K_0, K_1, K_2, K_3, K_4, K_5, K_6, K_7, K_8, K_9, K_PERIOD]
        num2_Key = [K_KP0, K_KP1, K_KP2 ,K_KP3, K_KP4, K_KP5, K_KP6, K_KP7, K_KP8, K_KP9, K_KP_PERIOD]
        numText = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '.']
        char_Key = [K_a, K_b, K_c, K_d, K_e, K_f, K_g, K_h, K_i, K_j, K_k, K_l, K_m, K_n, K_o, K_p, K_q, K_r, K_s, K_t, K_u, K_v, K_w, K_x, K_y, K_z]
        charText = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']

        self.allKey = num1_Key + num2_Key + char_Key
        self.allText = numText + numText + charText
        self.Key2Text = dict(zip(self.allKey, self.allText))

    def loadImage(self):
        self.serverBackgroundPath = 'img/Menu/ServerBackground.png'
        self.choiceLoadPath = 'img/Menu/Load.png'
        self.choiceStartPath = 'img/Menu/Start.png'
        self.inputServerIPPath = 'img/Menu/InputServerIP.png'
        self.inputServerPortPath = 'img/Menu/InputServerPort.png'
        # 输入名称界面
        self.serverBackgroundImage = pygame.image.load(self.serverBackgroundPath).convert_alpha()
        self.serverBackgroundImage = pygame.transform.scale(self.serverBackgroundImage, self.screenSize)

        # 选择进入房间或设置界面
        self.choiceLoadImage = pygame.image.load(self.choiceLoadPath).convert_alpha()
        self.choiceStartImage = pygame.image.load(self.choiceStartPath).convert_alpha()

        # 为Room和Setting设置一个半透明背景
        self.halfTransparent_room = pygame.Surface((483, 236)).convert_alpha()
        self.halfTransparent_room.fill((0, 125, 125, 50))

        # 输入服务器IP地址界面
        self.inputServerIPImage = pygame.image.load(self.inputServerIPPath).convert_alpha()
        self.inputServerIPImage = pygame.transform.scale(self.inputServerIPImage, self.screenSize)

        # 输入服务器端口号界面
        self.inputServerPortImage = pygame.image.load(self.inputServerPortPath).convert_alpha()
        self.inputServerPortImage = pygame.transform.scale(self.inputServerPortImage, self.screenSize)

    def startServer(self,):
        print(self.ServerIP, self.ServerPort)
        self.Server = Server(self.ServerIP, int(self.ServerPort))

    def start(self):
        running = True
        while running:
            # 事件处理
            for event in pygame.event.get():
                # 退出
                if event.type == QUIT:
                    sys.exit()

                if event.type == MOUSEBUTTONDOWN:
                    print(event.pos)

                if event.type == KEYDOWN:
                    if self.ProgressRate == 1:
                        # 输入服务器IP阶段
                        if event.key in self.allKey:
                            if len(self.PutIP) < 15:
                                self.PutIP.append(self.Key2Text[event.key])
                        elif event.key == K_BACKSPACE:
                            if len(self.PutIP) > 0:
                                self.PutIP.pop(-1)
                        elif event.key == K_RETURN:
                            if len(self.PutIP) > 0:
                                self.ServerIP = ''.join(self.PutIP)
                                self.ProgressRate += 1
                        elif event.key == K_ESCAPE:
                            self.ProgressRate -= 1
                    elif self.ProgressRate == 2:
                        # 输入服务器Port阶段
                        if event.key in self.allKey:
                            if len(self.PutPort) < 6:
                                self.PutPort.append(self.Key2Text[event.key])
                        elif event.key == K_BACKSPACE:
                            if len(self.PutPort) > 0:
                                self.PutPort.pop(-1)
                        elif event.key == K_RETURN:
                            if len(self.PutPort) > 0:
                                self.ServerPort = ''.join(self.PutPort)
                                self.ProgressRate += 1
                                self.startServer()

                        elif event.key == K_ESCAPE:
                            self.ProgressRate -= 1
                    elif self.ProgressRate == 3:
                        # 选择加载游戏或者开始游戏
                        if event.key == K_w or event.key == K_s:
                            if self.choiceLoad:
                                self.choiceLoad = False
                                self.choiceStart = True
                            elif self.choiceStart:
                                self.choiceLoad = True
                                self.choiceStart = False
                        elif event.key == K_RETURN:
                            if self.choiceLoad:
                                self.Server.sendOut('load game')

                            elif self.choiceStart:
                                self.Server.sendOut('start game')

                        elif event.key == K_ESCAPE:
                            pass

            self.screen.fill('black')

            if self.ProgressRate == 1:
                self.screen.blit(self.inputServerIPImage, (0, 0))
                self.textImage = self.myFont_IP.render(''.join(self.PutIP), True, (0, 125, 125))
                self.screen.blit(self.textImage, (550, 475))
            elif self.ProgressRate == 2:
                self.screen.blit(self.inputServerPortImage, (0, 0))
                self.textImage = self.myFont_Port.render(''.join(self.PutPort), True, (0, 125, 125))
                self.screen.blit(self.textImage, (550, 475))
            elif self.ProgressRate == 3:
                self.screen.blit(self.serverBackgroundImage, (0, 0))
                if self.choiceLoad:
                    self.screen.blit(self.halfTransparent_room, (223, 286))
                elif self.choiceStart:
                    self.screen.blit(self.halfTransparent_room, (223, 535))
                self.screen.blit(self.choiceLoadImage, (150, 250))
                self.screen.blit(self.choiceStartImage, (150, 500))

                self.player_num = len(self.Server.playerGroup)
                self.textImage = self.myFont_PlayerNum.render('Current number of players is : '+str(self.player_num), True, (50, 150, 200))
                self.screen.blit(self.textImage, (650, 100))
                for i, each_pla in enumerate(self.Server.playerGroup):
                    self.textImage = self.myFont_PlayerNum.render(each_pla, True, (220, 60, 60))
                    self.screen.blit(self.textImage, (800, 170+i*70))
            pygame.display.flip()
            self.fClock.tick(self.fps)
            if self.ProgressRate > 4:
                break

        pygame.quit()
start = StartGame()
start.start()


