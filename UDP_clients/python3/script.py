import asyncio
import IPython

from py3_client import Client, WorkerPool, Sprite, Keyboard

client = Client()

sprite = Sprite(spec="""
2 2 0
2 1 2
2 2 0
""")


keyboard = Keyboard()
client.sprites.append(sprite)

loop = asyncio.get_event_loop()
worker_pool = WorkerPool(loop=loop)



loop.create_task(worker_pool.run(client.flush, interval=0.2))



from pynput.keyboard import Key, Listener
from pynput import keyboard


def on_press(key):
    if key == Key.up:
        sprite.offset_y -= 1

    if key == Key.down:
        sprite.offset_y += 1

    if key == Key.left:
        sprite.offset_x -= 1

    if key == Key.right:
        sprite.offset_x += 1


def foo():
    with Listener(on_press=on_press) as listener:
        listener.join()

loop.create_task(worker_pool.run(foo))

def _cancel_all_tasks(loop):
    to_cancel = asyncio.Task.all_tasks()

    if not to_cancel:
        return

    for task in to_cancel:
        task.cancel()

    loop.run_until_complete(
        asyncio.gather(*to_cancel, loop=loop, return_exceptions=True))

    for task in to_cancel:
        if task.cancelled():
            continue

        if task.exception() is not None:
            loop.call_exception_handler({
                'message': 'unhandled exception during asyncio.run() shutdown',
                'exception': task.exception(),
                'task': task,
            })

try:
    loop.run_forever()

except KeyboardInterrupt:
    keyboard.running = False
    _cancel_all_tasks(loop)

#loop.run_until_complete(worker_pool.run(shell))
