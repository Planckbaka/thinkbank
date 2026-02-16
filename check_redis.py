
import redis
import os

def check():
    host = os.getenv('REDIS_HOST', 'localhost')
    port = int(os.getenv('REDIS_PORT', 6379))
    r = redis.Redis(host=host, port=port, db=0)
    queue_name = os.getenv('REDIS_QUEUE_NAME', 'thinkbank:tasks')
    print(f"Checking queue: {queue_name} on {host}:{port}")
    tasks = r.lrange(queue_name, 0, -1)
    print(f"Tasks in queue: {tasks}")
    print(f"Queue size: {r.llen(queue_name)}")

if __name__ == '__main__':
    check()
