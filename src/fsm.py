import datetime
import hashlib
import hmac
import json
import logging
from functools import reduce
from typing import Any, Dict, Optional, cast

import aiohttp
from aiogram.exceptions import DetailedAiogramError
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.base import BaseStorage, StateType, StorageKey
from vars import AWS_ACCESS_KEY, AWS_FSM_TABLE_NAME, AWS_REGION, AWS_SECRET_KEY


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

        self._access_key = access_key
        self._secret_key = secret_key
        self._table_name = table_name
        self._region = region

        self._service = "dynamodb"
        self._host = f"{self._service}.{self._region}.amazonaws.com"
        self._endpoint = f"https://{self._host}"
        self._logger = logging.getLogger(self.__class__.__name__)

    def _build_authorization_header(
        self, request_body: str, amz_target: str
    ) -> Dict[str, str]:
        t = datetime.datetime.utcnow()
        amz_date, date_stamp = t.strftime("%Y%m%dT%H%M%SZ"), t.strftime("%Y%m%d")

        method = "POST"
        content_type = "application/x-amz-json-1.0"
        canonical_uri, canonical_querystring = "/", ""
        canonical_headers = (
            f"content-type:{content_type}\nhost:{self._host}\n"
            f"x-amz-date:{amz_date}\nx-amz-target:{amz_target}\n"
        )
        signed_headers = "content-type;host;x-amz-date;x-amz-target"

        payload_hash = hashlib.sha256(request_body.encode("utf-8")).hexdigest()
        canonical_request = (
            f"{method}\n{canonical_uri}\n{canonical_querystring}\n"
            f"{canonical_headers}\n{signed_headers}\n{payload_hash}"
        )

        algorithm = "AWS4-HMAC-SHA256"
        credential_scope = f"{date_stamp}/{self._region}/{self._service}/aws4_request"
        string_to_sign = (
            f"{algorithm}\n{amz_date}\n{credential_scope}\n"
            f"{hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()}"
        )

        signing_key = reduce(
            lambda k, msg: hmac.digest(k, msg.encode("utf-8"), hashlib.sha256),
            [date_stamp, self._region, self._service, "aws4_request"],
            ("AWS4" + self._secret_key).encode("utf-8"),
        )
        signature = hmac.new(
            signing_key, string_to_sign.encode("utf-8"), hashlib.sha256
        ).hexdigest()

        authorization_header = (
            f"{algorithm} Credential={self._access_key}/{credential_scope},"
            f" SignedHeaders={signed_headers}, Signature={signature}"
        )

        return {
            "Content-Type": content_type,
            "X-Amz-Date": amz_date,
            "X-Amz-Target": amz_target,
            "Authorization": authorization_header,
        }

    async def _request_table(self, amz_target: str, request_parameters: str) -> str:
        request_headers = self._build_authorization_header(
            request_parameters, amz_target
        )

        async with aiohttp.ClientSession() as session:
            async with session.post(
                self._endpoint, data=request_parameters, headers=request_headers
            ) as response:
                response_body = await response.text()

                if response.status != 200:
                    response_err_message = json.loads(response_body).get("message", "")
                    self._logger.error(
                        f"Failed to request a state table with '{amz_target}' target in"
                        f" the FSM storage: '{response_err_message}'"
                    )
                    raise DetailedAiogramError(
                        "Failed to request a state table in the FSM storage"
                    )

        self._logger.debug(
            f"Successfully requested a state table with '{amz_target}' target in"
            " the FSM storage"
        )

        return response_body

    async def set_state(self, key: StorageKey, state: StateType = None) -> None:
        state_key = {
            "chat_id": {"S": str(key.chat_id)},
            "user_id": {"S": str(key.user_id)},
        }

        if state is None:
            amz_target = "DynamoDB_20120810.DeleteItem"
            request_parameters = json.dumps({
                "TableName": self._table_name,
                "Key": {**state_key},
            })
        else:
            amz_target = "DynamoDB_20120810.PutItem"
            state_parsed = cast(str, state.state if isinstance(state, State) else state)
            request_parameters = json.dumps({
                "TableName": self._table_name,
                "Item": {
                    **state_key,
                    "state": {"S": state_parsed},
                },
            })

        await self._request_table(amz_target, request_parameters)

    async def get_state(self, key: StorageKey) -> Optional[str]:
        request_parameters = json.dumps({
            "TableName": self._table_name,
            "Key": {
                "chat_id": {"S": str(key.chat_id)},
                "user_id": {"S": str(key.user_id)},
            },
            "ConsistentRead": True,
        })
        amz_target = "DynamoDB_20120810.GetItem"

        response = await self._request_table(amz_target, request_parameters)
        response_body = json.loads(response)
        response_table = response_body.get("ConsumedCapacity", {"TableName": None}).get(
            "TableName"
        )

        if self._table_name != response_table:
            raise DetailedAiogramError(
                "A state table name does not match with response table name"
            )
        elif "Item" not in response_body:
            raise DetailedAiogramError(
                "Received an empty state data from the FSM storage"
            )

        response_item = response_body.get("Item", {"state": {"S": None}})

        return response_item.get("state").get("S")

    async def set_data(self, key: StorageKey, data: Dict[str, Any]) -> None:
        pass

    async def get_data(self, key: StorageKey) -> Dict[str, Any]:
        pass

    async def close(self) -> None:
        pass


state_storage = DynamoDBStorage(
    AWS_ACCESS_KEY, AWS_SECRET_KEY, AWS_FSM_TABLE_NAME, AWS_REGION
)
