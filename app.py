from quart import Quart, request
from quart.utils import run_sync
import requests
import os
import openai
import threading
import json
import asyncio

from bot_secrets import (
    system_content,
    theo_system_details,
    iris_system_details,
    base_messages_theo,
    base_messages_iris,
    THEO,
    IRIS,
)

app = Quart(__name__)

openai.api_key = os.environ.get("OPENAI_API_KEY")
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN")

BOT_NAME = "Iris Black Mirror"


@app.route("/")
async def index():
    return "<p>This is a chatbot! Please use messenger to talk to Iris ;)</p>"


@app.route("/webhook", methods=["GET", "POST"])
async def webhook():
    if request.method == "GET":
        # Parse the query params
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        # Check if a token and mode is in the query string of the request
        if mode is not None and token is not None:
            # Check the mode and token sent is correct
            if mode == "subscribe":  # and token == config.verifyToken:
                # Respond with the challenge token from the request
                return challenge
            else:
                # Respond with '403 Forbidden' if verify tokens do not match
                return None, 403

        return challenge

    elif request.method == "POST":
        # Parse the incoming webhook event
        payload = await request.json

        # Process the event here (e.g. send a reply message)
        print("============== payload ================")
        print(payload)

        # handle_payload(payload) # this is blocking, so we need to use a thread

        thread = threading.Thread(target=handle_payload, args=[payload])
        thread.start()

        return "message received"


def handle_payload(payload):
    # Get the sender PSID
    sender_psid = payload["entry"][0]["messaging"][0]["sender"]["id"]
    message = payload["entry"][0]["messaging"][0]["message"]["text"]
    page_id = payload["entry"][0]["id"]

    print(f"±±±±±±±±±±±±±±± Message: {message} ±±±±±±±±±±±±±±±±")
    print("=============Getting previous messages ids============")
    previous_message_ids = get_user_conversation_message_ids(page_id, sender_psid)
    print("=============Got previous messages ids============")

    print("=============Getting previous messages============")
    # previous_messages = [get_message(id["id"]) for id in reversed(previous_message_ids)] # this is blocking, so we need to use a thread
    previous_messages = asyncio.run(
        get_previous_messages(reversed(previous_message_ids))
    )
    print("=============Got previous messages============")

    print("=============Preparing prompt============")
    messages = prepare_messages(previous_messages)
    print("=============Prompt ready============")
    print(messages)

    # Return a response to acknowledge receipt of the event
    print("=============Getting OpenAI response============")
    response = get_response(messages)
    print("=============Got OpenAI response============")
    print(response)
    # response = f'You sent "{message}"!'

    print("=============Sending response to Facebook============")
    url = f"https://graph.facebook.com/v14.0/{page_id}/messages?recipient={{id:{sender_psid}}}&message={{text:'{response}'}}&messaging_type=RESPONSE&access_token={PAGE_ACCESS_TOKEN}"
    fb_response = requests.post(
        url,
        params={"access_token": PAGE_ACCESS_TOKEN},
        data=json.dumps(
            {"recipient": {"id": sender_psid}, "message": {"text": response}}
        ),
        headers={"Content-type": "application/json"},
    ).json()
    print(url)
    print("=============Sent response to Facebook============")
    print(fb_response)
    print("=============Done============")


def get_user_conversation_message_ids(page_id, psid):
    # request the conversation id to facebook
    conversation_url = f"https://graph.facebook.com/v14.0/{page_id}/conversations?platform=messenger&user_id={psid}&access_token={PAGE_ACCESS_TOKEN}"
    response = requests.get(conversation_url).json()
    conversation_id = response["data"][0]["id"]

    # request the conversation history
    conversation_history_url = f"https://graph.facebook.com/v14.0/{conversation_id}?fields=messages&access_token={PAGE_ACCESS_TOKEN}"
    response = requests.get(conversation_history_url).json()
    message_ids = response["messages"]["data"]

    if not "next" in response["messages"]["paging"]:
        return message_ids[:50]

    next = response["messages"]["paging"]["next"]

    while len(message_ids) < 50:
        response = requests.get(next).json()
        message_ids += response["data"]
        if "next" not in response["paging"]:
            break
        next = response["paging"]["next"]
        response = requests.get(next).json()

    return message_ids[:50]


async def get_previous_messages(previous_message_ids):
    tasks = []
    for id in previous_message_ids:
        task = asyncio.create_task(get_message(id["id"]))
        tasks.append(task)
    previous_messages = await asyncio.gather(*tasks)
    return previous_messages


async def get_message(id):
    url = f"https://graph.facebook.com/v14.0/{id}?fields=id,message,from&access_token={PAGE_ACCESS_TOKEN}"

    def get_response():
        return requests.get(url).json()

    response = await run_sync(get_response)()
    return response


def prepare_messages(messages):
    base_prompt = get_base_prompt(messages)
    messages = list(map(prepare_message, messages))
    return [*base_prompt, *messages]


def get_base_prompt(messages):
    recipient = list(filter(lambda m: m["from"]["name"] != BOT_NAME, messages))[0][
        "from"
    ]["name"]

    print("=============Getting recipient============")
    print(recipient)
    print("=============Got recipient============")

    system_details = (
        theo_system_details
        if recipient == THEO
        else iris_system_details
        if recipient == IRIS
        else ""
    )
    system = {
        "role": "system",
        "content": system_content.format(system_details=system_details),
    }

    base_prompt_theo = [system, *base_messages_theo]
    base_prompt_iris = [system, *base_messages_iris]
    base_prompt_other = [system]

    if recipient == THEO:
        return base_prompt_theo
    elif recipient == IRIS:
        return base_prompt_iris
    return base_prompt_other


def prepare_message(message):
    if message["from"]["name"] == BOT_NAME:
        return {"role": "assistant", "content": message["message"]}
    return {"role": "user", "content": message["message"]}


def get_response(messages):
    response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)
    print("--------Tokens--------")
    print(response["usage"]["total_tokens"])
    print("--------Tokens--------")
    return response["choices"][0]["message"]["content"]
