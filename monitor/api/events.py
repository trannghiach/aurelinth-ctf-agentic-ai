# Aurelinth — SSE event bridge: Redis Stream → browser
import json
import asyncio
from redis import Redis


async def redis_event_stream(r: Redis):
    """
    Read aurelinth:events Redis Stream and yield SSE-formatted events.
    Uses blocking read with 1s timeout for real-time delivery.
    """
    last_id = "$"  # start from latest, catch all new events

    while True:
        try:
            results = r.xread(
                {"aurelinth:events": last_id},
                block=1000,  # block 1s waiting for new events
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

                    yield f"event: {event_type}\ndata: {data}\n\n"

        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
            await asyncio.sleep(1)