import black
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class FormatRequest(BaseModel):
    code: str
    line_length: int = 88


class FormatResponse(BaseModel):
    formatted: str
    changed: bool


@router.post("/api/format", response_model=FormatResponse)
async def format_code(req: FormatRequest):
    mode = black.Mode(line_length=req.line_length)
    try:
        formatted = black.format_str(req.code, mode=mode)
        return FormatResponse(formatted=formatted, changed=formatted != req.code)
    except black.InvalidInput as e:
        raise HTTPException(status_code=422, detail=str(e))
