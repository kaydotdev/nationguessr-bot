use serde::{Deserialize, Serialize};

#[derive(Deserialize)]
pub struct LambdaEvent {
    pub message: String,
}

#[derive(Serialize)]
pub struct Response {
    pub response: String,
}

#[derive(Serialize)]
pub struct ResponseMessage {
    pub chat_id: i64,
    pub text: String,
}

#[derive(Deserialize)]
pub struct Update {
    pub update_id: i64,
    pub message: Message,
}

#[derive(Deserialize)]
pub struct Message {
    pub message_id: i64,
    pub text: String,
    pub chat: Chat,
}

#[derive(Deserialize)]
pub struct Chat {
    pub id: i64,
}
