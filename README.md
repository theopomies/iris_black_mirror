# Messenger Chatbot with OpenAI GPT-3.5

This repository contains a Messenger chatbot built with Python and powered by OpenAI's GPT-3.5 model. The chatbot uses the Quart framework and the Requests library to communicate with the Messenger API.

The goal is to reproduce the relationship and phrasing of a real person, such as my girlfriend, inspired by Black Mirror's S2E1 Be Right Back.

It is currently hosted on Azure App Services.

## Dependencies

To use this Messenger chatbot, you'll need to have the following dependencies installed:

Python 3.9 or later
OpenAI API key with access to the GPT-3.5 model
Quart framework
Requests library

*Additionnaly you need a Facebook developer account and a Facebook app with access to the Messengers and Webhook services*

## Installation

Clone this repository: 

`git clone https://github.com/yourusername/yourrepository.git`

Install the dependencies:

`pip install -r requirements.txt`

Set up a Facebook Developer account and create a Messenger app.
Configure your Messenger app to use your chatbot's URL.

Run the chatbot:

`hypercorn app:app --bind 0.0.0.0:8000`

## Usage

To use the Messenger chatbot, simply start a conversation with your Facebook page and send a message. The chatbot will respond using OpenAI's GPT-3.5 model.

## Contributing

If you'd like to contribute to this project, feel free to submit a pull request. We welcome all contributions!

## License

This project is licensed under the GNU GENERAL PUBLIC LICENSE - see the LICENSE file for details.
