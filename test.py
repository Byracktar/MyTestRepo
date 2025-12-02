import requests

DJANGO_URL = "http://127.0.0.1:8088"


#Token al (JWT)

credentials = {
    "email": "platc13@gmail.com",  
    "password": "123"
}

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


res = requests.get(f"{DJANGO_URL}/api/services/", headers=headers)
print("Services GET:", res.json())


res = requests.post(
    f"{DJANGO_URL}/api/services/", 
    headers=headers, 
    json={
        "name": "Yeni Hizmet",
        "category": 1,       
        "description": "Test açıklama",
        "price_info": "100-200 TL",
        "duration_minutes": 60
    }
)
print("Add Service POST:", res.status_code, res.json())

res = requests.get(f"{DJANGO_URL}/api/workers/", headers=headers)
print("Workers GET:", res.json())


worker_id = 1  
res = requests.get(f"{DJANGO_URL}/api/workers/{worker_id}/", headers=headers)
print("Worker Info GET:", res.json())


res = requests.post(
    f"{DJANGO_URL}/api/appointments/", 
    headers=headers, 
    json={
        "worker": 1,           # valid worker ID
        "service": 1,          # valid service ID
        "start_time": "2025-12-05T10:00:00Z",
        "end_time": "2025-12-05T11:00:00Z",
        "request_details": "Test randevu"
    }
)
print("Create Appointment POST:", res.status_code, res.json())


res = requests.get(f"{DJANGO_URL}/api/worksamples/", headers=headers)
print("Work Samples GET:", res.json())


res = requests.get(f"{DJANGO_URL}/api/legaltexts/", headers=headers)
print("Legal Texts GET:", res.json())
