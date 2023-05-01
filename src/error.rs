use std::{error::Error, fmt};

#[derive(Debug)]
pub enum BotError {
    EnvironmentError(String),
    ParsingError(String),
    NetworkError(String),
    FsmError(String),
}

impl Error for BotError {}
impl fmt::Display for BotError {
    fn fmt(&self, fmt: &mut fmt::Formatter<'_>) -> fmt::Result {
        fmt.write_str(
            match self {
                BotError::EnvironmentError(msg) => {
                    format!("Environment error occured while executing function: '{msg}'.")
                }
                BotError::ParsingError(msg) => format!("Error while parsing structure: '{msg}'."),
                BotError::NetworkError(msg) => {
                    format!("Error while sending a network message: '{msg}'.")
                }
                BotError::FsmError(msg) => {
                    format!("Error while recording an application state: '{msg}'.")
                }
            }
            .as_str(),
        )
    }
}
