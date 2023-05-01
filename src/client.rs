use crate::error::BotError;
use reqwest::Client;
use serde_json::Value;

pub enum ParseMode {
    Markdown,
    HTML,
}

pub struct BotClient {
    client: Client,
    send_message_url: String,
}

pub struct BotMessage {
    chat_id: i64,
    text: String,
    parse_mode: ParseMode,
    disable_web_page_preview: bool,
    disable_notification: bool,
    reply_to_message_id: Option<i64>,
}

impl BotMessage {
    pub fn new(chat_id: i64, text: String) -> BotMessage {
        Self {
            chat_id,
            text,
            parse_mode: ParseMode::Markdown,
            disable_web_page_preview: false,
            disable_notification: false,
            reply_to_message_id: None,
        }
    }

    pub fn disable_web_page_preview(&mut self) {
        self.disable_web_page_preview = true;
    }

    pub fn disable_notification(&mut self) {
        self.disable_notification = true;
    }

    pub fn set_parse_mode(&mut self, parse_mode: ParseMode) {
        self.parse_mode = parse_mode;
    }

    pub fn set_reply_to_message(&mut self, id: i64) {
        self.reply_to_message_id = Some(id);
    }
}

impl BotClient {
    pub fn new(token: String) -> BotClient {
        Self {
            client: Client::new(),
            send_message_url: format!("https://api.telegram.org/bot{token}/sendMessage"),
        }
    }

    pub async fn send_message(&self, message: &BotMessage) -> Result<(), BotError> {
        let reply_to_message_id_val = match message.reply_to_message_id {
            Some(id) => Value::Number(id.into()),
            None => Value::Null,
        };
        let parse_mode_val = match message.parse_mode {
            ParseMode::Markdown => Value::String(String::from("Markdown")),
            ParseMode::HTML => Value::String(String::from("HTML")),
        };
        let request_body = serde_json::json!({
            "chat_id": message.chat_id,
            "text": message.text,
            "parse_mode": parse_mode_val,
            "disable_web_page_preview": message.disable_web_page_preview,
            "disable_notification": message.disable_notification,
            "reply_to_message_id": reply_to_message_id_val,
        });

        let request = self.client.post(&self.send_message_url).json(&request_body);
        let response = request.send().await.map_err(|_| {
            BotError::NetworkError(String::from("Failed to send a response to the user"))
        })?;
        if !response.status().is_success() {
            return Err(BotError::NetworkError(String::from(
                "Failed to send a response to the user",
            )));
        }

        Ok(())
    }
}
