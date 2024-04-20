import json
import os
import random
import string
import sys
from typing import Any, Dict
from urllib.parse import urlencode

import click
import requests
from requests.exceptions import HTTPError


def send_request(url: str, params: Dict[str, Any] | None = None) -> Dict[str, Any]:
    api_url = url + "?" + urlencode(params, doseq=True) if params is not None else url
    response = requests.post(api_url)
    response.raise_for_status()

    return json.loads(response.text)


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
@click.option(
    "-s",
    "--secret",
    is_flag=True,
    type=click.BOOL,
    help="Generate a random secret token for 'X-Telegram-Bot-Api-Secret-Token' and set it in webhook query parameters. "
    "Used to protect webhook API endpoint from unauthorized external requests. After a successful webhook set "
    "prints token to a standard output. Required only for the 'SET' command.",
)
def cli(action: str, token: str, url: str, secret: bool) -> None:
    token = token or os.getenv("VAR_TOKEN")
    url = url or os.getenv("VAR_WEBHOOK_URL")

    if token is None:
        click.echo(
            f"❌ Bot authentication token is not provided. Specify it in the command arguments "
            f"{click.style('python webhook.py --token TOKEN', bold=True, italic=True)} or set "
            f"it as {click.style('VAR_TOKEN', bold=True, italic=True)} environment variable.",
            err=True,
        )
        sys.exit(1)

    try:
        match action:
            case "GET":
                result = send_request(
                    f"https://api.telegram.org/bot{token}/getWebhookInfo"
                )

                for name, val in result.get("result", {}).items():
                    click.echo(
                        f"{click.style(name.replace('_', ' ').capitalize(), bold=True):30}  "
                        f"{click.style(val, fg='green')}"
                    )
            case "SET":
                if url is None:
                    click.echo(
                        "❌ Webhook callback URL is not provided. Specify it in the command arguments "
                        f"{click.style('python webhook.py --url URL', bold=True, italic=True)} or set "
                        f"it as {click.style('VAR_WEBHOOK_URL', bold=True, italic=True)} environment variable.",
                        err=True,
                    )
                    sys.exit(1)

                secret_token = ""
                params = {"url": url, "drop_pending_updates": True}

                if secret:
                    secret_token = "".join(
                        random.choices(string.ascii_letters + string.digits, k=256)
                    )
                    params["secret_token"] = secret_token

                result = send_request(
                    f"https://api.telegram.org/bot{token}/setWebhook", params
                )

                if secret:
                    click.echo(click.style(secret_token, bold=True))
                else:
                    click.echo(f"✅ {result.get('description')}")
            case "DELETE":
                result = send_request(
                    f"https://api.telegram.org/bot{token}/deleteWebhook"
                )
                click.echo(f"✅ {result.get('description')}")
    except HTTPError as e:
        err_description = json.loads(e.response.text).get("description")
        click.echo(
            f"❌ Received an error response from Telegram API: "
            f"{click.style(err_description, bold=True)}",
            err=True,
        )
    except Exception as e:
        click.echo(f"Caught an unexpected error: {e}", err=True)


if __name__ == "__main__":
    cli()
