"""In-process HTTP transport for the real Storage SDK; not cloud/IAM proof."""

import base64
import copy
import json
import re
from email import policy
from email.parser import BytesParser
from io import BytesIO
from threading import RLock
from urllib.parse import parse_qs, unquote, urlsplit

import google_crc32c
import requests
from google.api_core.client_options import ClientOptions
from google.auth.credentials import AnonymousCredentials
from google.cloud import storage
from urllib3.response import HTTPResponse


def response(url, status, body, *, media=False, headers=None):
    result = requests.Response()
    result.status_code, result.url = status, url
    result.request = requests.Request("GET", url).prepare()
    result.headers.update(headers or {})
    if media:
        result.raw = HTTPResponse(body=BytesIO(body), headers=result.headers, preload_content=False)
    else:
        result._content = json.dumps(body).encode()
        result.headers["content-type"] = "application/json"
    return result


class StoredHTTP:
    def __init__(self):
        self.objects, self.calls, self.lock = {}, [], RLock()
        self.before = lambda request: None
        self.after = lambda request, result: result

    def client(self, settings):
        return storage.Client(project=settings.project_id, credentials=AnonymousCredentials(),
            client_options=ClientOptions(api_endpoint=settings.api_endpoint), _http=self)

    def request(self, method, url, **kwargs):
        request = {"method": method, "url": url, **kwargs}
        with self.lock:
            self.calls.append(request)
            self.before(request)
            result = self._request(request)
            return self.after(request, result)

    def _request(self, request):
        method, url = request["method"], request["url"]
        parts = urlsplit(url)
        query = parse_qs(parts.query)
        bucket = re.search(r"/b/([^/]+)", parts.path).group(1)
        if method == "GET" and "/o/" not in parts.path:
            return response(url, 200, {"name": bucket, "location": "ASIA-SOUTH1",
                                      "projectNumber": "123", "locationType": "region"})
        if method == "POST":
            assert query["uploadType"] == ["multipart"]
            assert query["ifGenerationMatch"] == ["0"]
            assert "predefinedAcl" not in query
            headers = requests.structures.CaseInsensitiveDict(request["headers"])
            content_type = headers["content-type"]
            if isinstance(content_type, str):
                content_type = content_type.encode()
            mail = BytesParser(policy=policy.default).parsebytes(
                b"Content-Type: " + content_type + b"\r\n\r\n" + request["data"])
            metadata_part, image_part = list(mail.iter_parts())
            meta = json.loads(metadata_part.get_payload(decode=True))
            body = image_part.get_payload(decode=True)
            assert image_part.get_content_type() == "image/png"
            key = (bucket, meta["name"])
            crc = base64.b64encode(google_crc32c.Checksum(body).digest()).decode()
            assert meta["crc32c"] == crc
            if key in self.objects:
                return response(url, 412, {"error": {"message": "exists"}})
            meta.update(bucket=bucket, generation="1", metageneration="1", size=str(len(body)),
                        contentType=image_part.get_content_type())
            self.objects[key] = (meta, body)
            return response(url, 200, meta)
        assert method == "GET", "no cleanup/delete/IAM operation allowed"
        name = unquote(re.search(r"/o/(.*)$", parts.path).group(1))
        if (bucket, name) not in self.objects:
            return response(url, 404, {"error": {"message": "absent"}})
        meta, body = self.objects[(bucket, name)]
        for field, value in (("generation", meta["generation"]),
                             ("ifGenerationMatch", meta["generation"]),
                             ("ifMetagenerationMatch", meta["metageneration"])):
            if field in query and query[field] != [value]:
                return response(url, 412, {"error": {"message": "changed"}})
        if query.get("alt") == ["media"]:
            return response(url, 200, body, media=True, headers={
                "Content-Type": "image/png", "Content-Length": str(len(body)),
                "x-goog-hash": "crc32c=" + meta["crc32c"],
                "x-goog-generation": meta["generation"],
                "x-goog-metageneration": meta["metageneration"]})
        return response(url, 200, copy.deepcopy(meta))
