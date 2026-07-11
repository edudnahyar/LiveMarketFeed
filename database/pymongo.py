import pymongo

class PyMongo:
    def __init__(self):
        self.p = pymongo.MongoClient(host='localhost', port=27017)

    def connect(self):
        client = self.p

        try:
            client.admin.command('ping')
            print(f"Connection successful")

            if client["test"] is None:
                db = client["test"]
                collection = db["test"]
                data = {
                    "test": "validated"
                }
                collection.insert_one(data)

            else:
                db = client["test"]
                collection = db["test"]
                assert collection.count_documents({"test": "validated"}) > 0

            test = collection.find_one({"test": "validated"})

            print(f"Connection successful: {test}")
            return client

        except Exception as e:
            print(f"Connection error: {e}")
            return None