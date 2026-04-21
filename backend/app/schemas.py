from pydantic import BaseModel


class JobResponse(BaseModel):
    jobId: str
    status: str


class JobStatusResponse(BaseModel):
    id: str
    type: str
    status: str
    progress: int
    stage: str | None
    error: str | None


class SegmentResponse(BaseModel):
    index: int
    startSec: int
    endSec: int | None
    name: str
    strategy: str
    confidence: float | None


class PreviewResponse(BaseModel):
    video: dict
    segments: list[SegmentResponse]


class ExportRequest(BaseModel):
    names: list[str] | None = None


class ExportStatusResponse(BaseModel):
    exportId: str
    status: str
    zipPath: str | None
    csvPath: str | None
    txtPath: str | None
    error: str | None
