


import asyncio
import os

HOST = os.getenv("HOST", "wc_balancer")
PORT = int(os.getenv("PORT", "18861"))

REMOTES = os.getenv("REMOTE", "wc_server").split(";")
print(REMOTES)
print(len(REMOTES))
i = 0

HEALTH_CHECK_PORT = int(os.getenv("CHECK_PORT", "18861"))
HEALTH_CHECK_INTERVAL = float(os.getenv("CHECK_INTERVAL", "1"))
HEALTH = [True for _ in REMOTES]

async def proxy(read, write):
	while True:
		data = await read.read(1024)
		if not data: break

		write.write(data)
		await write.drain()
	write.close()

async def health_check():
	while True:
		await asyncio.sleep(HEALTH_CHECK_INTERVAL)
		for i, s in enumerate(REMOTES):
			is_healthy = False
			try:
				reader, writer = await asyncio.wait_for(asyncio.open_connection(s, HEALTH_CHECK_PORT), timeout=0.5)
				writer.close()
				await writer.wait_closed()
				is_healthy = True
			except:
				is_healthy = False

			if is_healthy and not HEALTH[i]:
				print(f"Server {s} ready for connections")
			elif not is_healthy and HEALTH[i]:
				print(f"Server {s} not ready for connections")
			HEALTH[i] = is_healthy

async def handle_conn(source_read, source_write):
	global i

	ti = i
	while not HEALTH[ti]:
		ti = (ti + 1) % len(REMOTES)
		if ti == i:
			print("No healthy servers") # What to do?
			break


	r = REMOTES[ti]
	i = (ti + 1) % len(REMOTES)
#	target_read, target_write = await asyncio.open_connection(r, PORT, ssl_handshake_timeout=.003)

	try:
		target_read, target_write = await asyncio.open_connection(r, PORT)
		await asyncio.wait([proxy(source_read, target_write), proxy(target_read, source_write)])
	except:
		print(f"Server {r} failed during execution")
		HEALTH[i] = False
		source_write.close()


loop = asyncio.get_event_loop()
coroutine = asyncio.start_server(handle_conn, HOST, PORT, loop=loop)
server = loop.run_until_complete(coroutine)

health_task = loop.create_task(health_check())

try:
	loop.run_forever()
except Exception:
	pass

server.close()
loop.run_until_complete(server.wait_closed())
loop.close()
