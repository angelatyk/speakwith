from db.mongo import check_connection

if check_connection():
    print("MongoDB Atlas is connected ✅")
else:
    print("Connection failed ❌")
