import redis

class Redis:
    def __init__(self):
        self.r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

    def connect(self):
        client = self.r

        try:
            if client.ping():
                print("Redis connected")

                client.set('user:name', 'validated')

                user = client.get('user:name')
                print(f"Connection: {user}")
                return self.r
            else:
                print("Redis not connected")
        except redis.ConnectionError:
            print("Could not connect to Redis. Ensure the server is running.")