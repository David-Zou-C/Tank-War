#! /usr/bin/python
# -*- coding: UTF-8 -*-

import random, time, os, pygame
from pygame.locals import *
from pygame.sprite import Sprite, DirtySprite

tankPath = "img/Tank.png"
bulletPath = "img/bullet_laser_02.png"
boomPath = "img/boomAnimation"
FPS = 60

#! 图片加载及预处理
class ImgPath:
    def __init__(self):
        self.tankPath = "img/Tank.png"  # 坦克图片地址
        self.bulletPath = "img/bullet_laser_02.png"
        self.boomPath = "img/boomAnimation"
        self.grassPath = "img/grass.png"
        self.riverPath = "img/river.png"
        self.brickPath = "img/brick wall.png"
        self.normalBulletPath = "img/bullet_normal.png"
        self.ironPath = "img/iron.png"
        self.lightningPath = "img/lightningAnimation/Animation-img"
        self.blackHolePath = "img/blackHoleAnimation/Animation"
        self.bloodBarPath = "img/user-info/blood bar.png"
        self.skillBarPath = "img/user-info/skill bar.png"
        self.explosionPath = "img/self exploding"

    def LoadImg(self):
        self.TankImage = pygame.image.load(self.tankPath).convert_alpha()
        self.TankImage = pygame.transform.scale(self.TankImage, (64, 64))

        self.LaserBulletImage = pygame.image.load(self.bulletPath).convert_alpha()
        self.GrassImage = pygame.image.load(self.grassPath).convert_alpha()
        self.RiverImage = pygame.image.load(self.riverPath).convert_alpha()
        self.BrickImage = pygame.image.load(self.brickPath).convert_alpha()
        self.NormalBulletImage = pygame.image.load(self.normalBulletPath).convert_alpha()
        self.BoomImageList = self.LoadAnimation(self.boomPath, self.TankImage.get_rect().size)
        self.IronImage = pygame.image.load(self.ironPath).convert_alpha()
        self.LightningImageList = self.LoadAnimation(self.lightningPath, all_const.Lightning_Size)
        self.BlackHoleImageList = self.LoadAnimation(self.blackHolePath, all_const.BlackHole_Size)
        self.BloodBarImage = pygame.image.load(self.bloodBarPath).convert_alpha()
        self.SkillBarImage = pygame.image.load(self.skillBarPath).convert_alpha()
        self.ExplosionImageList = self.LoadAnimation(self.explosionPath, all_const.ExplosionSize)

    def getMask(self):
        self.TankMask = pygame.mask.from_surface(self.TankImage)
        self.LaserBulletMask = pygame.mask.from_surface(self.LaserBulletImage)
        self.BrickMask = pygame.mask.from_surface(self.BrickImage)
        self.IronMask = pygame.mask.from_surface(self.IronImage)
        self.LightningMaskList = [pygame.mask.from_surface(x) for x in self.LightningImageList]
        self.BlackHoleMaskList = [pygame.mask.from_surface(x) for x in self.BlackHoleImageList]
        self.SelfExplosionMaskList = [pygame.mask.from_surface(x) for x in self.ExplosionImageList]

    def LoadAnimation(self, filepath, size=None):
        imageName_list = os.listdir(filepath)
        image_list = []
        for imageName in imageName_list:
            tempImage = pygame.image.load(f"{filepath}/{imageName}").convert_alpha()
            if size:
                tempImage = pygame.transform.scale(tempImage, size)
            image_list.append(tempImage)
        return image_list


#b 加载所有元素的图片，并存放到一个对象中
all_image = ImgPath()


#! 显示层管理
class LayerManage:
    def __init__(self):
        # 坦克
        self.TankLayer = 10
        # 普通子弹
        self.NormalBulletLayer = 10
        # 激光
        self.LaserBulletLayer = 20
        # 爆炸
        self.BoomLayer = 9
        # 草地
        self.GrassLayer = 100
        # 河流
        self.RiverLayer = 8
        # 砖墙
        self.BrickLayer = 8
        # 铁墙
        self.IronLayer = 8
        # 第一类墙
        self.Wall_1 = 10
        # 第二类墙
        self.Wall_2 = 30
        # 闪电
        self.Lightning = 200
        # 自爆
        self.SelfExplosionLayer = 150

#b 管理所有元素的显示层
all_layer = LayerManage()


#? 常数值设置
class SetNum:
    def __init__(self):
        self.TankLife = 200 # 坦克的初始生命值
        self.TankSkill = 100 # 坦克的初始技能值
        self.NormalBulletSpeed = 10 # 普通子弹的速度
        self.fire_normal_freq = 10 # 每秒发射次数
        self.NormalBulletRange = 800 # 普通子弹的射程
        self.LaserContainTime = 0.5 # 激光持续时间
        self.Laser_Skill_Expend = 20 # 激光初始化消耗
        self.fire_laser_freq = 2 # 激光每秒发射最大次数
        self.Lightning_Size = (400, 400) # 更改闪电的大小
        self.Lightning_playTime = 2 # 闪电动画全部播放一次的最短时间
        self.Lightning_ContainTime = 4 # 闪电出现的持续时间
        self.blood_bar_color = (255, 0, 0, 255) # 血条框的颜色
        self.blood_bar_line_width = 3 # 血条框的厚度
        self.BlackHole_Size = (300, 300) # 更改黑洞的大小
        self.BlackHole_playTime = 3 # 黑洞动画全部播放一次的最短时间
        self.BlackHole_containTime = 10 # 黑洞的持续时间
        self.SelfExplosionTime = 1 # 自爆动画完整播放一次的最短时间
        self.SelfExplosionContainTime = 3 # 自爆总持续时间
        self.ExplosionSize = (300, 300) # 自爆图片的大小


#b 所有常数值
all_const = SetNum()


#! 随机生成
"""
    随机生成效果简介：
        需要指定生成的块数和大小数量。
        将随机生成指定块数的场景元素，每一块都由相同指定大小数量的场景元素相连形成的。
        还可以在函数内部设置上下左右随机的概率，以控制每一块的形状，例如增大上下的概率，每块将容易形成纵向长条的形状。
        
    随机生成算法流程：
        1. 在地图大小范围内，随机生成两个数（一个坐标点），以此点生成一个对象。
        2. 将其与已经绘制在地图上的精灵组进行碰撞检测，是否与地图上已存在的精灵对象发生重叠。若是，则重新随机，否则下一步。
        3. 将成功随机生成的对象存入精灵组中，再随机从这个组中选择一个精灵，以这个精灵为中心，从上下左右四个方向随机挑出一个。
           例如，选择了上，则在该精灵上方紧挨的位置新建一个同样的对象，由于每个对象都有一个规则的矩形区域，所以很容易创建出与自身一样的上下左右四个相邻位置的精灵对象。
           将新建的这个精灵对象与已经成功生成的精灵组中进行碰撞检测，再与地图已存在的组检测，如果都没有碰撞，就将其添加到成功生成的组中，否则，换一个方向，若四个都不行，则重选一个精灵。
           若所有精灵都无法生成相邻的对象，则撤销这个精灵组，从第1步重新开始。
        4. 若在随机的时候出现空间的浪费，导致本来能随机生成的数量变得无法生成，此时，则会陷入死循环。
           添加时间限制，若一定时间，例如0.5s内无法完成指定块数和大小的场景的随机生成，则表示有空间被浪费，则撤销之前生成的块数，重新再来。
           如果总时间超过一定阈值，则进行报错（以下没有设置报错，需要根据地图自行合理设置块数和每块的大小，否则有可能进入死循环）。
"""
class RandomCreate:
    def __init__(self, mapWidth, mapHeight):
        self.mapWidth = mapWidth
        self.mapHeight = mapHeight
        pass

    def overRange(self, position, width, height):
        if 0 <= position[0] <= self.mapWidth - width:
            if 0 <= position[1] <= self.mapHeight - height:
                return False
        return True

    def Collide(self, elem, Group):
        return pygame.sprite.spritecollide(elem, Group, False)

    def element(self, image, Num, RangeNum, NoCollideGroup, Ele):
        t = time.time()
        imageWidth, imageHeight = image.get_width(), image.get_height()
        # 位置变更函数
        f1 = lambda x: (x[0] + imageWidth, x[1]) #
        f2 = lambda x: (x[0] - imageWidth, x[1])
        f3 = lambda x: (x[0], x[1] + imageHeight)
        f4 = lambda x: (x[0], x[1] - imageHeight)
        fn = [f1, f2, f3, f4]
        #? 可调整四个方向的概率，例如增大上下方的概率
        #? fn += [f1, f2] * 10
        # 随机生成
        Ele_Group = pygame.sprite.Group()
        li_position = []
        for n in range(Num):
            ele = Ele(image)
            ele.get_mask()
            while True:
                position = random.randint(0, self.mapWidth - imageWidth), random.randint(0, self.mapHeight - imageHeight)
                ele.location(position)
                if position not in li_position:
                    if not self.Collide(ele, Ele_Group) and not self.Collide(ele, NoCollideGroup):
                        break
            li_position.append(position)
            Ele_Group.add(ele)
            temp_li_position = [position]
            for j in range(RangeNum):
                ele = Ele(image)
                ele.get_mask()
                while True:
                    tempPosition = random.choice(temp_li_position)
                    fc = random.choice(fn)
                    newPosition = fc(tempPosition)
                    ele.location(newPosition)
                    if newPosition in li_position or self.Collide(ele, Ele_Group) or self.Collide(ele, NoCollideGroup):
                        pass
                    else:
                        li_position.append(newPosition)
                        temp_li_position.append(newPosition)
                        ele.get_mask()
                        Ele_Group.add(ele)
                        break
                    if time.time() - t > 1:
                        return self.element(image, Num, RangeNum, NoCollideGroup, Ele)
        return Ele_Group

    def River(self, Num, RangeNum, NoCollideGroup):
        River_Group = self.element(all_image.RiverImage, Num, RangeNum, NoCollideGroup, River)
        return River_Group

    def Grass(self, Num, RangeNum, NoCollideGroup):
        Grass_Group = self.element(all_image.GrassImage, Num, RangeNum, NoCollideGroup, Grass)
        return Grass_Group

    def Brick(self, Num, RangeNum, NoCollideGroup):
        Brick_Group = self.element(all_image.BrickImage, Num, RangeNum, NoCollideGroup, Brick)
        return Brick_Group

    def Iron(self, Num, RangeNum, NoCollideGroup):
        Iron_Group = self.element(all_image.IronImage, Num, RangeNum, NoCollideGroup, Iron)
        return Iron_Group

    def Tank(self, Num, speed, NoCollideGroup):
        image = all_image.TankImage
        imageWidth, imageHeight = image.get_width(), image.get_height()
        Tank_Group = pygame.sprite.Group()
        if Num == 1:
            position = random.randint(0, self.mapWidth - imageWidth), \
                       random.randint(0, self.mapHeight - imageHeight)
            tank = Tank(all_image.TankImage, position, speed, f'random-only1',
                        direction=random.choice(['up', 'down', 'left', 'right']))
            while self.Collide(tank, Tank_Group) or self.Collide(tank, NoCollideGroup):
                tank.rect.left, tank.rect.top = random.randint(0, self.mapWidth - imageWidth), \
                                                random.randint(0, self.mapHeight - imageHeight)
            return tank
        for i in range(Num):
            position = random.randint(0, self.mapWidth - imageWidth), \
                       random.randint(0, self.mapHeight - imageHeight)
            tank = Tank(all_image.TankImage, position, speed, f'random-{i}',
                        direction=random.choice(['up', 'down', 'left', 'right']))
            while self.Collide(tank, Tank_Group) or self.Collide(tank, NoCollideGroup):
                tank.rect.left, tank.rect.top = random.randint(0, self.mapWidth - imageWidth), \
                                                random.randint(0, self.mapHeight - imageHeight)
            Tank_Group.add(tank)
        return Tank_Group

    def Lightning(self, Num, NoCollideGroup):
        image_list = all_image.LightningImageList
        imageWidth, imageHeight = image_list[0].get_width(), image_list[0].get_height()
        Lightning_Group = pygame.sprite.Group()
        for i in range(Num):
            position = random.randint(0, self.mapWidth - imageWidth), \
                       random.randint(0, self.mapHeight - imageHeight)
            lightning = Lightning(image_list, position)
            lightning.get_mask_list(all_image.LightningMaskList)
            while self.Collide(lightning, Lightning_Group) or self.Collide(lightning, NoCollideGroup):
                lightning.rect.left, lightning.rect.top = random.randint(0, self.mapWidth - imageWidth),\
                                                          random.randint(0, self.mapHeight - imageHeight)
            Lightning_Group.add(lightning)
        return Lightning_Group

    def BlackHole(self, Num, NoCollideGroup):
        image_list = all_image.BlackHoleImageList
        imageWidth, imageHeight = image_list[0].get_width(), image_list[0].get_height()
        blackHole_Group = pygame.sprite.Group()
        for i in range(Num):
            position = random.randint(0, self.mapWidth - imageWidth), \
                       random.randint(0, self.mapHeight - imageHeight)
            blackHole = BlackHole(image_list, position)
            blackHole.get_mask_list(all_image.BlackHoleMaskList)
            while self.Collide(blackHole, blackHole_Group) or self.Collide(blackHole, NoCollideGroup):
                blackHole.rect.left, blackHole.rect.top = random.randint(0, self.mapWidth - imageWidth),\
                                                          random.randint(0, self.mapHeight - imageHeight)
            blackHole_Group.add(blackHole)
        return blackHole_Group

#! 坦克类，可指定速度
class Tank(DirtySprite):
    '''
    坦克类，继承DirtySprite
    '''

    def __init__(self, image, position, speed, tank_name, direction='up', layer=all_layer.TankLayer):
        DirtySprite.__init__(self)

        # 读取坦克的图片，并获得各个方向的坦克
        self.tank_load = image
        self.tank_up = self.tank_load
        self.tank_left = pygame.transform.rotate(self.tank_up, 90)
        self.tank_down = pygame.transform.rotate(self.tank_left, 90)
        self.tank_right = pygame.transform.rotate(self.tank_down, 90)
        self.image = self.tank_up
        self.mask = pygame.mask.from_surface(self.image)
        # 坦克的方向
        self.direction_list = ['up', 'down', 'left', 'right']
        self.tank_direction_list = [self.tank_up, self.tank_down, self.tank_left, self.tank_right]
        self.direction = direction
        self.direct()  # 将方向与Surface对象绑定（字典）
        self.image = self.Direc_tank[self.direction]

        # 设置坦克的位置
        self.rect = self.tank_load.get_rect()
        self.position = position
        self.rect.left, self.rect.top = self.position

        # 坦克的生命值
        self.totalLife = all_const.TankLife
        self.life = self.totalLife
        self.autoAddLife_time = time.time()

        # 坦克的技能条
        self.totalSkill = all_const.TankSkill
        self.skill = self.totalSkill
        self.autoAddSkill_time = time.time()

        # 坦克的速度
        self.speed = speed / FPS

        # 坦克的ID
        self.tank_name = tank_name

        # 坦克的方向
        self.direction = direction

        # 坦克的子弹
        self.laserBullet = all_image.LaserBulletImage
        self.normalBullet = all_image.NormalBulletImage
        self.laserBulletExpend = all_const.Laser_Skill_Expend

        # 坦克所在的图层
        self._layer = layer

        # 是否绘制坦克的血条
        self.bloodBar = True

        # 是否绘制坦克的边框
        self.bordered = False
        self.border_direct()  # 对各个方向绘制带边框的Surface对象，并得到绑定的字典

        # 坦克的运动状态
        self.move_Key = [K_w, K_s, K_a, K_d]
        self.isMove = False
        self.move_Direct = self.move_toUp, self.move_toLeft, self.move_toDown, self.move_toRight = [False for _ in range(4)]
        self.key_to_move = dict(zip(self.move_Key, self.move_Direct))

        # 是否发射子弹
        self.fired_laser_time = 0 # 上次发射激光子弹的时间
        self.fire_laser_freq = all_const.fire_laser_freq # 激光子弹发射最大频率（每秒次数）
        self.fire_laser_contain_time = all_const.LaserContainTime # 激光子弹持续时间


        self.fired_normal_time = 0 # 上次发射普通子弹的时间
        self.fire_normal_freq = all_const.fire_normal_freq # 普通子弹发射最大频率（每秒次数）


        # 是否爆炸
        self.BoomImageList = all_image.BoomImageList
        self.explode = False

        # 记录坦克所击毁的坦克名称
        self.kill_tank_name_list = []
        # 记录坦克所击毁的场景元素名称
        self.destroy_scene_type_list = []

        # 被击中的时间
        self.beHitType = {'laser bullet': 0, 'normal bullet': 0, 'lightning': 0, 'self explosion': 0}

    def update(self, *args, **kwargs) -> None:

        # 被黑洞吞噬
        if kwargs['updateGroupName'] == 'BlackHole_Swallowed_Group':
            if time.time() - self.BlackHole_Swallowed_Time > 10:
                self.kill()
                self.rebirth()
            return
        # 判断坦克生命值
        if self.life <= 0:
            self.boom()
        else:
            pass

        if time.time() - self.autoAddLife_time >= 1:
            if self.life < self.totalLife:
                self.life += 1

        self.mapSize = kwargs['size']
        self.Tank_Group = kwargs['Tank_Group']
        self.NoPassing_Group = kwargs['NoPassing_Group']
        self.CanDestroy_Group = kwargs['CanDestroy_Group']
        self.Bullet_Group = kwargs['Bullet_Group']
        self.Boom_Group = kwargs['Boom_Group']
        self.BlackHole_Swallowed_Group = kwargs['BlackHole_Swallowed_Group']
        self.SpecialScenes_Group = kwargs['SpecialScenes_Group']
        self.dirty = 0

        if self.bordered:
            self.image = self.Direc_tank_border[self.direction]
        else:
            self.image = self.Direc_tank[self.direction]

        if self.bloodBar:
            self.image = self.image.copy()
            self.display_blood_bar(self.image, self.rect, 3)

        if self.isMove:
            for i, state in enumerate(self.key_to_move.values()):
                if state:
                    self.move(self.NoPassing_Group, self.mapSize, direction=self.direction_list[i])
                    break
        else:
            self.move_Direct = self.move_toUp, self.move_toLeft, self.move_toDown, self.move_toRight = [False for _ in range(4)]


        self.autoAdd()

        if self.explode:
            self.Boom_Group.add(self.boomAnimation)
            self.boomAnimation.boom()
            self.kill()
            del self



    def move(self, Group, size, direction=None, speed=None):
        '''
        移动坦克
        :param speed: 速度
        :return: None
        '''
        if speed:
            self.speed = speed

        if direction is not None and direction in self.direction_list:
            self.direction = direction
            tempRect = self.rect.copy()

            if direction == 'up':
                self.rect.move_ip(0, -self.speed)
            elif direction == 'left':
                self.rect.move_ip(-self.speed, 0)
            elif direction == 'down':
                self.rect.move_ip(0, self.speed)
            elif direction == 'right':
                self.rect.move_ip(self.speed, 0)

            leftRange = size[0]-self.rect.width
            topRange = size[1]-self.rect.height
            if (0 <= self.rect.left <= leftRange) and (0 <= self.rect.top <= topRange):
                overRange = False
            else:
                overRange = True

            if self.move_check(Group) or overRange:
                self.rect = tempRect
            else:
                del tempRect

    def move_check(self, Group):
        Group.remove(self)
        collide = pygame.sprite.spritecollideany(self, Group)
        Group.add(self)
        if collide:
            return True
        else:
            return False

    def direct(self):
        self.Direc_tank = dict(zip(self.direction_list, self.tank_direction_list))

    def update_layer(self, layer):
        self._layer = layer

    def border_direct(self, color='green', width=2):
        self.tank_border_up = self.tank_up.copy()
        self.tank_border_down = self.tank_down.copy()
        self.tank_border_left = self.tank_left.copy()
        self.tank_border_right = self.tank_right.copy()
        pygame.draw.rect(self.tank_border_up, color, (0, 0, self.rect.width, self.rect.height), width)
        pygame.draw.rect(self.tank_border_down, color, (0, 0, self.rect.width, self.rect.height), width)
        pygame.draw.rect(self.tank_border_left, color, (0, 0, self.rect.width, self.rect.height), width)
        pygame.draw.rect(self.tank_border_right, color, (0, 0, self.rect.width, self.rect.height), width)
        self.Direc_tank_border = {'up': self.tank_border_up,
                                  'down': self.tank_border_down,
                                  'left': self.tank_border_left,
                                  'right': self.tank_border_right}

    def fireNormalBullet(self):
        if time.time() - self.fired_normal_time > 1/self.fire_normal_freq:
            temp = NormalBullet(self.normalBullet, self)
            self.Bullet_Group.add(temp)
            temp.fire()
            self.fired_normal_time = time.time()

    def fireLaserBullet(self):
        if self.skill < self.laserBulletExpend:
            return
        elif time.time() - self.fired_laser_time > 1/self.fire_laser_freq:
            self.skill -= self.laserBulletExpend
            temp = BulletLaser(self.laserBullet, self)
            self.Bullet_Group.add(temp)
            temp.fire()
            self.fired_laser_time = time.time()

    def boom(self):
        self.life = 0
        self.explode = True
        self.exploding(self.BoomImageList)

    def exploding(self, imageList):
        self.boomAnimation = Boom(imageList, self)

    def rebirth(self):
        self.rect.left, self.rect.top = random.randint(0, self.mapSize[0] - self.rect.width), \
                                        random.randint(0, self.mapSize[1] - self.rect.height)
        while pygame.sprite.spritecollide(self, self.BlackHole_Swallowed_Group, False)\
                or pygame.sprite.spritecollide(self, self.NoPassing_Group, False):
            self.rect.left, self.rect.top = random.randint(0, self.mapSize[0] - self.rect.width), \
                                            random.randint(0, self.mapSize[1] - self.rect.height)
        self.Tank_Group.add(self)
        self.NoPassing_Group.add(self)
        self.CanDestroy_Group.add(self)

    def selfExplosion(self):
        temp = Explosion(self)
        self.SpecialScenes_Group.add(temp)
        self.life = 0
        self.skill = 0
        self.kill()

    def be_hit(self, Type):
        if Type == 'blackHole':
            self.kill()
            self.BlackHole_Swallowed_Group.add(self)
            self.BlackHole_Swallowed_Time = time.time()

        if Type == 'lightning' and time.time() - self.beHitType['lightning'] > 2:
            self.life -= 20
            self.beHitType['lightning'] = time.time()
        elif Type == 'normal bullet' and time.time() - self.beHitType['normal bullet'] > 0:
            self.life -= 10
            self.beHitType['normal bullet'] = time.time()
        elif Type == 'laser bullet' and time.time() - self.beHitType['laser bullet'] > all_const.LaserContainTime+0.1:
            self.life -= 60
            self.beHitType['laser bullet'] = time.time()
        elif Type == 'self explosion':
            if time.time() - self.beHitType['self explosion'] > all_const.SelfExplosionTime+0.1:
                self.life -= 90
                self.beHitType['self explosion'] = time.time()

        if self.life < 0:
            self.life = 0

    def display_blood_bar(self, image, rect, offset):
        width, height = rect.width-2*offset, rect.height-2*offset
        C = (width+height)*2
        blood_bar_length = int(C * self.life/self.totalLife)
        startPoint = (0+offset, 0+offset)
        pointlist = [startPoint]
        if blood_bar_length <= width:
            pointlist.append((startPoint[0]+blood_bar_length, startPoint[1]))
        elif blood_bar_length <= width+height:
            pointlist += [(0+offset+width, 0+offset),
                          (0+offset+width, 0+offset+blood_bar_length-width)]
        elif blood_bar_length <= width*2+height:
            pointlist += [(0+offset+width, 0+offset),
                          (0+offset+width, 0+offset+height),
                          (0+offset+(width-blood_bar_length+width+height), 0+offset+height)]
        elif blood_bar_length <= C:
            pointlist += [(0+offset+width, 0+offset),
                          (0+offset+width, 0+offset+height),
                          (0+offset, 0+offset+height),
                          (0+offset, 0+offset+C-blood_bar_length)]
        pygame.draw.lines(image, all_const.blood_bar_color, False, pointlist, width=all_const.blood_bar_line_width)


    def autoAdd(self, addLife=2, addSkill=5, addLifeTime=0.5, addSkillTime=0.5):
        if time.time() - self.autoAddLife_time > addLifeTime:
            self.autoAddLife_time = time.time()
            if self.life < self.totalLife:
                self.life += addLife
                if self.life > self.totalLife:
                    self.life = self.totalLife
        if time.time() - self.autoAddSkill_time > addSkillTime:
            self.autoAddSkill_time = time.time()
            if self.skill < self.totalSkill:
                self.skill += addSkill
                if self.skill > self.totalSkill:
                    self.skill = self.totalSkill

#! 子弹基类
class Bullet(DirtySprite):
    def __init__(self, image, forTank, typeBullet, speed=1,  layer=all_layer.NormalBulletLayer):
        DirtySprite.__init__(self)

        # 加载子弹图片
        self.image = image

        # 设置子弹的位置
        # self.position = position
        self.rect = self.image.get_rect()

        # 子弹的速度
        self.speed = speed

        # 子弹所在层
        self._layer = layer

        # 所属坦克
        self.Tank = forTank

        # 子弹的类型
        self.Type = typeBullet

    def destroy(self):
        self.kill()
        del self

#! 普通子弹，可指定每颗子弹的伤害
class NormalBullet(Bullet):
    def __init__(self, image, forTank, speed=all_const.NormalBulletSpeed, dist=all_const.NormalBulletRange, layer=all_layer.NormalBulletLayer):
        super().__init__(image, forTank, 'normal bullet', speed, layer)

        self.alive_time = dist / (FPS * speed)
        self.fireRange = dist
        self.firedRange = 0

    def fire(self):
        self.fired_time = time.time()
        self.direction = self.Tank.direction
        if self.direction == 'up':
            self.rect.left = self.Tank.rect.left + (self.Tank.rect.width // 2 - self.rect.width // 2)
            self.rect.top = self.Tank.rect.top + self.rect.height
        elif self.direction == 'down':
            self.rect.left = self.Tank.rect.left  + (self.Tank.rect.width // 2 - self.rect.width // 2)
            self.rect.top = self.Tank.rect.top + self.Tank.rect.height
        elif self.direction == 'left':
            self.rect.left = self.Tank.rect.left - self.rect.width
            self.rect.top = self.Tank.rect.top + (self.Tank.rect.height // 2 - self.rect.height // 2)
        elif self.direction == 'right':
            self.rect.left = self.Tank.rect.left + self.Tank.rect.width + self.rect.width
            self.rect.top = self.Tank.rect.top + (self.Tank.rect.height // 2 - self.rect.height // 2)

    def update(self, *args, **kwargs) -> None:
        self.firedRange += self.speed
        if self.direction == 'up':
            self.rect.top -= self.speed
        elif self.direction == 'down':
            self.rect.top += self.speed
        elif self.direction == 'left':
            self.rect.left -= self.speed
        elif self.direction == 'right':
            self.rect.left += self.speed

        if self.firedRange >= self.fireRange:
            self.kill()
            del self


#! 激光子弹，可指定伤害
class BulletLaser(Bullet):
    def __init__(self, image, forTank, containTime=all_const.LaserContainTime, speed=1, layer=all_layer.LaserBulletLayer):
        super().__init__(image, forTank, 'laser bullet', speed, layer)

        self.laser_size = self.laser_width, self.laser_height = 32, 220
        self.image = pygame.transform.scale(self.image, self.laser_size)
        self.rect = self.image.get_rect()
        self.direct()

        # 设置激光显示在坦克的炮口
        self.fire()

        # 持续时间
        self.laser_contain_time = containTime

    def fire(self):
        self.fired_time = time.time()

        self.image = self.Direct_Laser[self.Tank.direction]
        self.rect = self.Rect_laser[self.Tank.direction]

        if self.Tank.direction == 'up':
            self.rect.left = self.Tank.rect.left + (self.Tank.rect.width // 2 - self.laser_width // 2)
            self.rect.top = self.Tank.rect.top - self.laser_height
        elif self.Tank.direction == 'down':
            self.rect.left = self.Tank.rect.left + (self.Tank.rect.width // 2 - self.laser_width // 2)
            self.rect.top = self.Tank.rect.top + self.Tank.rect.height
        elif self.Tank.direction == 'left':
            self.rect.left = self.Tank.rect.left - self.laser_height
            self.rect.top = self.Tank.rect.top + (self.Tank.rect.height // 2 - self.laser_width // 2)
        elif self.Tank.direction == 'right':
            self.rect.left = self.Tank.rect.left + self.Tank.rect.width
            self.rect.top = self.Tank.rect.top + (self.Tank.rect.height // 2 - self.laser_width // 2)

    def direct(self):
        self.laser_up = pygame.transform.rotate(self.image, 0)
        self.laser_up_rect = self.laser_up.get_rect()

        self.laser_left = pygame.transform.rotate(self.laser_up, 90)
        self.laser_left_rect = self.laser_left.get_rect()

        self.laser_down = pygame.transform.rotate(self.laser_left, 90)
        self.laser_down_rect = self.laser_down.get_rect()

        self.laser_right = pygame.transform.rotate(self.laser_down, 90)
        self.laser_right_rect = self.laser_right.get_rect()

        self.laser_direct = [self.laser_up, self.laser_down, self.laser_left, self.laser_right]
        self.laser_direct_rect = [self.laser_up_rect, self.laser_down_rect, self.laser_left_rect, self.laser_right_rect]

        self.Direct_Laser = dict(zip(self.Tank.direction_list, self.laser_direct))
        self.Rect_laser = dict(zip(self.Tank.direction_list, self.laser_direct_rect))

    def update(self, *args, **kwargs) -> None:
        if time.time() - self.fired_time > self.laser_contain_time:
            self.kill()
            del self


#! 毁灭的爆炸，在坦克毁灭时触发，可被穿过，不造成伤害
class Boom(DirtySprite):
    def __init__(self, boomImage, forTank, allTime=1, layer=all_layer.BoomLayer):
        DirtySprite.__init__(self)

        # 爆炸动画序列图像
        self.image_list = boomImage

        # 将爆炸的坦克
        self.Tank = forTank

        # 爆炸的总时间
        self.allTime = allTime

        # 显示的图层
        self._layer = layer

        # 是否爆炸
        self.explode = False

        # 加载爆炸图片
        self.image = self.image_list[0]
        self.rect = self.Tank.rect
        self.image_num = len(self.image_list)

    def update(self, *args, **kwargs) -> None:
        if self.explode:
            self.exploding()


    def boom(self):
        self.explode = True
        self.boomTime = time.time()
        self.exploding_image_num = 0

    def exploding(self):
        current_time = time.time()
        if current_time - self.boomTime > (self.allTime / self.image_num):
            if self.exploding_image_num == self.image_num:
                self.kill()
                del self
                return
            self.image = self.image_list[self.exploding_image_num]
            self.exploding_image_num += 1
            self.boomTime = current_time


#! 墙的基类
class Wall(DirtySprite):
    def __init__(self, image, position, layer):
        DirtySprite.__init__(self)

        # 加载图片
        self.image = image
        # 确定大小
        self.rect = self.image.get_rect()
        # 确定显示图层
        self._layer = layer
        # 定位
        self.rect.left, self.rect.top = self.position = position

    def get_mask(self):
        self.mask = pygame.mask.from_surface(self.image)

    def location(self, position):
        # 定位
        self.rect.left, self.rect.top = self.position = position

    def be_hit(self, Type):
        pass

    def destroy(self):
        self.kill()
        del self


#! 草地，可穿过，显示层级较高，会遮掩坦克及子弹
class Grass(Wall):
    def __init__(self, image, position=(0,0), Layer=all_layer.GrassLayer):
        Wall.__init__(self, image, position, Layer)

        self.WallType = 'grass'


#! 河流，仅子弹可穿过，无法破坏
class River(Wall):
    def __init__(self, image, position=(0,0), Layer=all_layer.RiverLayer):
        Wall.__init__(self, image, position, Layer)

        self.WallType = 'river'


#! 砖墙，不可穿过，可被打破
class Brick(Wall):
    def __init__(self, image, position=(0,0), Layer=all_layer.BrickLayer):
        Wall.__init__(self, image, position, Layer)

        self.WallType = 'brick'

    def be_hit(self, Type):
        if 'bullet' in Type or Type == 'lightning':
            self.destroy()
        elif Type == 'self explosion':
            self.destroy()


#! 钢块，无法穿过，无法破坏
class Iron(Wall):
    def __init__(self, image, position=(0,0), Layer=all_layer.IronLayer):
        Wall.__init__(self, image, position, Layer)

        self.WallType = 'iron'


#! 特殊场景基类
class SpecialScenes(DirtySprite):
    def __init__(self, image_list, position, play_time, contain_time, Layer, typeSS):
        DirtySprite.__init__(self)
        self.image_list = image_list
        self.image_number = len(image_list)
        self.image_order = 0
        self.image = image_list[0]
        self.rect = self.image.get_rect()
        self.rect.left, self.rect.top = self.position = position
        self.play_time = play_time
        self.contain_time = contain_time
        self._layer = Layer
        self.occurTime = time.time()
        self.startPlayTime = time.time()
        self.masked = False
        self.Type = typeSS

    def location(self, position):
        # 定位
        self.rect.left, self.rect.top = self.position = position

    def get_mask_list(self, mask_list):
        self.mask_list = mask_list
        self.mask = self.mask_list[self.image_order]
        self.masked = True


    def destroy(self):
        self.kill()
        del self


#! 雷区，区域内所有可破坏的元素都会遭受到伤害
class Lightning(SpecialScenes):
    def __init__(self, image_list, position, play_time=all_const.Lightning_playTime, contain_time=all_const.Lightning_ContainTime, Layer=all_layer.Lightning):
        SpecialScenes.__init__(self, image_list, position, play_time, contain_time, Layer, 'lightning')

    def update(self, *args, **kwargs) -> None:
        if time.time() - self.startPlayTime > self.contain_time:
            self.kill()
            del self
        elif time.time()-self.occurTime > self.play_time/self.image_number:
            self.occurTime = time.time()
            self.image_order += 1
            self.image_order = 0 if self.image_order >= self.image_number-1 else self.image_order
            self.image = self.image_list[self.image_order]
            if self.masked: self.mask = self.mask_list[self.image_order]


#! 黑洞，将范围内的坦克吞噬，并在10s后随机投放
class BlackHole(SpecialScenes):
    def __init__(self, image_list, position, play_time=all_const.BlackHole_playTime, contain_time=all_const.BlackHole_containTime, Layer=all_layer.Lightning):
        SpecialScenes.__init__(self, image_list, position, play_time, contain_time, Layer, 'blackHole')

    def update(self, *args, **kwargs) -> None:
        if time.time() - self.startPlayTime > self.contain_time:
            self.kill()
            del self
        elif time.time()-self.occurTime > self.play_time/self.image_number:
            self.occurTime = time.time()
            self.image_order += 1
            self.image_order = 0 if self.image_order >= self.image_number-1 else self.image_order
            self.image = self.image_list[self.image_order]
            if self.masked: self.mask = self.mask_list[self.image_order]


#! 自爆，坦克自身爆炸，对周围造成大量伤害
class Explosion(SpecialScenes):
    def __init__(self, forTank):
        SpecialScenes.__init__(self, all_image.ExplosionImageList,
                               (0, 0),
                               all_const.SelfExplosionTime,
                               all_const.SelfExplosionContainTime,
                               all_layer.SelfExplosionLayer,
                               'self explosion')

        self.image_list = all_image.ExplosionImageList
        self.Tank = forTank
        self.rect.left = self.Tank.rect.left - (self.rect.width - self.Tank.rect.width)//2
        self.rect.top = self.Tank.rect.top - (self.rect.height - self.Tank.rect.height)//2
        self.get_mask_list(all_image.SelfExplosionMaskList)

    def update(self, *args, **kwargs) -> None:
        if time.time() - self.startPlayTime > self.contain_time:
            self.kill()
            del self
        elif time.time()-self.occurTime > self.play_time/self.image_number:
            self.occurTime = time.time()
            self.image_order += 1
            self.image_order = 0 if self.image_order >= self.image_number-1 else self.image_order
            self.image = self.image_list[self.image_order]
            if self.masked: self.mask = self.mask_list[self.image_order]


#! 用户信息界面
class UserInfo:
    def __init__(self, blitSur, targetTank):
        self.Sur = blitSur
        self.Sur_rect = self.Sur.get_rect()
        self.targetTank = targetTank
        pass

    def draw_blood_bar(self):
        self.blood_bar_image = all_image.BloodBarImage
        self.blood_bar_image = pygame.transform.scale(self.blood_bar_image, (300, 40))
        blood = self.targetTank.life
        self.blood_bar_rect = self.blood_bar_image.get_rect()
        transparent_start = 5 + (self.blood_bar_rect.width-10) * blood // self.targetTank.totalLife
        # newArr = blood_bar_pixels[transparent_start:, :]
        blood_bar_pixels = pygame.PixelArray(self.blood_bar_image)[transparent_start:]
        blood_bar_pixels.replace((255,0,0), (255,255,255,0), 0.3, (1, 0, 0))
        blood_bar_pixels.close()
        self.Sur.blit(self.blood_bar_image, (50, 50))

    def draw_skill_bar(self):
        self.skill_bar_image = all_image.SkillBarImage
        self.skill_bar_image = pygame.transform.scale(self.skill_bar_image, (300, 40))
        skill = self.targetTank.skill
        self.skill_bar_rect = self.skill_bar_image.get_rect()
        transparent_start = 5 + (self.skill_bar_rect.width-10) * skill // self.targetTank.totalSkill
        # newArr = blood_bar_pixels[transparent_start:, :]
        skill_bar_pixels = pygame.PixelArray(self.skill_bar_image)[transparent_start:]
        skill_bar_pixels.replace((0,0,255), (255,255,255,0), 0.3, (0, 0, 1))
        skill_bar_pixels.close()
        self.Sur.blit(self.skill_bar_image, (50, 100))