import math
import logging
import time
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import bindparam, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from app.api.deps import get_current_admin, get_db
from app.core.database import engine, sql_explorer_engine
from app.models.audit import AdminAuditLog
from app.models.category import Category
from app.models.contact import ContactRequest
from app.models.item import FoundItem, ItemImage, ItemStatusHistory
from app.models.location import CampusLocation
from app.models.notification import Notification
from app.models.user import User
from app.queries.catalogue import SQL_QUERIES_CATALOGUE
from app.schemas.admin import (
    DatabaseOverviewOut, SqlQueryMeta, SqlQueryResultOut,
    SqlQueryRunRequest, TableColumnMeta, TableMeta, TableRowsOut
)

router = APIRouter(prefix="/admin", tags=["Admin Database Operations"])
logger = logging.getLogger(__name__)

# Sensitive columns to strictly redact from table explorer
REDACTED_COLUMNS = {
    "password",
    "password_hash",
    "token",
    "access_token",
    "refresh_token",
    "jwt_secret",
    "jwt_secret_key",
    "secret",
    "secret_key",
    "database_url",
    "db_url",
    "connection_string",
    "dsn",
}

# Allowlist of tables and views
ALLOWED_TABLES_VIEWS = {
    "users",
    "categories",
    "subcategories",
    "campus_locations",
    "found_items",
    "item_images",
    "contact_requests",
    "notifications",
    "item_status_history",
    "admin_audit_logs",
    "v_active_found_items",
    "v_category_listing_summary",
}


def _is_sensitive_column(column_name: str) -> bool:
    normalized = column_name.casefold()
    return (
        normalized in REDACTED_COLUMNS
        or "password" in normalized
        or "secret" in normalized
        or "credential" in normalized
    )


def _format_result(cursor):
    columns = list(cursor.keys())
    safe_columns = [column for column in columns if not _is_sensitive_column(column)]
    formatted_rows = []
    for row in cursor.fetchall():
        row_map = row._mapping
        formatted = {}
        for column in safe_columns:
            value = row_map[column]
            if hasattr(value, "isoformat"):
                formatted[column] = value.isoformat()
            elif isinstance(value, bytes):
                formatted[column] = "<binary data>"
            elif isinstance(value, float):
                formatted[column] = round(value, 2)
            else:
                formatted[column] = value
        formatted_rows.append(formatted)
    return safe_columns, formatted_rows


def _validate_catalogue_query(sql_text: str) -> None:
    statement = sql_text.strip()
    if statement.endswith(";"):
        statement = statement[:-1].rstrip()
    if (
        not (statement.upper().startswith("SELECT ") or statement.upper().startswith("SELECT\n"))
        or ";" in statement
    ):
        logger.error("A non-read-only statement was found in the SQL query catalogue.")
        raise HTTPException(
            status_code=500,
            detail="The predefined SQL query is not available.",
        )


def _validate_explorer_grants(connection) -> None:
    if sql_explorer_engine is None:
        raise HTTPException(
            status_code=503,
            detail="The SQL Explorer read-only database connection is not configured.",
        )

    database_name = sql_explorer_engine.url.database
    grants = [
        row[0].replace("`", "").upper()
        for row in connection.execute(text("SHOW GRANTS")).fetchall()
    ]
    select_grant_prefix = f"GRANT SELECT ON {database_name}.* TO ".upper()
    has_database_select = False
    for grant in grants:
        if grant.startswith("GRANT USAGE ON *.* TO "):
            continue
        if grant.startswith(select_grant_prefix):
            has_database_select = True
            continue
        raise HTTPException(
            status_code=503,
            detail="The SQL Explorer account must have SELECT-only access to the Found It database.",
        )
    if not has_database_select:
        raise HTTPException(
            status_code=503,
            detail="The SQL Explorer account must have SELECT-only access to the Found It database.",
        )


@router.get("/database/overview", response_model=DatabaseOverviewOut)
def get_database_overview(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin),
):
    total_users = db.query(User).count()
    total_items = db.query(FoundItem).count()
    available_items = db.query(FoundItem).filter(FoundItem.status == "available").count()
    returned_items = db.query(FoundItem).filter(FoundItem.status == "returned").count()
    removed_items = db.query(FoundItem).filter(FoundItem.status == "removed").count()
    total_contact_requests = db.query(ContactRequest).count()
    categories_count = db.query(Category).count()
    locations_count = db.query(CampusLocation).count()
    total_images = db.query(ItemImage).count()
    total_notifications = db.query(Notification).count()
    total_status_history = db.query(ItemStatusHistory).count()

    return DatabaseOverviewOut(
        total_users=total_users,
        total_items=total_items,
        available_items=available_items,
        returned_items=returned_items,
        removed_items=removed_items,
        total_contact_requests=total_contact_requests,
        categories_count=categories_count,
        locations_count=locations_count,
        total_images=total_images,
        total_notifications=total_notifications,
        total_status_history=total_status_history,
    )


@router.get("/database/tables", response_model=List[TableMeta])
def get_tables(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin),
):
    sql = text("""
        SELECT 
            t.TABLE_NAME, 
            t.TABLE_TYPE
        FROM information_schema.tables t
        WHERE t.TABLE_SCHEMA = DATABASE()
          AND t.TABLE_NAME IN :allowed_tables
        ORDER BY t.TABLE_TYPE DESC, t.TABLE_NAME ASC;
    """)
    table_rows = db.execute(
        sql.bindparams(bindparam("allowed_tables", expanding=True)),
        {"allowed_tables": tuple(ALLOWED_TABLES_VIEWS)},
    ).fetchall()

    result = []
    for t_name, t_type in table_rows:
        # Get count
        count_res = db.execute(text(f"SELECT COUNT(*) FROM `{t_name}`")).scalar()
        row_count = int(count_res or 0)

        # Get column definitions
        col_sql = text("""
            SELECT 
                COLUMN_NAME, 
                DATA_TYPE, 
                IS_NULLABLE, 
                COLUMN_KEY, 
                COLUMN_DEFAULT
            FROM information_schema.columns
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = :table_name
            ORDER BY ORDINAL_POSITION ASC;
        """)
        cols = db.execute(col_sql, {"table_name": t_name}).fetchall()
        columns_meta = []
        for col_name, data_type, is_nullable, col_key, col_default in cols:
            columns_meta.append(
                TableColumnMeta(
                    name=col_name,
                    type=data_type,
                    nullable=(is_nullable == "YES"),
                    is_primary=(col_key == "PRI"),
                    default=str(col_default) if col_default is not None else None,
                )
            )

        result.append(
            TableMeta(
                name=t_name,
                type=t_type,
                row_count=row_count,
                columns=columns_meta,
            )
        )

    return result


@router.get("/database/tables/{table_name}/rows", response_model=TableRowsOut)
def get_table_rows(
    table_name: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(15, ge=1, le=100),
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin),
):
    if table_name not in ALLOWED_TABLES_VIEWS:
        raise HTTPException(
            status_code=400,
            detail=f"Table '{table_name}' is not in the allowlist of accessible tables.",
        )

    # Count rows
    count_sql = text(f"SELECT COUNT(*) FROM `{table_name}`")
    total_rows = db.execute(count_sql).scalar() or 0
    total_pages = max(1, math.ceil(total_rows / page_size))
    offset = (page - 1) * page_size

    # Fetch rows
    fetch_sql = text(f"SELECT * FROM `{table_name}` LIMIT :limit OFFSET :offset")
    rows_cursor = db.execute(fetch_sql, {"limit": page_size, "offset": offset})
    column_names = list(rows_cursor.keys())

    safe_columns = [column for column in column_names if not _is_sensitive_column(column)]

    rows_data = []
    for r in rows_cursor.fetchall():
        # Format datetimes & non-serializable objects
        formatted = {}
        for k in safe_columns:
            v = r._mapping[k]
            if hasattr(v, "isoformat"):
                formatted[k] = v.isoformat()
            elif isinstance(v, bytes):
                formatted[k] = "<binary data>"
            else:
                formatted[k] = v
        rows_data.append(formatted)

    return TableRowsOut(
        table_name=table_name,
        total_rows=total_rows,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        columns=safe_columns,
        rows=rows_data,
    )


@router.get("/sql/queries", response_model=List[SqlQueryMeta])
def list_sql_queries(
    admin_user: User = Depends(get_current_admin),
):
    catalogue_list = []
    for q_id, q_data in SQL_QUERIES_CATALOGUE.items():
        catalogue_list.append(
            SqlQueryMeta(
                id=q_data["id"],
                title=q_data["title"],
                category=q_data["category"],
                concept=q_data["concept"],
                description=q_data["description"],
                sql_text=q_data["sql_text"],
                params=q_data.get("default_params", {}),
            )
        )
    return catalogue_list


@router.post("/sql/queries/{query_id}/run", response_model=SqlQueryResultOut)
def run_predefined_query(
    query_id: str,
    run_req: Optional[SqlQueryRunRequest] = None,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin),
):
    if query_id not in SQL_QUERIES_CATALOGUE:
        raise HTTPException(
            status_code=404,
            detail=f"Query '{query_id}' not found in the verified predefined catalogue.",
        )

    q_data = SQL_QUERIES_CATALOGUE[query_id]
    sql_text = q_data["sql_text"]
    _validate_catalogue_query(sql_text)

    merged_params = dict(q_data.get("default_params", {}))
    supplied_params = run_req.params if run_req else {}
    unexpected_params = set(supplied_params) - set(merged_params)
    if unexpected_params:
        raise HTTPException(
            status_code=422,
            detail="One or more parameters are not supported by this predefined query.",
        )
    merged_params.update(supplied_params)
    for name, value in merged_params.items():
        if type(value) is not int:
            raise HTTPException(status_code=500, detail="The predefined SQL parameters are invalid.")
        if name == "limit" and not 1 <= value <= 100:
            raise HTTPException(status_code=422, detail="'limit' must be between 1 and 100.")
        if name == "min_count" and not 1 <= value <= 100000:
            raise HTTPException(status_code=422, detail="'min_count' must be between 1 and 100000.")
        if name == "min_days" and not 0 <= value <= 3650:
            raise HTTPException(status_code=422, detail="'min_days' must be between 0 and 3650.")

    # Execute parameterized query
    start_time = time.perf_counter()
    if (
        sql_explorer_engine is None
        or sql_explorer_engine.url == engine.url
        or sql_explorer_engine.url.username == engine.url.username
    ):
        raise HTTPException(
            status_code=503,
            detail="The SQL Explorer requires a separate read-only MySQL account.",
        )
    try:
        with sql_explorer_engine.connect() as explorer_db:
            _validate_explorer_grants(explorer_db)
            cursor = explorer_db.execute(text(sql_text), merged_params)
            safe_columns, formatted_rows = _format_result(cursor)
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
    except HTTPException:
        raise
    except SQLAlchemyError:
        logger.exception("SQL Explorer query execution failed for query_id=%s", query_id)
        raise HTTPException(
            status_code=503,
            detail="The SQL Explorer could not complete the query. Check its read-only MySQL connection.",
        )

    # Log audit event
    audit = AdminAuditLog(
        admin_user_id=admin_user.id,
        action="RUN_SQL_QUERY",
        target_type="sql_explorer",
        target_reference=query_id,
    )
    db.add(audit)
    db.commit()

    return SqlQueryResultOut(
        query_id=query_id,
        title=q_data["title"],
        concept=q_data["concept"],
        sql_executed=q_data["sql_text"],
        execution_time_ms=duration_ms,
        row_count=len(formatted_rows),
        columns=safe_columns,
        rows=formatted_rows,
    )


@router.get("/database/relationships")
def get_relationships(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin),
):
    sql = text("""
        SELECT 
            TABLE_NAME, 
            COLUMN_NAME, 
            CONSTRAINT_NAME, 
            REFERENCED_TABLE_NAME, 
            REFERENCED_COLUMN_NAME
        FROM information_schema.KEY_COLUMN_USAGE
        WHERE TABLE_SCHEMA = DATABASE()
          AND REFERENCED_TABLE_NAME IS NOT NULL
        ORDER BY TABLE_NAME, COLUMN_NAME;
    """)
    rows = db.execute(sql).fetchall()
    return [
        {
            "from_table": r[0],
            "from_column": r[1],
            "constraint_name": r[2],
            "to_table": r[3],
            "to_column": r[4],
        }
        for r in rows
    ]
