import requests

SITE_BASE_URL = "http://135.225.108.179:5000"
API_BASE_URL = f"{SITE_BASE_URL}/api"


LOGIN_EMAIL = "admin@example.com"
LOGIN_PASSWORD = "password"

session = requests.Session()


def login():
    login_url = f"{SITE_BASE_URL}/login"

    data = {
        "email": LOGIN_EMAIL,
        "password": LOGIN_PASSWORD
    }

    response = session.post(
        login_url,
        data=data,
        timeout=10,
        allow_redirects=True
    )

    print("Login status:", response.status_code)
    print("Efter login URL:", response.url)

    # Simpel check: hvis vi stadig ser login-siden, fejlede login nok
    if "<title>Login</title>" in response.text:
        raise ValueError("Login fejlede. Tjek email/password.")

    print("Login lykkedes")


def get_faces():
    response = session.get(f"{API_BASE_URL}/faces", timeout=10)
    response.raise_for_status()
    return response.json()

def verify_pin(pin_code):
    response = requests.post(
        f"{API_BASE_URL}/pins/verify",
        json={
            "pin_code": pin_code
        },
        timeout=10
    )

    response.raise_for_status()
    return response.json()

def get_image_url(path):
    if path.startswith("http"):
        return path

    return f"{SITE_BASE_URL}/{path}"


def download_file(url, save_path):
    response = session.get(url, timeout=15)

    print("Download URL:", url)
    print("Status code:", response.status_code)
    print("Content-Type:", response.headers.get("Content-Type"))
    print("Content length:", len(response.content))

    response.raise_for_status()

    content_type = response.headers.get("Content-Type", "")

    if not content_type.startswith("image/"):
        print("Dette er ikke et billede. Første del af response:")
        print(response.text[:300])
        raise ValueError("URL returnerede ikke et billede")

    with open(save_path, "wb") as file:
        file.write(response.content)

    return save_path