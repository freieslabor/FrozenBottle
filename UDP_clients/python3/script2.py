import IPython
import random
import time


sprite1 = Sprite(spec="""
1 1 0
1 0 1
1 1 0
""")

sprite2 = Sprite(spec="""
2 2 0
2 0 2
2 2 0
""", offset_x=8, offset_y=8)

client.sprite_mode = True

client.sprites.append(sprite1)
client.sprites.append(sprite2)


while True:
    for i in range(5):
        sprite1.offset_x += random.randint(0, 1)
        sprite1.offset_y += random.randint(0, 1)
        sprite2.offset_x += random.randint(0, 1)
        sprite2.offset_y += random.randint(0, 1)

        time.sleep(0.5)

    sprite1.offset_x = 0
    sprite1.offset_y = 0
    sprite2.offset_x = 8
    sprite2.offset_y = 8

    time.sleep(0.5)


