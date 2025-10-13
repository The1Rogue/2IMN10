


import asyncio
import os

HOST = os.getenv("HOST", "wc_balancer")
PORT = int(os.getenv("PORT", "18861"))

REMOTES = os.getenv("REMOTE", "wc_server").split(";")
print(REMOTES)
print(len(REMOTES))
i = 0

async def proxy(read, write):
	while True:
		data = await read.read(1024)
		if not data: break

		write.write(data)
		await write.drain()

	write.close()



async def handle_conn(source_read, source_write):
	global i
	r = REMOTES[i]
	print(r)
	i = (i + 1) % len(REMOTES)
	print(i)
	target_read, target_write = await asyncio.open_connection(r, PORT)

	await asyncio.wait([proxy(source_read, target_write), proxy(target_read, source_write)])



loop = asyncio.get_event_loop()
coroutine = asyncio.start_server(handle_conn, HOST, PORT, loop=loop)
server = loop.run_until_complete(coroutine)

try:
	loop.run_forever()
except Exception:
	pass

server.close()
loop.run_until_complete(server.wait_closed())
loop.close()
