import requests

DJANGO_URL = "http://127.0.0.1:8000"

# Kullanıcı bilgisi
credentials = {
    "username": "fghhfg",
    "password": "Ruhi123gsddfyfs"
}

# 1️⃣ Token al
login_res = requests.post(f"{DJANGO_URL}/api/token/", json=credentials)
if login_res.status_code != 200:
    print("Login failed:", login_res.text)
    exit()

tokens = login_res.json()
access = tokens['access']
refresh = tokens['refresh']
print("Access Token:", access)
print("Refresh Token:", refresh)

headers = {
    "Authorization": f"Bearer {access}",
    "Content-Type": "application/json"
}


# 2️⃣ GET Services
res = requests.get(f"{DJANGO_URL}/api/services/", headers=headers)
print("Services GET:", res.json())

# 3️⃣ POST Add Service (Admin)
res = requests.post(f"{DJANGO_URL}/api/services/", headers=headers, json={"name": "Yeni Hizmet"})
print("Add Service POST:", res.json())

# 4️⃣ GET Operators
res = requests.get(f"{DJANGO_URL}/api/operators/", headers=headers)
print("Operators GET:", res.json())

# 5️⃣ GET Operator Info
res = requests.get(f"{DJANGO_URL}/api/operator/info/", headers=headers)
print("Operator Info GET:", res.json())

# 6️⃣ POST Add Operator Info (Admin)
res = requests.post(f"{DJANGO_URL}/api/operator/info/", headers=headers, json={"info": "5 yıldız"})
print("Add Operator Info POST:", res.json())

# 7️⃣ POST Select Operator
res = requests.post(f"{DJANGO_URL}/api/operator/select/", headers=headers, json={"selected": "Usta A"})
print("Select Operator POST:", res.json())
