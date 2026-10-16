import logging

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from common.config import config

log = logging.getLogger("carlog.auth")

bearer = HTTPBearer(auto_error=True)


def current_user_id(creds: HTTPAuthorizationCredentials = Depends(bearer)):
    try:
        payload = jwt.decode(creds.credentials, config.JWT_SECRET, algorithms=["HS256"])
    except jwt.PyJWTError as error:
        log.info(
            "Токен отклонён",
            extra={"fields": {"error.type": type(error).__name__}},
        )
        raise HTTPException(401, "Неверный или просроченный токен")
    return int(payload["sub"])
