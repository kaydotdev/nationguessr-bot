import json
import os
import sys
from urllib.parse import urlencode

import click
import requests


@click.command(
    "webhook",
    help="A CLI application for managing the Telegram API webhook of the @nationguessr_bot.",
)
@click.version_option("1.0.0", prog_name="webhook")
@click.argument(
    "action", type=click.Choice(["GET", "SET", "DELETE"], case_sensitive=True)
)
@click.option(
    "-t",
    "--token",
    type=click.STRING,
    help="Obtained authentication token from @BotFather. If not set as an option, the CLI gets the value from the "
    "environment variable `VAR_TOKEN`.",
)
@click.option(
    "-u",
    "--url",
    type=click.STRING,
    help="HTTPS URL to send updates to. Required only for the 'SET' command. If not set as an option, the CLI gets "
    "the value from the environment variable `VAR_WEBHOOK_URL`.",
)
def cli(action: str, token: str, url: str) -> None:
    api_url_templates = {
        "GET": "https://api.telegram.org/bot{token}/getWebhookInfo",
        "SET": "https://api.telegram.org/bot{token}/setWebhook",
        "DELETE": "https://api.telegram.org/bot{token}/deleteWebhook",
    }

    token = token or os.getenv("VAR_TOKEN")
    url = url or os.getenv("VAR_WEBHOOK_URL")

    if token is None:
        click.echo(
            "❌ Bot authentication token is not provided. Specify it in the command arguments "
            f"{click.style('python webhook.py --token TOKEN', bold=True, italic=True)} or set "
            f"it as {click.style('VAR_TOKEN', bold=True, italic=True)} environment variable.",
            err=True,
        )
        sys.exit(1)

    api_url = api_url_templates[action].format(token=token)

    if action == "SET":
        if url is None:
            click.echo(
                "❌ Webhook callback URL is not provided. Specify it in the command arguments "
                f"{click.style('python webhook.py --url URL', bold=True, italic=True)} or set "
                f"it as {click.style('VAR_WEBHOOK_URL', bold=True, italic=True)} environment variable.",
                err=True,
            )
            sys.exit(1)

        api_url = (
            api_url
            + "?"
            + urlencode({"url": url, "drop_pending_updates": True}, doseq=True)
        )

    response = requests.post(api_url)

    if response.status_code != 200:
        response_err_msg = {
            400: "❌ The provided webhook URL is invalid. Ensure the link is correct and includes the `https://` "
            "protocol prefix.",
            401: "❌ The bot authentication token is invalid. Ensure the token is correct or revoke it from @BotFather.",
            403: "❌ Attempted to manage a webhook for a bot that is blacklisted.",
            420: "❌ Too many requests. A wait of a few seconds is required.",
            500: "❌ Something went wrong. Try again later.",
        }

        click.echo(response_err_msg.get(response.status_code), err=True)
        sys.exit(1)

    response_result = json.loads(response.text).get("result", {})

    match action:
        case "GET":
            for name, val in response_result.items():
                click.echo(
                    f"{click.style(name.replace('_', ' ').capitalize(), bold=True):30}  {click.style(val, fg='green')}"
                )
        case "SET":
            click.echo(f"✅ New webhook is set at {click.style(url, bold=True)}.")
        case "DELETE":
            click.echo("✅ Webhook is deleted.")


if __name__ == "__main__":
    cli()
