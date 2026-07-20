import urllib.request, json

data = json.dumps({"client_id": "test_script", "device_name": "Test Device"}).encode('utf-8')
req = urllib.request.Request("http://127.0.0.1:8000/api/sync/ping", data=data, headers={'Content-Type': 'application/json'})
try:
    resp = urllib.request.urlopen(req)
    print(resp.read())
except Exception as e:
    print(e)
