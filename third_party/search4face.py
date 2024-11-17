from PIL import Image
import io
import base64
from typing import List, Literal, Tuple
from types import MappingProxyType
from jsonrpc_async import Server

from third_party.base import ThirdPartyRequest


class Search4Face(ThirdPartyRequest):
    def __init__(
        self,
        api_key: str,
        url: str = "https://search4faces.com/api/json-rpc/v1",
        path_params: MappingProxyType = MappingProxyType({}),
        headers: MappingProxyType = MappingProxyType({}),
        **kwargs,
    ):
        self.base_url = url
        _headers: dict = dict(headers)
        _headers["Content-Type"] = "application/json"
        _headers["x-authorization-token"] = api_key
        super().__init__(url, path_params, MappingProxyType(_headers))

    def cut_face(self, img: str, x: int, y: int, width: int, height: int) -> str:
        image_data = base64.b64decode(img)
        img = Image.open(io.BytesIO(image_data))
        
        right = x + width
        bottom = y + height
        box = (x, y, right, bottom)

        cropped_image = img.crop(box)
        
        buffered = io.BytesIO()
        cropped_image.save(buffered, format="JPEG")  # or use "PNG" if needed
        base64_image = base64.b64encode(buffered.getvalue()).decode("utf-8")
        
        return base64_image

    def add_cuted_faces_to_list(self, img: str, faces: List[dict]) -> List[dict]:
        for face in faces:
            face["img"] = self.cut_face(img, face["x"], face["y"], face["width"], face["height"])
        return faces

    async def detect_face(self, img: str) -> Tuple[int, dict]:
        async with Server(
            self.base_url,
            headers=self.headers,
        ) as server:
            response = await server.detectFaces(image=img)
            import json
            print("Response: ", json.dumps(response, indent=2))
        return (
            200,
            {
                "items": self.add_cuted_faces_to_list(img, response.get("faces", [])),
                "image": response.get("image", ""),
            },
        )

    async def search_face(
        self,
        img: str,
        face: dict,
        db: Literal["vkok_avatar", "vk_wall", "tt_avatar", "ch_avatar", "vkokn_avatar", "sb_photo"] = "vkok_avatar",
    ) -> Tuple[int, dict]:
        async with Server(
            self.base_url,
            headers=self.headers,
        ) as server:
            response = await server.searchFace(
                image=img,
                face=face,
                source=db,
                results=50,
                hidden=True
            )
            res = response.get("profiles", [])
            res.sort(key=lambda obj: float(obj["score"]), reverse=True)
        return 200, {"items": res}

    async def search(self, img: str, search_type: Literal["detect", "search"] = "detect", *args, **kwargs) -> Tuple[int, dict]:
        method = getattr(self, f"{search_type}_face", None)
        if not method:
            return 500, {"items": []}
        return await method(img, *args, **kwargs)
