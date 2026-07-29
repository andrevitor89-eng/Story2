import json
import subprocess
import tempfile
from pathlib import Path

cors = {
    "CORSRules": [
        {
            "AllowedOrigins": ["*"],
            "AllowedMethods": ["GET", "HEAD"],
            "AllowedHeaders": ["*"],
            "ExposeHeaders": ["ETag"],
            "MaxAgeSeconds": 3600,
        }
    ]
}

path = Path(tempfile.gettempdir()) / "story2-cors.json"
path.write_text(json.dumps(cors), encoding="utf-8")

cmd = [
    "docker",
    "compose",
    "run",
    "--rm",
    "--entrypoint",
    "/bin/sh",
    "minio-setup",
    "-c",
    f"mc alias set local http://minio:9000 story2 story2123456 && "
    f"mc cors set local/story2 /cors.json && mc cors get local/story2 && echo cors-ok",
]
# mount cors file
cmd = [
    "docker",
    "compose",
    "run",
    "--rm",
    "-v",
    f"{path}:/cors.json:ro",
    "--entrypoint",
    "/bin/sh",
    "minio-setup",
    "-c",
    "mc alias set local http://minio:9000 story2 story2123456 && "
    "mc cors set local/story2 /cors.json && mc cors get local/story2 && echo cors-ok",
]
print("running", " ".join(cmd))
subprocess.check_call(cmd, cwd=Path(__file__).resolve().parent)
