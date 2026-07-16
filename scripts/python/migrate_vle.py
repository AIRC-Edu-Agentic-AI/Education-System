from pymongo import MongoClient

local = MongoClient("mongodb://localhost:27017/")["oulad_db"]
atlas = MongoClient("mongodb+srv://whitedevil0981907116_db_user:airc@ouladcluster.tsrzoux.mongodb.net/?appName=OuladCluster")["oulad_db"]

print("Migration vle_interactions...")
atlas["vle_interactions"].drop()
count = 0
batch = []

for doc in local["vle_interactions"].find({}, {"_id": 0}):
    batch.append(doc)
    if len(batch) >= 5000:
        atlas["vle_interactions"].insert_many(batch, ordered=False)
        count += len(batch)
        batch = []
        print("Insere : " + str(count))

if batch:
    atlas["vle_interactions"].insert_many(batch, ordered=False)
    count += len(batch)

print("DONE : " + str(count) + " documents")