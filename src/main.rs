use client::{BotClient, ResponseMessage};
use dto::*;
use error::BotError;
use lambda_http::{
    http::StatusCode, run, service_fn, Error as LambdaError, IntoResponse, Request, RequestExt,
};
use log::info;
use serde_json::{json, Value};
use std::env;

pub mod client;
pub mod dto;
pub mod error;

async fn message_handler(event: &Request) -> Result<(), BotError> {
    let token = env::var("BOT_TOKEN").map_err(|_| {
        BotError::EnvironmentError(String::from(
            "Bot token is not set in environment variables",
        ))
    })?;

    let bot_client = BotClient::new(token);
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

    info!("Processing message from user: {}", chat_id);

    let response_msg = ResponseMessage {
        chat_id,
        text: format!("You said: {}.", text),
    };
    bot_client.send_message(&response_msg).await?;

    Ok(())
}

pub async fn function_handler(event: Request) -> Result<impl IntoResponse, LambdaError> {
    let response: (StatusCode, Value) = match message_handler(&event).await {
        Err(err) => (
            StatusCode::BAD_REQUEST,
            json!({ "message": err.to_string() }),
        ),
        Ok(()) => (
            StatusCode::OK,
            json!({ "message": "Response sent successfully." }),
        ),
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
