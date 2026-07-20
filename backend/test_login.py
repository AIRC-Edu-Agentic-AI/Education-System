import requests

def test_login(sid, pwd):
    print(f"Testing login for {sid} with password '{pwd}'...")
    try:
        r = requests.post("http://localhost:8000/api/auth/login", json={"student_id": sid, "password": pwd})
        print(f"Status: {r.status_code}")
        print(f"Response: {r.json()}")
    except Exception as e:
        print(f"Error: {e}")

test_login(10004, "123456")
test_login(10004, "wrong")
test_login(999999, "123456")