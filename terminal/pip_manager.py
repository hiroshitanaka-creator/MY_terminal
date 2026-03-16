import asyncio
import sys
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

router = APIRouter()


class PackageRequest(BaseModel):
    package: str


async def _stream_pip(args: list[str]):
    proc = await asyncio.create_subprocess_exec(
        sys.executable, "-m", "pip", *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    async for line in proc.stdout:
        yield line
    await proc.wait()


@router.get("/api/pip/list")
async def pip_list():
    proc = await asyncio.create_subprocess_exec(
        sys.executable, "-m", "pip", "list", "--format=json",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await proc.communicate()
    import json
    return json.loads(stdout)


@router.post("/api/pip/install")
async def pip_install(req: PackageRequest):
    return StreamingResponse(
        _stream_pip(["install", req.package]),
        media_type="text/plain",
    )


@router.post("/api/pip/uninstall")
async def pip_uninstall(req: PackageRequest):
    return StreamingResponse(
        _stream_pip(["uninstall", "-y", req.package]),
        media_type="text/plain",
    )
