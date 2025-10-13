
import os, time, csv, pathlib
import asyncio
import rpyc

SERVER_HOST = os.getenv("SERVER_HOST", "server")
SERVER_PORT = int(os.getenv("SERVER_PORT", "18861"))
NAME = os.getenv("NAME", "unknown")

OUT = pathlib.Path("/out")
OUT.mkdir(exist_ok=True)

def run(batch):
    """
    batch: list of (keyword, filename)
    returns: rows list
    """
    conn = rpyc.connect(SERVER_HOST, SERVER_PORT)
    svc = conn.root

    rows = []
    i = 0
    for kw, fn in batch:
        i += 1
        t0 = time.perf_counter()
        resp = svc.count(kw, fn)
        t1 = time.perf_counter()

        client_latency_ms = (t1 - t0) * 1000.0
        rows.append({
            "req_id": i,
            "keyword": kw,
            "filename": fn,
            "client_latency_ms": round(client_latency_ms, 3),
            "server_time_ms": round(resp["server_time_ms"], 3),
            "cached": resp["cached"],
            "host": resp["host"]
        })
        print(f"[client] #{i:02d} {fn} | '{kw}' -> count={resp['count']} "
              f"(cached={resp['cached']}) "
              f"client_latency_ms={client_latency_ms:.2f} "
              f"host={resp['host']}")

    conn.close()
    return rows

def parse(i):
    batch = [
        ("sea",  "moby_dick.txt"),
        ("whale",  "moby_dick.txt"),
        ("father","frankenstein.txt"),
        ("parents","frankenstein.txt"),
        ("artist",   "moby_dick.txt"),
        ("sailor", "moby_dick.txt"),
    ]

    rows = run(batch)
    out_csv = OUT / f"latency_phase2_{NAME}_{i}.csv"
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader(); w.writerows(rows)
    print(f"[client] wrote {out_csv}")

async def main():
    await asyncio.gather(parse(i) for i in range(5))

if __name__ == "__main__":
    asyncio.run(asyncio.sleep(10)) #make sure servers have started and are ready
    asyncio.run(main())


