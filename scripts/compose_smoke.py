"""Build and verify a disposable local stack, with no user data or provider keys.

Only this script's uniquely named containers, network and volumes are removed.
The regular Compose project and its persistent resources are never selected.
"""

import json
import os
import re
import subprocess
import tempfile
import time
from email.message import Message
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]


def response(
    url: str, method: str = "GET", body: bytes | None = None, **headers: str
) -> tuple[int, bytes, Message]:
    request = Request(url, data=body, method=method, headers=headers)
    try:
        with urlopen(request, timeout=30) as result:
            return result.status, result.read(), result.headers
    except HTTPError as error:
        return error.code, error.read(), error.headers


def main() -> None:
    project = "researchai-smoke-" + uuid4().hex[:12]
    with tempfile.TemporaryDirectory(prefix=project + "-") as directory:
        folder = Path(directory)
        settings = {
            "MONGODB_URI": "mongodb://mongodb:27017",
            "MONGODB_DB_NAME": project.replace("-", "_"),
            "DOCKER_RABBITMQ_URL": "amqp://guest:guest@rabbitmq:5672/",
            "RABBITMQ_DEFAULT_USER": "guest",
            "RABBITMQ_DEFAULT_PASS": "guest",
            "LLAMA_CLOUD_API_KEY": "",
            "VOYAGE_API_KEY": "",
            "OPENROUTER_API_KEY": "",
            "APP_PORT": "0",
            "FRONTEND_PORT": "0",
            "MONGODB_PORT": "0",
            "AMQP_PORT": "0",
            "RABBITMQ_MANAGEMENT_PORT": "0",
            "RESEARCHAI_IMAGE_TAG": project,
        }
        env_file = folder / "smoke.env"
        settings["RESEARCHAI_ENV_FILE"] = str(env_file)
        env_file.write_text("".join(f"{key}={value}\n" for key, value in settings.items()))
        env = {**os.environ, **settings}
        overrides = {
            "services": {
                name: {"container_name": f"{project}-{name}"}
                for name in ("mongodb", "rabbitmq", "gateway", "workers", "frontend")
            },
            "volumes": {
                name: {"name": project + "-" + name} for name in ("mongodb_data", "rabbitmq_data")
            },
            "networks": {"researchai-network": {"name": project + "-network"}},
        }
        overrides["services"]["workers"]["stop_grace_period"] = "15s"
        override_file = folder / "override.json"
        override_file.write_text(json.dumps(overrides))
        command = [
            os.environ.get("DOCKER_BIN", "docker"),
            "compose",
            "--project-name",
            project,
            "--env-file",
            str(env_file),
            "-f",
            str(ROOT / "docker-compose.yml"),
            "-f",
            str(override_file),
            "--profile",
            "local",
        ]

        def compose(*arguments: str, capture: bool = False) -> str:
            result = subprocess.run(
                [*command, *arguments],
                cwd=ROOT,
                env=env,
                check=True,
                capture_output=capture,
                text=True,
                timeout=1800,
            )
            return result.stdout.strip() if capture else ""

        try:
            compose("config", "-q")  # Never print an interpolated environment.
            compose("up", "-d", "--build", "--wait", "--wait-timeout", "240")
            address = compose("port", "frontend", "8080", capture=True)
            base = "http://" + address
            status, html, _ = response(base + "/")
            assert status == 200 and b'<div id="root">' in html, "Built frontend unavailable"
            asset = re.search(rb'(?P<path>/assets/[^" ]+\.js)', html)
            assert asset and response(base + asset["path"].decode())[0] == 200
            lock = json.loads((ROOT / "frontend/package-lock.json").read_text())
            pdf_version = lock["packages"]["node_modules/pdfjs-dist"]["version"]
            assert (
                response(base + f"/pdfjs/{pdf_version}/standard_fonts/LiberationSans-Regular.ttf")[
                    0
                ]
                == 200
            )
            assert response(base + "/api/v1/health")[0] == 200, "API proxy unavailable"
            assert response(base + "/healthz")[0] == 200
            for name in ("gateway", "workers", "frontend"):
                assert compose("exec", "-T", name, "id", "-u", capture=True) != "0"
            compose("exec", "-T", "frontend", "nginx", "-t")
            compose(
                "exec",
                "-T",
                "gateway",
                "python",
                "-c",
                "import importlib.util; from pathlib import Path; "
                "assert not Path('/app/.env').exists(); "
                "assert all(importlib.util.find_spec(name) is None for name in ('pytest', 'ruff', 'ragas'))",
            )
            # Generate a valid, blank fixture using the already approved runtime dependency.
            pdf = subprocess.check_output(
                [
                    *command,
                    "exec",
                    "-T",
                    "gateway",
                    "python",
                    "-c",
                    (
                        "import sys; from io import BytesIO; from pypdf import PdfWriter; "
                        "writer=PdfWriter(); writer.add_blank_page(width=200,height=300); "
                        "buffer=BytesIO(); writer.write(buffer); sys.stdout.buffer.write(buffer.getvalue())"
                    ),
                ],
                cwd=ROOT,
                env=env,
            )
            boundary = uuid4().hex
            multipart = (
                (
                    f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="smoke.pdf"\r\n'
                    "Content-Type: application/pdf\r\n\r\n"
                ).encode()
                + pdf
                + f"\r\n--{boundary}--\r\n".encode()
            )
            status, uploaded, _ = response(
                base + "/api/v1/documents",
                "POST",
                multipart,
                **{"Content-Type": "multipart/form-data; boundary=" + boundary},
            )
            assert status == 201, f"Upload through proxy returned {status}"
            identifier = json.loads(uploaded)["document"]["id"]
            endpoint = base + "/api/v1/documents/" + identifier
            assert response(endpoint + "/pdf")[1] == pdf, "Stored PDF changed through proxy"
            status, job, _ = response(endpoint + "/processing")
            assert status == 200 and json.loads(job)["document_id"] == identifier
            status, duplicate, _ = response(
                base + "/api/v1/documents",
                "POST",
                multipart,
                **{"Content-Type": "multipart/form-data; boundary=" + boundary},
            )
            assert status == 200 and json.loads(duplicate)["is_duplicate"]
            for _ in range(20):
                status, _, _ = response(endpoint, "DELETE")
                if status != 409:
                    break
                time.sleep(0.2)
            assert status == 204 and response(endpoint)[0] == 404
            print(
                "PASS: healthy services, non-root images, built assets, PDF fonts, API proxy, upload/dedup/GridFS/status/delete."
            )
            print("No provider keys were supplied; paid processing and Ragas were not run.")
        except Exception:
            compose("logs", "--no-color", "--tail", "80", "gateway", "workers", "frontend")
            raise
        finally:
            compose("down", "--volumes", "--remove-orphans")


if __name__ == "__main__":
    main()
