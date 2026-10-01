from pydantic import BaseModel, Field


class OptimizationAnalyzeRequest(BaseModel):
    metric_id: int | None = Field(default=None, gt=0)


class OptimizationExecuteRequest(BaseModel):
    metric_id: int = Field(gt=0)
    expected_action: str = Field(min_length=1, max_length=80)
    confirmed: bool = False