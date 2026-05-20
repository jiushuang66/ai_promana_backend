from typing import Generator

import pymysql
from fastapi import HTTPException, status

from ai_promana_backend.config import settings


def _database_connection_http_error(exc: pymysql.MySQLError) -> HTTPException:
    error_code = exc.args[0] if exc.args else None
    message = "数据库连接失败，请检查 .env 中的 MySQL 配置。"
    hint = "请确认 MySQL 服务已启动，并检查 MYSQL_HOST、MYSQL_PORT、MYSQL_USER、MYSQL_PASSWORD、MYSQL_DATABASE。"

    if error_code == 1045:
        message = "MySQL 用户名或密码错误，数据库拒绝连接。"
        hint = "请更新 .env 中的 MYSQL_USER 和 MYSQL_PASSWORD。"
    elif error_code == 1049:
        message = "目标数据库不存在。"
        hint = "请先执行 `python database_setup.py` 初始化数据库。"
    elif error_code == 2003:
        message = "无法连接到 MySQL 服务。"
        hint = "请确认 MySQL 已启动，并检查 MYSQL_HOST 与 MYSQL_PORT。"

    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail={
            "code": "DATABASE_CONNECTION_ERROR",
            "message": message,
            "hint": hint,
            "mysqlError": str(exc),
        },
    )


def get_connection() -> pymysql.connections.Connection:
    try:
        return pymysql.connect(
            host=settings.MYSQL_HOST,
            port=settings.MYSQL_PORT,
            user=settings.MYSQL_USER,
            password=settings.MYSQL_PASSWORD,
            database=settings.MYSQL_DATABASE,
            charset="utf8mb4",
            autocommit=False,
            cursorclass=pymysql.cursors.DictCursor,
        )
    except pymysql.MySQLError as exc:
        raise _database_connection_http_error(exc) from exc


def get_db() -> Generator[pymysql.connections.Connection, None, None]:
    """FastAPI dependency that yields a pymysql connection."""
    conn = get_connection()
    try:
        yield conn
    finally:
        try:
            conn.close()
        except Exception:
            pass
