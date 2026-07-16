from pymongo import MongoClient

local = MongoClient("mongodb://localhost:27017/")["oulad_db"]
atlas = MongoClient("mongodb+srv://micipssadjaroun_db_user:airc2@ouladcluster2.hvn6kza.mongodb.net/?appName=ouladcluster2")["oulad_db"]

# 1. Filter students from modules AAA and BBB only
print("Filtering students from modules AAA and BBB...")
sampled_students = list(local["students"].find(
    {"code_module": {"$in": ["AAA", "BBB"]}},
    {"_id": 0}
))
sampled_ids = set(s["id_student"] for s in sampled_students)
print("Students selected: " + str(len(sampled_ids)))

# 2. Migration students
print("Migration students...")
atlas["students"].drop()
atlas["students"].insert_many(sampled_students)
print("OK : " + str(len(sampled_students)) + " documents")

# 3. Migration modules (tous)
print("Migration modules...")
docs = list(local["modules"].find({"code_module": {"$in": ["AAA", "BBB"]}}, {"_id": 0}))
atlas["modules"].drop()
atlas["modules"].insert_many(docs)
print("OK : " + str(len(docs)) + " documents")

# 4. Migration assessments_meta (tous)
print("Migration assessments_meta...")
docs = list(local["assessments_meta"].find({"code_module": {"$in": ["AAA", "BBB"]}}, {"_id": 0}))
atlas["assessments_meta"].drop()
atlas["assessments_meta"].insert_many(docs)
print("OK : " + str(len(docs)) + " documents")

# 5. Migration registrations (filtrés)
print("Migration registrations...")
docs = list(local["registrations"].find({"id_student": {"$in": list(sampled_ids)}}, {"_id": 0}))
atlas["registrations"].drop()
atlas["registrations"].insert_many(docs)
print("OK : " + str(len(docs)) + " documents")

# 6. Migration student_assessments (filtrés)
print("Migration student_assessments...")
docs = list(local["student_assessments"].find({"id_student": {"$in": list(sampled_ids)}}, {"_id": 0}))
atlas["student_assessments"].drop()
atlas["student_assessments"].insert_many(docs)
print("OK : " + str(len(docs)) + " documents")

# 7. Migration vle_interactions (filtrés) par batch
print("Migration vle_interactions...")
atlas["vle_interactions"].drop()
count = 0
batch = []
for doc in local["vle_interactions"].find({"id_student": {"$in": list(sampled_ids)}}, {"_id": 0}):
    batch.append(doc)
    if len(batch) >= 5000:
        atlas["vle_interactions"].insert_many(batch, ordered=False)
        count += len(batch)
        batch = []
        print("Insere : " + str(count))
if batch:
    atlas["vle_interactions"].insert_many(batch, ordered=False)
    count += len(batch)
print("vle_interactions OK : " + str(count) + " documents")

print("MIGRATION COMPLETE !")