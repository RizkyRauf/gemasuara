from pathlib import Path

import requests

from auth import get_valid_access_token

BASE_URL = "https://open.tiktokapis.com/v2"


def _bearer_headers(access_token):
    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=UTF-8",
    }


def _check_response(data):
    """Raise error kalau response TikTok tidak ok."""
    error = data.get("error", {})
    if error.get("code") != "ok":
        raise RuntimeError(f"TikTok API error: {error}")


def query_creator_info(open_id):
    """Ambil info creator sebelum posting (berguna untuk Direct Post)."""
    access_token = get_valid_access_token(open_id)

    resp = requests.post(
        f"{BASE_URL}/post/publish/creator_info/query/",
        headers=_bearer_headers(access_token),
        json={},
    )
    resp.raise_for_status()
    data = resp.json()
    _check_response(data)
    return data["data"]


def _upload_file_to_url(upload_url, video_path):
    """Upload file video ke upload_url yang diberikan TikTok."""
    video_path = Path(video_path)
    size = video_path.stat().st_size

    with open(video_path, "rb") as f:
        resp = requests.put(
            upload_url,
            data=f,
            headers={
                "Content-Type": "video/mp4",
                "Content-Length": str(size),
                "Content-Range": f"bytes 0-{size - 1}/{size}",
            },
        )
    resp.raise_for_status()
    return resp


def direct_post_video(open_id, video_path, caption, privacy_level="PUBLIC_TO_EVERYONE"):
    """
    Posting video langsung ke profil TikTok.
    Butuh scope 'video.publish' dan app sudah melalui audit TikTok
    agar bisa public. Kalau belum diaudit, biasanya hanya bisa SELF_ONLY.
    """
    access_token = get_valid_access_token(open_id)
    video_path = Path(video_path)
    size = video_path.stat().st_size

    init_resp = requests.post(
        f"{BASE_URL}/post/publish/video/init/",
        headers=_bearer_headers(access_token),
        json={
            "post_info": {
                "title": caption,
                "privacy_level": privacy_level,
                "disable_duet": False,
                "disable_comment": False,
                "disable_stitch": False,
            },
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": size,
                "chunk_size": size,
                "total_chunk_count": 1,
            },
        },
    )
    init_resp.raise_for_status()
    init_data = init_resp.json()
    _check_response(init_data)

    upload_url = init_data["data"]["upload_url"]
    publish_id = init_data["data"]["publish_id"]

    _upload_file_to_url(upload_url, video_path)

    return publish_id, init_data["data"]


def upload_draft_video(open_id, video_path):
    """
    Upload video sebagai draft ke inbox TikTok.
    User harus membuka notifikasi di aplikasi TikTok untuk melanjutkan posting.
    Scope yang dipakai: 'video.upload'.
    """
    access_token = get_valid_access_token(open_id)
    video_path = Path(video_path)
    size = video_path.stat().st_size

    init_resp = requests.post(
        f"{BASE_URL}/post/publish/inbox/video/init/",
        headers=_bearer_headers(access_token),
        json={
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": size,
                "chunk_size": size,
                "total_chunk_count": 1,
            },
        },
    )
    init_resp.raise_for_status()
    init_data = init_resp.json()
    _check_response(init_data)

    upload_url = init_data["data"]["upload_url"]
    publish_id = init_data["data"]["publish_id"]

    _upload_file_to_url(upload_url, video_path)

    return publish_id, init_data["data"]
