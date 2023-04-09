use client::{BotClient, BotMessage};
use dto::*;
use error::BotError;
use fsm::FSMClient;
use lambda_http::{
    http::StatusCode, run, service_fn, Error as LambdaError, IntoResponse, Request, RequestExt,
};
use log::info;
use serde_json::{json, Value};
use std::env;

pub mod client;
pub mod dto;
pub mod error;
pub mod fsm;

static START_MESSAGE: &str = "🌎 Hi there, I'm Nationguessr! With me, you get to test your knowledge about countries from all over the world by trying to guess them based on random facts about their history, culture, geography, and much more!

🔁 To play a quiz from the beginning use /restart command.
🔝 To see your highest score in quiz use /score command.
🆑 To clear all your high score history use /clear command.

Here is your first question:";

async fn message_handler(event: &Request) -> Result<(), BotError> {
    let token = env::var("BOT_TOKEN").map_err(|_| {
        BotError::EnvironmentError(String::from(
            "Bot token is not set in environment variables",
        ))
    })?;

    let fsm_table_name = env::var("FSM_TABLE_NAME").map_err(|_| {
        BotError::EnvironmentError(String::from(
            "FSM table name is not set in environment variables",
        ))
    })?;

    let bot_client = BotClient::new(token);
    let fsm_client = FSMClient::build(fsm_table_name).await;
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

    match fsm_client
        .get_state(chat_id)
        .await?
        .as_ref()
        .map(|s| s.as_str())
    {
        Some("playing") => {
            let test_message = BotMessage::new(
                chat_id,
                String::from("The quiz is over Your score is: *0*."),
            );
            fsm_client.reset(chat_id).await?;
            bot_client.send_message(&test_message).await
        }
        _ => {
            let bot_message = match text.as_str() {
                "/start" => BotMessage::new(chat_id, String::from(START_MESSAGE)),
                "/restart" => BotMessage::new(chat_id, String::from("Sure, let's try from the very beginning! Here is your first question:")),
                "/score" => BotMessage::new(chat_id, String::from("Your top score is: *0*.")),
                "/stop" => BotMessage::new(chat_id, String::from("Sure! Let's end our quiz here! Your score is: *0*.")),
                _ => BotMessage::new(chat_id, format!("Your command *{}* is not recognized! See the list of available commands in the *Menu* on the left.", text)),
            };
            fsm_client
                .set_state(chat_id, String::from("playing"))
                .await?;
            bot_client.send_message(&bot_message).await
        }
    }
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
