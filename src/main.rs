use dto::*;
use lambda_http::{
    http::StatusCode, run, service_fn, Error as LambdaError, IntoResponse, Request, RequestExt,
};
use reqwest::Client;
use serde_json::json;
use std::{env, error::Error, fmt};

pub mod dto;

#[derive(Debug)]
enum BotError {
    EnvironmentError(String),
    ParsingError(String),
    NetworkError(String),
}

impl Error for BotError {}
impl fmt::Display for BotError {
    fn fmt(&self, fmt: &mut fmt::Formatter<'_>) -> fmt::Result {
        fmt.write_str(
            match self {
                BotError::EnvironmentError(msg) => format!(
                    "Environment error occured while executing function: '{}'.",
                    msg
                ),
                BotError::ParsingError(msg) => format!("Error while parsing structure: '{}'.", msg),
                BotError::NetworkError(msg) => {
                    format!("Error while sending a network message: '{}'.", msg)
                }
            }
            .as_str(),
        )
    }
}

async fn message_handler(event: &Request) -> Result<(), BotError> {
    let token = env::var("BOT_TOKEN").map_err(|_| {
        BotError::EnvironmentError(String::from(
            "Bot token is not set in environment variables",
        ))
    })?;
    let api_url = format!("https://api.telegram.org/bot{}/", token);

    let update: Update = event
        .payload::<Update>()
        .map_err(|_| {
            BotError::ParsingError(String::from(
                "Incorrect update message from the Telegram API",
            ))
        })?
        .ok_or(BotError::ParsingError(String::from(
            "Some update message fields are empty or have wrong format",
        )))?;
    let chat_id = update.message.chat.id;
    let text = update.message.text;

    let response_text = format!("You said: {}", text);
    let send_message_url = format!("{}sendMessage", api_url);

    let client = Client::new();
    let request_body = serde_json::json!({
        "chat_id": chat_id,
        "text": response_text,
        "parse_mode": "Optional",
        "disable_web_page_preview": false,
        "disable_notification": false
    });
    let res = client
        .post(&send_message_url)
        .json(&request_body)
        .send()
        .await
        .map_err(|_| {
            BotError::NetworkError(String::from("Failed to send a response to the user"))
        })?;

    if !res.status().is_success() {
        return Err(BotError::NetworkError(String::from(
            "Failed to send a response to the user",
        )));
    }

    Ok(())
}

pub async fn function_handler(event: Request) -> Result<impl IntoResponse, LambdaError> {
    let response: (StatusCode, String) = match message_handler(&event).await {
        Err(err) => (
            StatusCode::BAD_REQUEST,
            json!({ "message": err.to_string() }).to_string(),
        ),
        Ok(()) => (StatusCode::OK, String::new()),
    };

    Ok(response)
}

#[tokio::main]
async fn main() -> Result<(), LambdaError> {
    tracing_subscriber::fmt()
        .with_ansi(false)
        .without_time()
        .with_max_level(tracing_subscriber::filter::LevelFilter::INFO)
        .init();

    run(service_fn(function_handler)).await
}
