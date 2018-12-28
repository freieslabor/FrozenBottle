import asyncio

from py3_client import Client, WorkerPool, arrow_keys

#client = Client(host='151.217.153.70', port=8901)
client = Client()

loop = asyncio.get_event_loop()
worker_pool = WorkerPool(loop=loop)

POINT = [0, 0]


async def pacman():
    return
    for i in range(14):
        client.set(i, 0, 0, 0, 255)
        client.set(i, 13, 0, 0, 255)


def print_point():
    client.set(POINT[0], POINT[1], 255, 0, 0)




loop.create_task(worker_pool.run(client.flush, interval=0.3))
loop.create_task(worker_pool.run(get_key_presses))
loop.create_task(pacman())

loop.run_forever()



#loop.run_until_complete(worker_pool.run(shell))
