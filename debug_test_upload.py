import requests
from bs4 import BeautifulSoup

BASE = 'http://127.0.0.1:5000'
LOGIN = BASE + '/auth/login'
TEST_UPLOAD = BASE + '/customers-new/api/test-upload'

s = requests.Session()
# GET login page to extract csrf
r = s.get(LOGIN, timeout=10)
print('GET login status:', r.status_code)
if r.status_code != 200:
    print('Failed to GET login page', r.status_code)
    print(r.text[:1000])
    raise SystemExit(1)

soup = BeautifulSoup(r.text, 'html.parser')
csrf = ''
csrf_input = soup.find('input', {'name': 'csrf_token'})
if csrf_input:
    csrf = csrf_input.get('value')
print('CSRF token:', bool(csrf))

payload = {
    'username': 'admin',
    'password': 'admin',
    'csrf_token': csrf,
}

r2 = s.post(LOGIN, data=payload, timeout=10, allow_redirects=True)
print('Login status code after POST:', r2.status_code)
print('Login response length:', len(r2.text))
if 'الرجاء تسجيل الدخول' in r2.text:
    print('Login failed: still on login page')

# Prepare test upload data
import json
new_docs = [
    {
        'name': 'test.txt',
        'type': 'text/plain',
        'size': 11,
        'data': 'data:text/plain;base64,SGVsbG8gV29ybGQ='
    }
]

try:
    r3 = s.post(TEST_UPLOAD, data={'customer_id': '6', 'new_documents_data': json.dumps(new_docs)}, timeout=10)
    print('Test upload response status:', r3.status_code)
    print('Test upload response:', r3.text)
except Exception as e:
    print('Exception during test upload:', repr(e))
