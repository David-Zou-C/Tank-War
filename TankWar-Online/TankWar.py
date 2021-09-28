
import sys, gc

from element import *
import socket
import json
import struct
from threading import Thread
import threading


threadLock = threading.Lock()

class TankWar:
    def __init__(self, ip, port, playerID=1):
        random.seed(1234)
        # 设定玩家ID
        self.playerID = playerID
        self.tankID = 999
        # 创建socket对象
        self.client = socket.socket()

        # 连接服务端
        self.client.connect((ip, port))

        # 接收数据缓冲区
        self.dataBuffer = bytes()

        # 初始化部分json格式
        self.get_json()

        # 首先发送自身的ID信息
        self.sendServer(f'My player id is {self.playerID}')

        # 是否开始进入游戏
        self.EnterGame = False

        # 发送自身信息的时间检查
        self.sendTime = time.time()

        # 发送自身信息的时间间隔
        self.sendTimeDist = 1/FPS

        t1 = Thread(target=self.receiveServer, args=(self.client,))
        t1.setDaemon(True)
        t1.start()


    def receiveServer(self, client):
        # 用一个线程接收服务端的信息
        while True:
            data = client.recv(1024)
            # print('接收到了，写入缓冲区中~')
            self.writeBuffer(data)


    def writeBuffer(self, bytes):
        threadLock.acquire()
        self.dataBuffer += bytes
        threadLock.release()

    def readBuffer(self):
        '''
        从缓冲区读取一个数据包的消息
        :return:
        '''
        threadLock.acquire()
        if len(self.dataBuffer) < self.headerSize:
            # print('小于头部信息')
            # 如果缓冲区小于头部信息的大小，则退出
            threadLock.release()
            return None
        # 如果大于头部大小，则首先从头部信息获取消息主体大小
        headerPack = struct.unpack('!3I', self.dataBuffer[:self.headerSize])  # 解码头部信息
        bodySize = headerPack[1]  # 获取消息主体大小
        # 判断缓冲区是否已经完整地接收到此数据包（头部+主体）
        if len(self.dataBuffer) >= self.headerSize+bodySize:
            # 如果已经完整地接收到了，则读取消息的正文内容
            body = self.dataBuffer[self.headerSize:self.headerSize+bodySize]
            # 读取完消息主体之后，丢弃此数据包
            self.dataBuffer = self.dataBuffer[self.headerSize+bodySize:]
            # 解码消息
            str_data = body.decode('utf-8')
            # print(str_data)
            # 返回消息
            threadLock.release()
            return str_data
        else:
            # 没有完整地接收到数据包
            # print('没有完整接收到数据包')
            threadLock.release()
            return None


    def sendServer(self, data):
        # print(data)
        # 消息正文
        body = data
        # 消息头部
        header = [self.header_ver, len(body), self.header_cmd]
        # 编码并打包
        headPack = struct.pack('!3I', *header)
        bodyPack = body.encode(encoding='utf-8')
        sendPack = headPack + bodyPack
        # 发送
        self.client.send(sendPack)

    def get_json(self):
        self.move_json = {
            'event type': 'move',
            'player id': self.playerID,
            'tank id': self.tankID,
            'move type': 'None',
        }
        self.fire_json = {
            'event type': 'fire',
            'player id': self.playerID,
            'tank id': self.tankID,
            'fire type': 'None',
        }
        self.key_json = {
            'event type': 'key',
            'player id': self.playerID,
            'tank id': self.tankID,
            'key type': 'None',
            'key': 'K_w'
        }
        self.position_json = {
            'event type': 'position',
            'player id': self.playerID,
            'tank id': self.tankID,
            'position': (0, 0)
        }
        self.connect_json = {
            'event type': 'connect',
            'player id': self.playerID,
            'tank id': self.tankID
        }
        self.scenes_json = {
            'event type': 'special scenes',
            'player id': self.playerID,
            'tank id': self.tankID,
            'lightning num': None,
            'lightning positions': None,
            'black hole num': None,
            'black hole positions': None
        }
        # 数据包头部定义
        self.header_ver = 1  # 数据包头部版本号
        self.header_cmd = 102  # 数据包头部指令
        self.headerSize = 12  # 数据包头部大小

    def play(self):
        # 等待加载游戏的指令
        while True:
            isLoad = self.readBuffer()
            # print('?')
            if isLoad and 'load game' in isLoad:
                print('load game...')
                LoadInfo = eval(isLoad)
                self.tankNum = LoadInfo['tank num']
                self.tankID = LoadInfo['tank id']
                self.get_json()
                break

        # pygame的初始化
        pygame.init()

        # 显示界面的创造
        ## 部分常数值
        # 屏幕尺寸
        screenSize = width, height = 1440, 900
        # 整个地图尺寸
        mapSize = MapWidth, MapHeight = 1440*2, 900*2
        # 小地图尺寸
        smallMapSize = smallMapWidth, smallMapHeight = 400, 200
        # 用户信息界面尺寸
        userInterfaceSize = userInterfaceWidth, userInterfaceHeight = 500, 100
        speed = 200
        fps = FPS


        # 设置显示对象
        screen = pygame.display.set_mode(screenSize)
        # 初始化整个地图
        totalMap = pygame.Surface(mapSize)
        # 初始化小地图界面
        smallMap = pygame.Surface(smallMapSize).convert_alpha()
        # 初始化用户信息界面
        userInterface = pygame.Surface(userInterfaceSize)

        # 定义刷新时间对象
        fClock = pygame.time.Clock()

        # 加载所有图片
        all_image.LoadImg()
        all_image.getMask()
        # 所有场景元素的组
        Scene_Group = pygame.sprite.Group()

        # 不可穿过的组
        NoPassing_Group = pygame.sprite.Group()

        # 可以被毁灭的组
        CanDestroy_Group = pygame.sprite.Group()

        # 随机生成场景元素的类
        randomScene = RandomCreate(MapWidth, MapHeight)

        # 随机生成草地
        Num_Grass = 10
        Grass_range = 60
        Grass_Group = randomScene.Grass(Num_Grass, Grass_range, Scene_Group)
        # 加入对应的大组
        Scene_Group.add(*Grass_Group)

        # 随机生成河流
        Num_River = 10
        River_range = 50
        River_Group = randomScene.River(Num_River, River_range, Scene_Group)
        # 加入对应的大组
        Scene_Group.add(*River_Group)
        NoPassing_Group.add(*River_Group)

        # 随机生成砖墙
        Num_Brick = 15
        Brick_range = 10
        Brick_Group = randomScene.Brick(Num_Brick, Brick_range, Scene_Group)
        # 加入对应的大组
        Scene_Group.add(*Brick_Group)
        NoPassing_Group.add(*Brick_Group)
        CanDestroy_Group.add(*Brick_Group)

        # 随机生成铁墙
        Num_Iron = 20
        Iron_range = 10
        Iron_Group = randomScene.Iron(Num_Iron, Iron_range, Scene_Group)
        # 加入对应的大组
        Scene_Group.add(*Iron_Group)
        NoPassing_Group.add(*Iron_Group)
        CanDestroy_Group.add(*Iron_Group)

        # 随机生成N个坦克，根据坦克的大小设定了范围，避免越过边界
        Num_tank = self.tankNum  # 坦克数量
        Tank_Group = randomScene.Tank(Num_tank, speed, NoPassing_Group)
        # 加入对应的大组
        NoPassing_Group.add(*Tank_Group)
        CanDestroy_Group.add(*Tank_Group)

        Tank_list = Tank_Group.sprites()
        target_tank = Tank_list[self.tankID]
        target_tank_id = 0
        target_tank.bordered = True

        display_left, display_top = target_tank.rect.left, target_tank.rect.top
        # 子弹组
        Bullet_Group = pygame.sprite.Group()
        # 爆炸组
        Boom_Group = pygame.sprite.Group()
        # 特殊场景
        SpecialScenes_Group = pygame.sprite.Group()
        # 被黑洞吞噬的组
        BlackHole_Swallowed_Group = pygame.sprite.Group()
        SpecialScenes_RandomTime = time.time()  # 随机场景时间初始化
        Num_SpecialScenes = 2   # 随机场景每次生成最大数量
        # 加入“所有”组，在之后一起绘制
        All_Group = pygame.sprite.Group()
        All_Group.add(*Tank_Group, *Bullet_Group, *Boom_Group, *Scene_Group)
        All_Group = pygame.sprite.LayeredUpdates(*All_Group)

        # 用户信息界面
        User_Group = pygame.sprite.Group()


        # 按键列表
        All_Key_list = [K_j, K_b, K_k]

        # 等待发送开始信号
        print('Already!')
        while True:
            # print('read buffer...')
            data = self.readBuffer()
            if data == 'start game':
                break
        print('get start!')
        self_state_changed = False
        # 事件主循环
        running = True
        while running:
            # 事件处理
            for event in pygame.event.get():
                # 退出
                if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                    self.sendServer('I quit')
                    self.client.close()
                    sys.exit()

                if event.type == KEYDOWN or event.type == KEYUP:
                    if target_tank.alive() and Tank_Group in target_tank.groups():
                        if event.key in target_tank.move_Key:
                            if event.type == KEYUP:
                                target_tank.key_to_move[event.key] = False
                            else:
                                target_tank.isMove = True
                                target_tank.key_to_move[event.key] = True

                        if event.key in All_Key_list:
                            # selfState = target_tank.get_state()
                            # selfState['player id'] = self.playerID
                            # print('Key self')
                            # self.sendServer(str(selfState))

                            send2Ser = self.key_json.copy()
                            if event.type == KEYUP:
                                send2Ser['key type'] = KEYUP
                            else:
                                send2Ser['key type'] = KEYDOWN
                            send2Ser['key'] = event.key
                            self.sendServer(str(send2Ser))



            # print('get message?')
            event_storage = []
            event_occurs = False
            r_data = self.readBuffer()
            while r_data:
                event_occurs = True
                event_storage.append(r_data)
                r_data = self.readBuffer()
            if event_occurs:
                event_occurs = False
                # print('got message!')
                for each_str_json in event_storage:
                    each_json = eval(each_str_json)
                    targetID = each_json['tank id']
                    # 按键处理
                    if each_json['event type'] == 'key':
                        targetID_key_type = each_json['key type']
                        targetID_key = each_json['key']
                        targetID_tank = Tank_list[targetID]
                        if targetID_key_type == KEYDOWN:

                            if targetID_tank.alive() and Tank_Group in targetID_tank.groups():
                                if targetID_key in targetID_tank.move_Key:
                                    targetID_tank.isMove = True
                                    targetID_tank.key_to_move[targetID_key] = True
                                elif targetID_key == K_j:
                                    targetID_tank.fireLaserBullet()
                                elif targetID_key == K_k:
                                    targetID_tank.fireNormalBullet()
                                elif targetID_key == K_b:
                                    targetID_tank.selfExplosion()
                        elif targetID_key_type == KEYUP:
                            if targetID_key in targetID_tank.move_Key:
                                targetID_tank.key_to_move[targetID_key] = False
                    # 玩家角色信息更新
                    elif each_json['event type'] == 'tank state':
                        if targetID != self.tankID:
                            Tank_list[targetID].change_state(each_json)

                    # 特殊场景信息更新
                    elif each_json['event type'] == 'special scenes':
                        lightning_Group = pygame.sprite.Group()
                        for pl in each_json['lightning positions']:
                            lightning = Lightning(all_image.LightningImageList, pl)
                            lightning.get_mask_list(all_image.LightningMaskList)
                            lightning_Group.add(lightning)
                        blackhole_Group = pygame.sprite.Group()
                        for pb in each_json['black hole positions']:
                            blackhole = BlackHole(all_image.BlackHoleImageList, pb)
                            blackhole.get_mask_list(all_image.BlackHoleMaskList)
                            blackhole_Group.add(blackhole)
                        SpecialScenes_Group.add(*lightning_Group, *blackhole_Group)
            # 事件处理结束 #
            # print('tank self state')
            if (Tank_Group in target_tank.groups()) and (time.time() - self.sendTime > self.sendTimeDist):
                self.sendTime = time.time()
                selfState = Tank_list[self.tankID].get_state()
                selfState['tank id'] = self.tankID
                # print('发送状态', selfState)
                self.sendServer(str(selfState))
            elif not target_tank.alive():
                selfState = Tank_list[self.tankID].get_state()
                selfState['tank id'] = self.tankID
                # print('发送状态', selfState)
                self.sendServer(str(selfState))
            # 检查子弹组与坦克组的相交情况
            collide_dict = pygame.sprite.groupcollide(Bullet_Group, CanDestroy_Group, False, False)
            for each_Bullet in collide_dict.keys():
                for Bullet_collide_e in collide_dict[each_Bullet]:
                    if Bullet_collide_e != each_Bullet.Tank:
                        if isinstance(Bullet_collide_e, Tank):
                            each_Bullet.Tank.kill_tank_name_list.append(Bullet_collide_e.tank_name)
                            Bullet_collide_e.be_hit(each_Bullet.Type)
                        elif isinstance(Bullet_collide_e, Brick):
                            each_Bullet.Tank.destroy_scene_type_list.append(Bullet_collide_e.WallType)
                            Bullet_collide_e.be_hit(each_Bullet.Type)
                        if isinstance(each_Bullet, NormalBullet):
                            each_Bullet.destroy()

            # 随机生成特殊场景
            if self.tankID == 0:
                if time.time() - SpecialScenes_RandomTime > random.randint(2, 5):
                    SpecialScenes_RandomTime = time.time()
                    t = random.randint(0, 11)
                    if t > 5:
                        nL = random.randint(0,Num_SpecialScenes)
                        Lightning_Group = randomScene.Lightning(nL, SpecialScenes_Group)
                        nB = random.randint(0,Num_SpecialScenes)
                        BlackHole_Group = randomScene.BlackHole(nB, SpecialScenes_Group)
                        # 将生成的场景数据发送到服务端
                        self.scenes_json['lightning num'] = nL
                        self.scenes_json['black hole num'] = nB
                        tempLG = []
                        for p in Lightning_Group.sprites():
                            tempLG.append((p.rect.left, p.rect.top))
                        self.scenes_json['lightning positions'] = tempLG
                        tempBH = []
                        for p in BlackHole_Group.sprites():
                            tempBH.append((p.rect.left, p.rect.top))
                        self.scenes_json['black hole positions'] = tempBH
                        self.sendServer(str(self.scenes_json))

            # 检查特殊场景与其它组的相交情况
            spread_to = pygame.sprite.groupcollide(SpecialScenes_Group, CanDestroy_Group, False, False, pygame.sprite.collide_mask)
            for each_Hit_SS in spread_to.keys():
                for each_beHit in spread_to[each_Hit_SS]:
                    if isinstance(each_beHit, Tank):
                        each_beHit.be_hit(each_Hit_SS.Type)
                    elif isinstance(each_beHit, Brick):
                        each_beHit.be_hit(each_Hit_SS.Type)
            # 随机场景结束 #

            # pygame.sprite.LayeredUpdates(*All_Group)
            # print(All_Group.layers()) # 显示所有层数
            # screen.fill('black')
            smallMap.fill((100, 255, 100, 120))
            UserInfo(smallMap, target_tank).draw_blood_bar()
            UserInfo(smallMap, target_tank).draw_skill_bar()
            totalMap.fill('black')
            BlackHole_Swallowed_Group.update(updateGroupName='BlackHole_Swallowed_Group')
            All_Group.update(updateGroupName='All_Group',
                             size=mapSize,
                             All_Group=All_Group,
                             Bullet_Group=Bullet_Group,
                             Boom_Group=Boom_Group,
                             Tank_Group=Tank_Group,
                             NoPassing_Group=NoPassing_Group,
                             CanDestroy_Group=CanDestroy_Group,
                             BlackHole_Swallowed_Group=BlackHole_Swallowed_Group,
                             SpecialScenes_Group=SpecialScenes_Group)

            All_Group.add(*Tank_Group, *Bullet_Group, *Boom_Group, *SpecialScenes_Group)
            All_Group.draw(totalMap)

            if target_tank:
                target_left, target_top = target_tank.rect.left, target_tank.rect.top
                cal_left, cal_top = target_left - width/2, target_top - height/2
                cal_left = cal_left if cal_left+width <= MapWidth else  MapWidth-width
                cal_top = cal_top if cal_top+height <= MapHeight else MapHeight-height
                display_left = cal_left if cal_left>=0 else 0
                display_top = cal_top if cal_top>=0 else 0

            display_Rect = screen.get_rect()
            display_Rect.left, display_Rect.top = display_left, display_top
            display_Sur = totalMap.subsurface(display_Rect)
            screen.blit(display_Sur, (0,0))
            screen.blit(smallMap, (width-smallMapWidth, 0))
            # gc.collect()
            pygame.display.flip()
            fClock.tick(fps)


if __name__ == "__main__":
    # print('输入IP地址：')
    # ip = input()
    # print("输入端口号：")
    # port = int(input())
    # print("你的玩家ID（0~9）：")
    # id = int(input())
    ip = '127.0.0.1'
    port = 1234
    id = 2
    if 0 <= id < 10:
        pass
    else:
        id = random.randint(0, 9)
    TankWar(ip, port, id).play()

