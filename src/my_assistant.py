#!/usr/bin/env python3
# Copyright 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Run a recognizer using the Google Assistant Library.

The Google Assistant Library has direct access to the audio API, so this Python
code doesn't need to record audio. Hot word detection "OK, Google" is supported.

The Google Assistant Library can be installed with:
    env/bin/pip install google-assistant-library==0.0.2

It is available for Raspberry Pi 2/3 only; Pi Zero is not supported.
"""

import logging
import pprint
import random
import subprocess
import sys
import re
import aiy.assistant.auth_helpers
import aiy.audio
import aiy.voicehat
from google.assistant.library import Assistant
from google.assistant.library.event import EventType
import swearing

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
)


def power_off_pi(*args):
    aiy.audio.say('Good bye!')
    subprocess.call('sudo shutdown now', shell=True)


def reboot_pi(*args):
    aiy.audio.say('See you in a bit!')
    subprocess.call('sudo reboot', shell=True)


def say_ip(*args):
    ip_address = subprocess.check_output("hostname -I | cut -d' ' -f1", shell=True)
    aiy.audio.say('My IP address is %s' % ip_address.decode('utf-8'))


def update(*args):
    subprocess.call('cd /home/pi/AIY-voice-kit-python/src ; git pull --rebase : sudo reboot', shell=True)


def do_a_swear(*args):
    swear = random.choice(swearing.swears)
    aiy.audio.say(swear)


def ping(*args):
    match = args[0]
    hostname = match.group("hostname")
    if hostname:
        inputy = "ping {}".format(hostname)
        print(inputy)
        aiy.audio.say(inputy)
        outputy = subprocess.check_output(inputy, shell=True).decode('utf-8')
        print(outputy)
        aiy.audio.say(outputy)


class Command(object):
    def __init__(self, regex, func):
        self._regex = re.compile(regex, re.IGNORECASE)
        self._func = func

    def is_match(self, text, assistant):
        match = self._regex.match(text)
        if match:
            assistant.stop_conversation()
            self._func(match)


commands = [
    Command("power off", power_off_pi),
    Command("reboot", reboot_pi),
    Command("ip address", say_ip),
    Command("update", update),
    Command("swear", do_a_swear),
    Command("ping (?P<hostname>[\w]+", ping)
]


def command_match(text, assistant):
    for command in commands:
        command.is_match(text, assistant)


def process_event(assistant, event):
    status_ui = aiy.voicehat.get_status_ui()
    if event.type == EventType.ON_START_FINISHED:
        status_ui.status('ready')
        if sys.stdout.isatty():
            print('Say "OK, Google" then speak, or press Ctrl+C to quit...')

    elif event.type == EventType.ON_CONVERSATION_TURN_STARTED:
        status_ui.status('listening')

    elif event.type == EventType.ON_RECOGNIZING_SPEECH_FINISHED and event.args:
        pprint.pprint(event.args)
        text = event.args['text'].lower()
        print(text)
        command_match(text, assistant)

    elif event.type == EventType.ON_END_OF_UTTERANCE:
        status_ui.status('thinking')

    elif event.type == EventType.ON_CONVERSATION_TURN_FINISHED:
        status_ui.status('ready')

    elif event.type == EventType.ON_ASSISTANT_ERROR and event.args and event.args['is_fatal']:
        sys.exit(1)


def main():
    credentials = aiy.assistant.auth_helpers.get_assistant_credentials()
    with Assistant(credentials) as assistant:
        for event in assistant.start():
            process_event(assistant, event)


if __name__ == '__main__':
    main()