# Aurelinth — SSE event bridge: Redis Stream → browser
import json
import asyncio
from redis import Redis


async def redis_event_stream(r: Redis):
    last_id = "$"

    while True:
        try:
            results = await asyncio.to_thread(
                r.xread,
                {"aurelinth:events": last_id},
                10,   # count
                1000  # block ms
            )

            if not results:
                continue

            for stream_name, messages in results:
                for msg_id, fields in messages:
                    last_id = msg_id
                    event_type = fields.get("type", "unknown")
                    data = fields.get("data", "{}")
                    yield {"event": event_type, "data": data}

        except Exception as e:
            yield {"event": "error", "data": json.dumps({"error": str(e)})}
            await asyncio.sleep(1)