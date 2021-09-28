#! /usr/bin/python
# -*- coding: UTF-8 -*-

import sys, gc

from element import *
import socket
import json
from threading import Thread
import threading

# # 定义联机时数据发送的格式
# trans_data = {
#     'event type': 'move',
#     'player id': None,
#     'action': 'None',
# }


#! 坦克大战开始
class TankWar:
    def __init__(self):

        # 设定玩家ID，为多人联机做准备
        self.playerID = 1


    def play(self):
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
        Num_Grass = 20
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
        Brick_range = 100
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
        Num_tank = 100  # 坦克数量
        Tank_Group = randomScene.Tank(Num_tank, speed, NoPassing_Group)
        # 加入对应的大组
        NoPassing_Group.add(*Tank_Group)
        CanDestroy_Group.add(*Tank_Group)

        Tank_list = Tank_Group.sprites()
        target_tank = Tank_list[self.playerID]
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
        # 事件主循环
        running = True
        while running:

            # 事件处理
            for event in pygame.event.get():
                # 退出
                if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                    sys.exit()

                if event.type == KEYDOWN:
                    if Tank_Group:
                        if event.key == K_TAB:  # 切换目标操作坦克
                            target_tank.bordered = False
                            target_tank.isMove = False
                            target_tank_id = target_tank_id + 1 if target_tank_id < len(Tank_list) - 1 else 0
                            while not Tank_list[target_tank_id].alive():
                                target_tank_id = target_tank_id + 1 if target_tank_id < len(Tank_list) - 1 else 0
                            else:
                                target_tank = Tank_list[target_tank_id]
                                target_tank.bordered = True
                        if target_tank.alive() and Tank_Group in target_tank.groups():
                            if event.key in target_tank.move_Key:
                                target_tank.isMove = True
                                target_tank.key_to_move[event.key] = True
                            elif event.key == K_j: # 发射激光弹
                                target_tank.fireLaserBullet()
                            elif event.key == K_k: # 发射普通子弹
                                target_tank.fireNormalBullet()
                            elif event.key == K_b: # 自爆
                                target_tank.selfExplosion()
                        if event.key == K_o: # 测试用 ---- 所有坦克一起发射激光弹
                            for each_Tank in Tank_Group:
                                each_Tank.fireLaserBullet()
                        if event.key == K_i: # 测试用 ---- 所有坦克一起发射普通子弹
                            for each_Tank in Tank_Group:
                                each_Tank.fireNormalBullet()

                elif event.type == KEYUP:
                    if event.key in target_tank.move_Key:
                        target_tank.key_to_move[event.key] = False
            #b 事件处理结束 #

            #! 检查子弹组与坦克组的相交情况
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

            #! 随机时间随机生成特殊场景
            if time.time() - SpecialScenes_RandomTime > random.randint(2, 5):
                SpecialScenes_RandomTime = time.time()
                t = random.randint(0, 11)
                if t > 5:
                    n = random.randint(0,Num_SpecialScenes)
                    Lightning_Group = randomScene.Lightning(n, SpecialScenes_Group)
                    BlackHole_Group = randomScene.BlackHole(n, SpecialScenes_Group)
                    SpecialScenes_Group.add(*Lightning_Group, *BlackHole_Group)
            #! 检查特殊场景与其它组的相交情况
            spread_to = pygame.sprite.groupcollide(SpecialScenes_Group, CanDestroy_Group, False, False, pygame.sprite.collide_mask)
            for each_Hit_SS in spread_to.keys():
                for each_beHit in spread_to[each_Hit_SS]:
                    if isinstance(each_beHit, Tank):
                        each_beHit.be_hit(each_Hit_SS.Type)
                    elif isinstance(each_beHit, Brick):
                        each_beHit.be_hit(each_Hit_SS.Type)
            #b 随机场景结束 #

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
    TankWar().play()
