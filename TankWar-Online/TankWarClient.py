

from TankWar import *
random.seed(None)

class StartGame:
    def __init__(self):

        # 通过图形界面输入并获取：游戏名称、IP地址、端口号
        self.playerName = None
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


        # 界面进度，1为设置游戏名称，2为选择进入房间或设置
        self.ProgressRate = 1
        # 设置按键的对应值表
        self.setKey2text()

        # 文本对象
        self.myFont_Name = pygame.font.Font('fonts/arial.TTF', 70)
        self.myFont_IP = pygame.font.Font('fonts/arial.TTF', 55)
        self.myFont_Port = pygame.font.Font('fonts/arial.TTF', 55)
        self.PutName = [random.choice(self.allText[10:]) for _ in range(5)]
        self.PutIP = list('127.0.0.1')
        self.PutPort = list('1234')
        # 进度2的一些值
        self.choiceRoom = True
        self.choiceSet = False


    def setKey2text(self):
        num1_Key = [K_0, K_1, K_2, K_3, K_4, K_5, K_6, K_7, K_8, K_9, K_PERIOD]
        num2_Key = [K_KP0, K_KP1, K_KP2,K_KP3, K_KP4, K_KP5, K_KP6, K_KP7, K_KP8, K_KP9, K_KP_PERIOD]
        numText = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '.']
        char_Key = [K_a, K_b, K_c, K_d, K_e, K_f, K_g, K_h, K_i, K_j, K_k, K_l, K_m, K_n, K_o, K_p, K_q, K_r, K_s, K_t, K_u, K_v, K_w, K_x, K_y, K_z]
        charText = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']

        self.allKey = num1_Key + num2_Key + char_Key
        self.allText = numText + numText + charText
        self.Key2Text = dict(zip(self.allKey, self.allText))

    def loadImage(self):
        self.startMenuImagePath = 'img/Menu/menu-start.png'
        self.choiceRSPath = 'img/Menu/choiceRS.png'
        self.choiceRoomPath = 'img/Menu/Room.png'
        self.choiceSettingPath = 'img/Menu/Setting.png'
        self.inputServerIPPath = 'img/Menu/InputServerIP.png'
        self.inputServerPortPath = 'img/Menu/InputServerPort.png'
        self.settingAllPath = 'img/Menu/setting-All.png'
        self.settingKeyPath = 'img/Menu/setting-Key.png'
        # 输入名称界面
        self.startMenuImage = pygame.image.load(self.startMenuImagePath).convert_alpha()
        self.startMenuImage = pygame.transform.scale(self.startMenuImage, self.screenSize)

        # 选择进入房间或设置界面
        self.choiceRSImage = pygame.image.load(self.choiceRSPath).convert_alpha()
        self.choiceRSImage = pygame.transform.scale(self.choiceRSImage, self.screenSize)
        self.choiceRoomImage = pygame.image.load(self.choiceRoomPath).convert_alpha()
        self.choiceSettingImage = pygame.image.load(self.choiceSettingPath).convert_alpha()

        # 设置总界面
        self.settingAllImage = pygame.image.load(self.settingAllPath).convert_alpha()
        self.settingAllImage = pygame.transform.scale(self.settingAllImage, self.screenSize)
        # 设置按键界面
        self.settingKeyImage = pygame.image.load(self.settingKeyPath).convert_alpha()
        self.settingKeyImage = pygame.transform.scale(self.settingKeyImage, self.screenSize)

        # 为Room和Setting设置一个半透明背景
        self.halfTransparent_room = pygame.Surface((600, 225)).convert_alpha()
        self.halfTransparent_room.fill((0, 125, 125, 50))

        # 输入服务器IP地址界面
        self.inputServerIPImage = pygame.image.load(self.inputServerIPPath).convert_alpha()
        self.inputServerIPImage = pygame.transform.scale(self.inputServerIPImage, self.screenSize)

        # 输入服务器端口号界面
        self.inputServerPortImage = pygame.image.load(self.inputServerPortPath).convert_alpha()
        self.inputServerPortImage = pygame.transform.scale(self.inputServerPortImage, self.screenSize)

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
                        if event.key in self.allKey:
                            if len(self.PutName) < 12:
                                self.PutName.append(self.Key2Text[event.key])
                        elif event.key == K_BACKSPACE:
                            if len(self.PutName) > 0:
                                self.PutName.pop(-1)
                        elif event.key == K_RETURN:
                            if len(self.PutName) > 0:
                                self.playerName = ''.join(self.PutName)
                                self.ProgressRate += 1
                    elif self.ProgressRate == 2:
                        # 选择进入房间或者设置按键
                        if event.key == K_w or event.key == K_s:
                            if self.choiceRoom:
                                self.choiceRoom = False
                                self.choiceSet = True
                            elif self.choiceSet:
                                self.choiceRoom = True
                                self.choiceSet = False
                        elif event.key == K_RETURN:
                            if self.choiceRoom:
                                self.ProgressRate = 3
                            elif self.choiceSet:
                                self.ProgressRate = 5
                        elif event.key == K_ESCAPE:
                            self.ProgressRate -= 1
                    elif self.ProgressRate == 3:
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
                    elif self.ProgressRate == 4:
                        # 输入服务器Port阶段
                        if event.key in self.allKey:
                            if len(self.PutPort) < 6:
                                self.PutPort.append(self.Key2Text[event.key])
                        elif event.key == K_BACKSPACE:
                            if len(self.PutPort) > 0:
                                self.PutPort.pop(-1)
                        elif event.key == K_RETURN:
                            if len(self.PutPort) > 0:
                                self.ServerPort = int(''.join(self.PutPort))
                                self.ProgressRate = 100
                        elif event.key == K_ESCAPE:
                            self.ProgressRate -= 1
                    elif self.ProgressRate == 5:
                        if event.key == K_RETURN:
                            self.ProgressRate = 6
                        elif event.key == K_ESCAPE:
                            self.ProgressRate = 3

                    elif self.ProgressRate == 6:
                        if event.key == K_ESCAPE:
                            self.ProgressRate = 5
            self.screen.fill('black')

            if self.ProgressRate == 1:# 开始菜单
                self.screen.blit(self.startMenuImage, (0, 0))
                self.textImage = self.myFont_Name.render(''.join(self.PutName), True, (0, 125, 125))
                self.screen.blit(self.textImage, (535, 495))
            elif self.ProgressRate == 2:# 选择进入房间或设置
                self.screen.blit(self.choiceRSImage, (0, 0))
                if self.choiceRoom:
                    self.screen.blit(self.halfTransparent_room, (232, 314))
                elif self.choiceSet:
                    self.screen.blit(self.halfTransparent_room, (232, 564))
                self.screen.blit(self.choiceRoomImage, (150, 250))
                self.screen.blit(self.choiceSettingImage, (150, 500))
            elif self.ProgressRate == 3:# 输入服务器IP地址
                self.screen.blit(self.inputServerIPImage, (0, 0))
                self.textImage = self.myFont_IP.render(''.join(self.PutIP), True, (0, 125, 125))
                self.screen.blit(self.textImage, (550, 475))
            elif self.ProgressRate == 4:# 输入服务器Port
                self.screen.blit(self.inputServerPortImage, (0, 0))
                self.textImage = self.myFont_Port.render(''.join(self.PutPort), True, (0, 125, 125))
                self.screen.blit(self.textImage, (550, 475))
            elif self.ProgressRate == 5:# 设置总界面
                self.screen.blit(self.settingAllImage, (0,0))
            elif self.ProgressRate == 6:# 设置按键界面
                self.screen.blit(self.settingKeyImage, (0,0))

            pygame.display.flip()
            self.fClock.tick(self.fps)
            if self.ProgressRate > 10:
                break
        pygame.quit()
start = StartGame()
start.start()

TankWar(start.ServerIP, start.ServerPort, start.playerName).play()