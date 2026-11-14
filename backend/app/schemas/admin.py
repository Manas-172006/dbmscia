from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, StrictInt


class DatabaseOverviewOut(BaseModel):
    total_users: int
    total_items: int
    available_items: int
    returned_items: int
    removed_items: int
    total_contact_requests: int
    categories_count: int
    locations_count: int
    total_images: int
    total_notifications: int
    total_status_history: int


class TableColumnMeta(BaseModel):
    name: str
    type: str
    nullable: bool
    is_primary: bool
    default: Optional[str] = None


class TableMeta(BaseModel):
    name: str
    type: str  # 'BASE TABLE' or 'VIEW'
    row_count: int
    columns: List[TableColumnMeta]


class TableRowsOut(BaseModel):
    table_name: str
    total_rows: int
    page: int
    page_size: int
    total_pages: int
    columns: List[str]
    rows: List[Dict[str, Any]]


class SqlQueryMeta(BaseModel):
    id: str
    title: str
    category: str
    concept: str
    description: str
    sql_text: str
    params: Optional[Dict[str, Any]] = None


class SqlQueryRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    params: Dict[str, StrictInt] = Field(default_factory=dict)


class SqlQueryResultOut(BaseModel):
    query_id: str
    title: str
    concept: str
    sql_executed: str
    execution_time_ms: float
    row_count: int
    columns: List[str]
    rows: List[Dict[str, Any]]
