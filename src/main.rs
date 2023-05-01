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

    let current_state = fsm_client.get_state(chat_id).await?;

    match text.as_str() {
        "/start" => {
            let bot_message = BotMessage::new(chat_id, String::from(START_MESSAGE));
            fsm_client
                .set_state(chat_id, String::from("playing"))
                .await?;
            bot_client.send_message(&bot_message).await
        }
        "/restart" => {
            let bot_message =
                BotMessage::new(chat_id, String::from("TODO: implement restart command."));
            bot_client.send_message(&bot_message).await
        }
        "/score" => {
            let bot_message =
                BotMessage::new(chat_id, String::from("TODO: implement score command."));
            bot_client.send_message(&bot_message).await
        }
        "/clear" => {
            let bot_message = BotMessage::new(
                chat_id,
                String::from(
                    "Now your high score board is empty. Use /start command to play a new game!",
                ),
            );
            fsm_client.reset(chat_id).await?;
            bot_client.send_message(&bot_message).await
        }
        _ => match current_state.as_deref() {
            Some("playing") => {
                let bot_message = BotMessage::new(chat_id, String::from("TODO: implement quiz."));
                bot_client.send_message(&bot_message).await
            }
            _ => {
                let bot_message = BotMessage::new(chat_id, format!("Your command *{text}* is not recognized! See the list of available commands in the *Menu* section."));
                bot_client.send_message(&bot_message).await
            }
        },
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
