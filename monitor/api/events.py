# Aurelinth — SSE event bridge: Redis Stream → browser
import json
import asyncio
from redis import Redis


async def redis_event_stream(r: Redis):
    last_id = "$"

    while True:
        try:
            results = r.xread(
                {"aurelinth:events": last_id},
                block=1000,
                count=10
            )

            if not results:
                await asyncio.sleep(0.1)
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