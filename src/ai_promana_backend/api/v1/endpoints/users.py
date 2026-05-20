# TODO: /api/auth/* 当前为首版契约接口，后续需要与旧 /api/v1/users/* 统一认证模型、token 刷新和权限依赖。
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query
import pymysql
from datetime import datetime, timedelta
from uuid import uuid4
from ai_promana_backend.database import get_db
from ai_promana_backend.core.security import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)
from ai_promana_backend.schemas.user import (
    UserOut,
    LoginResponse,
)
from ai_promana_backend.api.v1.endpoints import _mock

router = APIRouter()

@router.post("/login", response_model=LoginResponse, summary="用户登录", description="用户登录获取访问令牌")
def login_user(
    username: str = Query(..., description="用户名"),
    password: str = Query(..., description="密码"),
    db: pymysql.connections.Connection = Depends(get_db)
):
    cursor = None
    try:
        cursor = db.cursor()
        
        # 查询用户
        cursor.execute(
            "SELECT id, username, email, phone, real_name AS full_name, role, password_hash AS password, created_at, updated_at FROM users WHERE username = %s",
            (username,)
        )
        user = cursor.fetchone()
        
        # 验证用户是否存在且密码正确
        if not user or not verify_password(password, user["password"]):
            raise HTTPException(status_code=401, detail="用户名或密码错误")
        
        # 创建访问令牌
        access_token = create_access_token(data={"sub": user["id"], "username": user["username"], "role": user["role"]})
        
        return LoginResponse(
            access_token=access_token,
            user=UserOut(
                id=user["id"],
                username=user["username"],
                email=user["email"],
                phone=user["phone"],
                full_name=user["full_name"],
                role=user["role"],
                created_at=user["created_at"].strftime("%Y-%m-%d %H:%M:%S") if hasattr(user["created_at"], "strftime") else user["created_at"],
                updated_at=user["updated_at"].strftime("%Y-%m-%d %H:%M:%S") if hasattr(user["updated_at"], "strftime") else user["updated_at"]
            )
        )
    
    except pymysql.MySQLError as e:
        raise HTTPException(status_code=500, detail=f"数据库操作失败：{str(e)}")
    finally:
        if cursor:
            cursor.close()


auth_router = APIRouter()


ACCESS_EXPIRES_SECONDS = 7200
REFRESH_EXPIRES_DAYS = 30


def _utc_now() -> datetime:
    return datetime.utcnow()


def _build_token_payload(current_user: dict[str, Any], session_id: str) -> dict[str, Any]:
    return {
        "sub": str(current_user["id"]),
        "username": current_user["username"],
        "role": current_user.get("platformRole", "user"),
        "sid": session_id,
    }


def _issue_tokens(current_user: dict[str, Any], session_id: str) -> dict[str, Any]:
    token_payload = _build_token_payload(current_user, session_id)
    access_expires_at = _utc_now() + timedelta(seconds=ACCESS_EXPIRES_SECONDS)
    refresh_expires_at = _utc_now() + timedelta(days=REFRESH_EXPIRES_DAYS)
    token_payload = {
        **token_payload,
    }
    return {
        "accessToken": create_access_token(
            data=token_payload,
            expires_delta=timedelta(seconds=ACCESS_EXPIRES_SECONDS),
        ),
        "refreshToken": create_access_token(
            data={**token_payload, "tokenType": "refresh"},
            expires_delta=timedelta(days=REFRESH_EXPIRES_DAYS),
        ),
        "expiresIn": ACCESS_EXPIRES_SECONDS,
        "accessExpiresAt": access_expires_at,
        "refreshExpiresAt": refresh_expires_at,
    }


def _mock_current_user(username: str | None = None) -> dict[str, Any]:
    current_user = _mock.current_user()
    if username:
        current_user["username"] = username
        current_user["name"] = current_user.get("name") or username
    current_user["accountStatus"] = current_user.get("accountStatus", "active")
    return current_user


def _issue_login_payload(current_user: dict[str, Any]) -> dict[str, Any]:
    session_id = f"sess_{uuid4().hex}"
    tokens = _issue_tokens(current_user, session_id)
    return {
        **tokens,
        "sessionId": session_id,
        "tokenType": "Bearer",
        "user": current_user,
        "currentUser": current_user,
        "permissions": current_user.get("permissions", []),
        "redirectPath": "/dashboard",
    }


def _register_placeholder_email(account: str) -> str:
    normalized = account.strip().lower().replace(" ", "_")
    return f"{normalized}@pending.local"


def _build_current_user_from_db(user: dict[str, Any]) -> dict[str, Any]:
    current_user = _mock_current_user(user["username"])
    current_user["id"] = str(user["id"])
    current_user["name"] = user.get("full_name") or current_user.get("name") or user["username"]
    current_user["nickname"] = current_user.get("nickname") or current_user["name"]
    current_user["platformRole"] = user.get("role", current_user.get("platformRole", "user"))
    current_user["email"] = user.get("email")
    current_user["phone"] = user.get("phone")
    current_user["department"] = user.get("department")
    current_user["accountStatus"] = user.get("status", current_user.get("accountStatus", "active"))
    return current_user


def _persist_user_session(
    cursor: Any,
    user_id: int,
    login_payload: dict[str, Any],
    user_agent: str | None = None,
    ip_address: str | None = None,
) -> None:
    cursor.execute("UPDATE user_sessions SET is_current = 0 WHERE user_id = %s AND status = 'active'", (user_id,))
    cursor.execute(
        """
        INSERT INTO user_sessions (
            session_id, user_id, access_token, refresh_token, access_expires_at, refresh_expires_at,
            device_name, ip_address, location, user_agent, is_current, status, last_active_at, revoked_at, created_at, updated_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            login_payload["sessionId"],
            user_id,
            login_payload["accessToken"],
            login_payload["refreshToken"],
            login_payload["accessExpiresAt"],
            login_payload["refreshExpiresAt"],
            "web",
            ip_address,
            None,
            user_agent,
            1,
            "active",
            _utc_now(),
            None,
            _utc_now(),
            _utc_now(),
        ),
    )


def _find_active_session_by_access_token(cursor: Any, access_token: str) -> dict[str, Any] | None:
    cursor.execute(
        """
        SELECT session_id, user_id, access_token, refresh_token, access_expires_at, refresh_expires_at, status
        FROM user_sessions
        WHERE access_token = %s AND status = 'active'
        LIMIT 1
        """,
        (access_token,),
    )
    return cursor.fetchone()


def _find_active_session_by_refresh_token(cursor: Any, refresh_token: str) -> dict[str, Any] | None:
    cursor.execute(
        """
        SELECT session_id, user_id, access_token, refresh_token, access_expires_at, refresh_expires_at, status
        FROM user_sessions
        WHERE refresh_token = %s AND status = 'active'
        LIMIT 1
        """,
        (refresh_token,),
    )
    return cursor.fetchone()


def _fetch_user_by_id(cursor: Any, user_id: int) -> dict[str, Any] | None:
    cursor.execute(
        """
        SELECT id, username, email, phone, real_name AS full_name, role, department, status, created_at, updated_at
        FROM users
        WHERE id = %s
        LIMIT 1
        """,
        (user_id,),
    )
    return cursor.fetchone()


@auth_router.post("/login", summary="账号密码登录")
def auth_login(
    username: str = Query(..., description="用户名"),
    password: str = Query(..., description="密码"),
    userAgent: str | None = Header(default=None, alias="User-Agent"),
    db: pymysql.connections.Connection = Depends(get_db),
):
    cursor = None
    try:
        cursor = db.cursor()
        cursor.execute(
            "SELECT id, username, email, phone, real_name AS full_name, role, password_hash AS password, created_at, updated_at "
            "FROM users WHERE username = %s",
            (username,),
        )
        user = cursor.fetchone()

        if not user or not verify_password(password, user["password"]):
            raise HTTPException(status_code=401, detail="用户名或密码错误")

        current_user = _build_current_user_from_db(user)
        login_payload = _issue_login_payload(current_user)
        _persist_user_session(cursor, int(user["id"]), login_payload, user_agent=userAgent)
        db.commit()
        return _mock.api_response(login_payload)
    except pymysql.MySQLError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"数据库操作失败：{str(e)}")
    finally:
        if cursor:
            cursor.close()


@auth_router.post("/register", summary="注册")
def auth_register(
    account: str = Query(..., min_length=2, max_length=64, description="研发工号 / 平台账号"),
    name: str | None = Query(None, min_length=2, max_length=40, description="姓名"),
    department: str | None = Query(None, min_length=2, max_length=60, description="部门名称"),
    password: str = Query(..., min_length=8, max_length=128, description="密码"),
    confirmPassword: str | None = Query(None, min_length=8, max_length=128, description="确认密码"),
    departmentId: str | None = Query(None, description="部门 ID"),
    inviteCode: str | None = Query(None, description="邀请码"),
    captchaToken: str | None = Query(None, description="验证码 token"),
    clientType: str = Query("web", description="客户端类型"),
    db: pymysql.connections.Connection = Depends(get_db),
):
    normalized_account = account.strip()
    normalized_name = name.strip() if name else None
    normalized_department = department.strip() if department else None

    if not normalized_account:
        raise HTTPException(status_code=400, detail={"code": "AUTH_REGISTER_PARAM_INVALID", "message": "账号不能为空"})
    if confirmPassword is not None and password != confirmPassword:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "AUTH_PASSWORD_CONFIRM_NOT_MATCH",
                "message": "两次输入密码不一致",
            },
        )

    cursor = None
    try:
        cursor = db.cursor()
        cursor.execute("SELECT id FROM users WHERE username = %s LIMIT 1", (normalized_account,))
        if cursor.fetchone():
            raise HTTPException(
                status_code=409,
                detail={"code": "AUTH_ACCOUNT_EXISTS", "message": "账号已存在"},
            )

        placeholder_email = _register_placeholder_email(normalized_account)
        cursor.execute("SELECT id FROM users WHERE email = %s LIMIT 1", (placeholder_email,))
        if cursor.fetchone():
            placeholder_email = f"{normalized_account.lower()}_{int(datetime.now().timestamp())}@pending.local"

        now = datetime.now()
        password_hash = get_password_hash(password)
        cursor.execute(
            """
            INSERT INTO users (
                username, nickname, password_hash, real_name, email, phone, avatar_url,
                role, department, department_id, position, note, status, join_date,
                last_login_time, last_login_ip, password_updated_at, failed_login_count,
                locked_until, version, created_at, updated_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                normalized_account,
                normalized_name or normalized_account,
                password_hash,
                normalized_name,
                placeholder_email,
                None,
                None,
                "user",
                normalized_department,
                departmentId,
                None,
                f"inviteCode={inviteCode or ''};captchaToken={captchaToken or ''};clientType={clientType}",
                "pending",
                now.date(),
                None,
                None,
                now,
                0,
                None,
                1,
                now,
                now,
            ),
        )
        user_id = cursor.lastrowid
        db.commit()

        return _mock.api_response(
            {
                "registrationId": _mock.make_id("reg"),
                "userId": str(user_id),
                "account": normalized_account,
                "name": normalized_name,
                "department": normalized_department,
                "departmentId": departmentId,
                "accountStatus": "pending",
                "reviewStatus": "pending",
                "submittedAt": _mock.now_iso(),
                "message": "注册申请已提交，请等待系统管理员审核。",
                "redirectPath": "/login",
                "clientType": clientType,
            }
        )
    except pymysql.MySQLError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail={"code": "COMMON_SERVER_ERROR", "message": f"数据库操作失败：{str(e)}"})
    finally:
        if cursor:
            cursor.close()


@auth_router.get("/register/config", summary="获取注册配置")
def get_register_config():
    return _mock.api_response(
        {
            "registrationEnabled": True,
            "reviewRequired": True,
            "emailVerificationRequired": False,
            "captchaRequired": False,
            "inviteCodeRequired": False,
            "passwordPolicy": {
                "minLength": 8,
                "maxLength": 128,
                "requireUppercase": True,
                "requireLowercase": True,
                "requireNumber": True,
                "requireSpecialChar": False,
            },
            "departmentMode": "free_text",
        }
    )


@auth_router.get("/register/check-account", summary="校验账号可用性")
def check_register_account(
    account: str = Query(..., min_length=2, max_length=64, description="待校验账号"),
    db: pymysql.connections.Connection = Depends(get_db),
):
    normalized_account = account.strip()
    cursor = None
    try:
        cursor = db.cursor()
        cursor.execute("SELECT id FROM users WHERE username = %s LIMIT 1", (normalized_account,))
        exists = cursor.fetchone() is not None
        return _mock.api_response({"available": not exists, "normalizedAccount": normalized_account})
    except pymysql.MySQLError as e:
        raise HTTPException(status_code=500, detail={"code": "COMMON_SERVER_ERROR", "message": f"数据库操作失败：{str(e)}"})
    finally:
        if cursor:
            cursor.close()


@auth_router.get("/register/check-email", summary="校验邮箱可用性")
def check_register_email(email: str = Query(..., description="待校验邮箱"), db: pymysql.connections.Connection = Depends(get_db)):
    normalized_email = email.strip().lower()
    cursor = None
    try:
        cursor = db.cursor()
        cursor.execute("SELECT id FROM users WHERE email = %s LIMIT 1", (normalized_email,))
        exists = cursor.fetchone() is not None
        return _mock.api_response({"available": not exists, "normalizedEmail": normalized_email})
    except pymysql.MySQLError as e:
        raise HTTPException(status_code=500, detail={"code": "COMMON_SERVER_ERROR", "message": f"数据库操作失败：{str(e)}"})
    finally:
        if cursor:
            cursor.close()


# TODO: 从 token 解析当前用户，查询最新资料、角色和权限，不再返回静态 CurrentUser。
@auth_router.get("/me", summary="获取当前用户")
def get_current_user(
    authorization: str | None = Header(default=None),
    db: pymysql.connections.Connection = Depends(get_db),
):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail={"code": "AUTH_TOKEN_MISSING", "message": "缺少访问令牌"})

    token = authorization.split(" ", 1)[1]
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail={"code": "AUTH_TOKEN_INVALID", "message": "Token 无效或已过期"})

    cursor = None
    try:
        cursor = db.cursor()
        session = _find_active_session_by_access_token(cursor, token)
        if session is None:
            raise HTTPException(status_code=401, detail={"code": "AUTH_SESSION_INVALID", "message": "登录会话不存在或已失效"})
        if session.get("access_expires_at") and session["access_expires_at"] < _utc_now():
            cursor.execute(
                "UPDATE user_sessions SET status = 'expired', is_current = 0, updated_at = %s WHERE session_id = %s",
                (_utc_now(), session["session_id"]),
            )
            db.commit()
            raise HTTPException(status_code=401, detail={"code": "AUTH_TOKEN_EXPIRED", "message": "访问令牌已过期"})

        user = _fetch_user_by_id(cursor, int(session["user_id"]))
        if user is None:
            raise HTTPException(status_code=401, detail={"code": "AUTH_USER_NOT_FOUND", "message": "用户不存在"})

        cursor.execute(
            "UPDATE user_sessions SET last_active_at = %s, updated_at = %s WHERE session_id = %s",
            (_utc_now(), _utc_now(), session["session_id"]),
        )
        db.commit()
        return _mock.api_response(_build_current_user_from_db(user))
    except pymysql.MySQLError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail={"code": "COMMON_SERVER_ERROR", "message": f"数据库操作失败：{str(e)}"})
    finally:
        if cursor:
            cursor.close()


# TODO: 校验 refreshToken 有效期和撤销状态，签发新 accessToken 并按策略轮换 refreshToken。
@auth_router.post("/refresh", summary="刷新会话")
def refresh_session(
    refreshToken: str | None = Query(None, description="登录响应返回的 refreshToken"),
    db: pymysql.connections.Connection = Depends(get_db),
):
    token = refreshToken
    decoded = decode_access_token(token) if token else None
    if token is None or decoded is None:
        raise HTTPException(status_code=401, detail={"code": "AUTH_TOKEN_INVALID", "message": "refreshToken 无效或已过期"})
    if decoded.get("tokenType") != "refresh":
        raise HTTPException(status_code=401, detail={"code": "AUTH_TOKEN_INVALID", "message": "refreshToken 类型错误"})

    cursor = None
    try:
        cursor = db.cursor()
        session = _find_active_session_by_refresh_token(cursor, token)
        if session is None:
            raise HTTPException(status_code=401, detail={"code": "AUTH_SESSION_INVALID", "message": "刷新会话不存在或已失效"})
        if session.get("refresh_expires_at") and session["refresh_expires_at"] < _utc_now():
            cursor.execute(
                "UPDATE user_sessions SET status = 'expired', is_current = 0, updated_at = %s WHERE session_id = %s",
                (_utc_now(), session["session_id"]),
            )
            db.commit()
            raise HTTPException(status_code=401, detail={"code": "AUTH_TOKEN_EXPIRED", "message": "refreshToken 已过期"})

        user = _fetch_user_by_id(cursor, int(session["user_id"]))
        if user is None:
            raise HTTPException(status_code=401, detail={"code": "AUTH_USER_NOT_FOUND", "message": "用户不存在"})

        current_user = _build_current_user_from_db(user)
        tokens = _issue_tokens(current_user, session["session_id"])
        cursor.execute(
            """
            UPDATE user_sessions
            SET access_token = %s, refresh_token = %s, access_expires_at = %s, refresh_expires_at = %s,
                last_active_at = %s, updated_at = %s, status = 'active', is_current = 1
            WHERE session_id = %s
            """,
            (
                tokens["accessToken"],
                tokens["refreshToken"],
                tokens["accessExpiresAt"],
                tokens["refreshExpiresAt"],
                _utc_now(),
                _utc_now(),
                session["session_id"],
            ),
        )
        db.commit()
        return _mock.api_response(
            {
                "accessToken": tokens["accessToken"],
                "refreshToken": tokens["refreshToken"],
                "expiresIn": tokens["expiresIn"],
                "tokenType": "Bearer",
                "sessionId": session["session_id"],
            }
        )
    except pymysql.MySQLError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail={"code": "COMMON_SERVER_ERROR", "message": f"数据库操作失败：{str(e)}"})
    finally:
        if cursor:
            cursor.close()


@auth_router.post("/logout", summary="退出登录")
def logout(
    authorization: str | None = Header(default=None),
    db: pymysql.connections.Connection = Depends(get_db),
):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail={"code": "AUTH_TOKEN_MISSING", "message": "缺少访问令牌"})

    token = authorization.split(" ", 1)[1]
    cursor = None
    try:
        cursor = db.cursor()
        session = _find_active_session_by_access_token(cursor, token)
        if session is None:
            return _mock.api_response(True)
        cursor.execute(
            """
            UPDATE user_sessions
            SET status = 'revoked', is_current = 0, revoked_at = %s, updated_at = %s
            WHERE session_id = %s
            """,
            (_utc_now(), _utc_now(), session["session_id"]),
        )
        db.commit()
        return _mock.api_response(True)
    except pymysql.MySQLError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail={"code": "COMMON_SERVER_ERROR", "message": f"数据库操作失败：{str(e)}"})
    finally:
        if cursor:
            cursor.close()


@auth_router.get("/providers", summary="第三方登录方式")
def list_auth_providers():
    return _mock.api_response(
        [
            {"id": "fingerprint", "name": "Fingerprint", "enabled": True},
            {"id": "qr_code_scanner", "name": "QR Code Scanner", "enabled": True},
        ]
    )


@auth_router.post("/social/start", summary="发起扫码/外部登录")
def start_social_login(provider: str = Query("fingerprint", description="第三方登录方式")):
    return _mock.api_response(
        {
            "provider": provider,
            "state": _mock.make_id("social"),
            "qrCodeUrl": f"https://example.com/auth/{provider}/qr",
            "expiresIn": 300,
        }
    )


@auth_router.post("/social/confirm", summary="第三方登录确认")
def confirm_social_login(
    provider: str = Query("fingerprint", description="第三方登录方式"),
    state: str | None = Query(None, description="登录状态标识"),
):
    current_user = _mock_current_user()
    auth_payload = _issue_login_payload(current_user)
    return _mock.api_response(
        {
            "provider": provider,
            "state": state,
            **auth_payload,
        }
    )
