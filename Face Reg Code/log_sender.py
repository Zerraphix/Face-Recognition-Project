from api_client import API_BASE_URL, session


def send_log(
    user_id,
    device,
    used_method,
    access_granted,
    result,
    image_path=None
):
    data = {
        "user_id": str(user_id),
        "device": device,
        "used_method": used_method,
        "access_granted": "true" if access_granted else "false",
        "result": result
    }

    files = None

    try:
        if image_path:
            files = {
                "file": open(image_path, "rb")
            }

        response = session.post(
            f"{API_BASE_URL}/logs",
            data=data,
            files=files,
            timeout=15
        )

        print("Log status code:", response.status_code)
        print("Log response:", response.text)

        response.raise_for_status()
        return response.json()

    finally:
        if files:
            files["file"].close()