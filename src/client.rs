use crate::dto::ResponseMessage;
use crate::error::BotError;
use reqwest::Client;

pub struct BotClient {
    client: Client,
    send_message_url: String,
}

impl BotClient {
    pub fn new(token: String) -> BotClient {
        Self {
            client: Client::new(),
            send_message_url: format!("https://api.telegram.org/bot{}/sendMessage", token),
        }
    }

    pub async fn send_message(&self, message: ResponseMessage) -> Result<(), BotError> {
        let request_body = serde_json::json!({
            "chat_id": message.chat_id,
            "text": message.text,
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
