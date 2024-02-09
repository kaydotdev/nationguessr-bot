import datetime
import hashlib
import hmac
import json
import logging
from functools import reduce
from typing import Any, Dict, Optional, cast

import aiohttp
from aiogram.exceptions import AiogramError
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.base import BaseStorage, StateType, StorageKey
from vars import AWS_ACCESS_KEY, AWS_FSM_TABLE_NAME, AWS_REGION, AWS_SECRET_KEY


class AiogramFsmError(AiogramError):
    pass


class BotState(StatesGroup):
    select_game = State()
    playing_guess_facts = State()
    playing_guess_flag = State()


class DynamoDBStorage(BaseStorage):
    def __init__(
        self,
        access_key: str,
        secret_key: str,
        table_name: str,
        region: str = "eu-central-1",
    ) -> None:
        if not access_key or not secret_key:
            raise AttributeError("No AWS credentials available")

        self.access_key = access_key
        self.secret_key = secret_key
        self.table_name = table_name
        self.region = region

        self.service = "dynamodb"
        self.host = f"dynamodb.{region}.amazonaws.com"
        self.endpoint = f"https://{self.host}"
        self.logger = logging.getLogger(self.__class__.__name__)

    def _build_authorization_header(
        self, request_body: str, amz_target: str
    ) -> Dict[str, str]:
        t = datetime.datetime.utcnow()
        amz_date, date_stamp = t.strftime("%Y%m%dT%H%M%SZ"), t.strftime("%Y%m%d")

        method = "POST"
        content_type = "application/x-amz-json-1.0"
        canonical_uri, canonical_querystring = "/", ""
        canonical_headers = (
            f"content-type:{content_type}\nhost:{self.host}\n"
            f"x-amz-date:{amz_date}\nx-amz-target:{amz_target}\n"
        )
        signed_headers = "content-type;host;x-amz-date;x-amz-target"

        payload_hash = hashlib.sha256(request_body.encode("utf-8")).hexdigest()
        canonical_request = (
            f"{method}\n{canonical_uri}\n{canonical_querystring}\n"
            f"{canonical_headers}\n{signed_headers}\n{payload_hash}"
        )

        algorithm = "AWS4-HMAC-SHA256"
        credential_scope = f"{date_stamp}/{self.region}/{self.service}/aws4_request"
        string_to_sign = (
            f"{algorithm}\n{amz_date}\n{credential_scope}\n"
            f"{hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()}"
        )

        signing_key = reduce(
            lambda k, msg: hmac.digest(k, msg.encode("utf-8"), hashlib.sha256),
            [date_stamp, self.region, self.service, "aws4_request"],
            ("AWS4" + self.secret_key).encode("utf-8"),
        )
        signature = hmac.new(
            signing_key, string_to_sign.encode("utf-8"), hashlib.sha256
        ).hexdigest()

        authorization_header = (
            f"{algorithm} Credential={self.access_key}/{credential_scope},"
            f" SignedHeaders={signed_headers}, Signature={signature}"
        )

        return {
            "Content-Type": content_type,
            "X-Amz-Date": amz_date,
            "X-Amz-Target": amz_target,
            "Authorization": authorization_header,
        }

    async def set_state(self, key: StorageKey, state: StateType = None) -> None:
        amz_target = "DynamoDB_20120810.PutItem"
        state_parsed = cast(str, state.state if isinstance(state, State) else state)
        new_state = {
            "chat_id": {"S": str(key.chat_id)},
            "user_id": {"S": str(key.user_id)},
            "state": {"S": state_parsed},
        }
        request_parameters = json.dumps({
            "TableName": self.table_name,
            "Item": new_state,
        })
        request_headers = self._build_authorization_header(
            request_parameters, amz_target
        )

        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.endpoint, data=request_parameters, headers=request_headers
            ) as response:
                raw_response = await response.text()

                if response.status != 200:
                    response_err_message = json.loads(raw_response).get("message", "")
                    self.logger.error(
                        "Failed to set a state in the FSM storage:"
                        f" '{response_err_message}'."
                    )

                    raise AiogramFsmError
                else:
                    self.logger.debug(
                        f"Updated new state in the FSM storage: '{new_state}'"
                    )

    async def get_state(self, key: StorageKey) -> Optional[str]:
        pass

    async def set_data(self, key: StorageKey, data: Dict[str, Any]) -> None:
        pass

    async def get_data(self, key: StorageKey) -> Dict[str, Any]:
        pass

    async def close(self) -> None:
        pass


state_storage = DynamoDBStorage(
    AWS_ACCESS_KEY, AWS_SECRET_KEY, AWS_FSM_TABLE_NAME, AWS_REGION
)
