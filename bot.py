from cryptography.fernet import Fernet
import traceback
import requests
import logging
import telebot
import time
import re
import os

from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import subprocess

from utils import getToken, getNgrokIP

def createEmptyBot():
    TOKEN = getToken()
    bot = telebot.TeleBot(token=TOKEN)
    bot.checkAuth = False
    bot.isAuthorized = False
    bot.awaitingInput = False

    # @bot.message_handler(func=lambda message: True)
    # def _start(message):
    #     return

    buttons = ['led-on', 'led-off', 'ssh-url', 'execute']
    markup = ReplyKeyboardMarkup(row_width=len(buttons))
    markup.add(*[KeyboardButton(button) for button in buttons])

    def messageFilter(message):
        return message.text in buttons

    @bot.message_handler(commands=["start"])
    def _start(message):
        bot.send_message(message.chat.id, f'Choose command: ', reply_markup=markup)
        bot.awaitingInput = True
        return
        
    # @bot.message_handler(func=lambda message: message in buttons)
    @bot.message_handler(func=lambda message: bot.awaitingInput and messageFilter(message) and not bot.checkAuth and not bot.isAuthorized)
    def _keyboardCommand(message):
        bot.awaitingInput = False
        if message.text in ['led-on', 'led-off']:
            ledCommand(message)
        elif message.text == 'ssh-url':
            getNgrokUrl(message)
        elif message.text == 'execute':
            bot.send_message(message.chat.id, f'Enter password: ')
            bot.checkAuth = True
        else:
            bot.send_message(message.chat.id, f'Command-{message.txt} is not configured')
        return

    @bot.message_handler(func=lambda message: bot.checkAuth)
    def _authenticate(message):
        bot.checkAuth = False
        bot.delete_message(message.chat.id, message.id)
        if message.text == os.getenv('PASSWORD'):
            bot.isAuthorized = True
            bot.send_message(message.chat.id, 'User is authenticated, please type command in next message')
        else:
            bot.isAuthorized = False
            bot.send_message(message.chat.id, f'User is not authenticated')
        return

    @bot.message_handler(func=lambda message: bot.isAuthorized)
    def _execCommand(message):
        bot.isAuthorized = False
        cmd = f'./run {message.text}'
        proc = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        stdout, stderr = [i.decode().strip() if i else None for i in proc.communicate()]
        bot.send_message(message.chat.id, f'Output:\n{stdout}')
        return
    
    def authUser(message):
        if message.text == os.getenv('PASSWORD'):
            bot.isAuthorized = True
        else:
            bot.isAuthorized = False

    def getNgrokUrl(message):
        url = f'http://{getNgrokIP()}/api/tunnels'
        response = requests.get(url, timeout=30).json()
        public_url = ''
        for tunnel in response['tunnels']:
            if tunnel['name'] == 'ssh':
                public_url = tunnel['public_url'].split('/')[-1]
        if public_url:
            bot.send_message(message.chat.id, f'SSH URL @ {public_url}')
        else:
            bot.send_message(message.chat.id, f'SSH tunnel not configured')

    def ledCommand(message):
        # print(message, message in buttons)
        cmd = 'cat /sys/class/leds/ACT/brightness'
        proc = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        std_out, std_err = proc.communicate()
        status = 'led-on' if int(std_out.decode().strip()) else 'led-off'
        if status != message.text:
            cmd = f'./run {message.text}'
            proc = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            std_out, std_err = proc.communicate()
            message.text += ' (' + std_out.decode().strip() + ')'
        else:
            message.text += ' (no change)'
        # bot.send_message(message.chat.id, f'Current status: {message.text}', reply_markup=ReplyKeyboardRemove())
        bot.send_message(message.chat.id, f'Current status: {message.text}')
        return

    return bot

# {'content_type': 'text', 'id': 10038, 'message_id': 10038, 'from_user': {'id': 6122662956, 'is_bot': False, 'first_name': 'Jun Jie', 'username': None, 'last_name': None, 'language_code': 'en', 'can_join_groups': None, 'can_read_all_group_messages': None, 'supports_inline_queries': None}, 'date': 1692904010, 'chat': {'id': 6122662956, 'type': 'private', 'title': None, 'username': None, 'first_name': 'Jun Jie', 'last_name': None, 'photo': None, 'bio': None, 'has_private_forwards': None, 'description': None, 'invite_link': None, 'pinned_message': None, 'permissions': None, 'slow_mode_delay': None, 'message_auto_delete_time': None, 'has_protected_content': None, 'sticker_set_name': None, 'can_set_sticker_set': None, 'linked_chat_id': None, 'location': None}, 'sender_chat': None, 'forward_from': None, 'forward_from_chat': None, 'forward_from_message_id': None, 'forward_signature': None, 'forward_sender_name': None, 'forward_date': None, 'is_automatic_forward': None, 'reply_to_message': None, 'via_bot': None, 'edit_date': None, 'has_protected_content': None, 'media_group_id': None, 'author_signature': None, 'text': 'led-on', 'entities': None, 'caption_entities': None, 'audio': None, 'document': None, 'photo': None, 'sticker': None, 'video': None, 'video_note': None, 'voice': None, 'caption': None, 'contact': None, 'location': None, 'venue': None, 'animation': None, 'dice': None, 'new_chat_member': None, 'new_chat_members': None, 'left_chat_member': None, 'new_chat_title': None, 'new_chat_photo': None, 'delete_chat_photo': None, 'group_chat_created': None, 'supergroup_chat_created': None, 'channel_chat_created': None, 'migrate_to_chat_id': None, 'migrate_from_chat_id': None, 'pinned_message': None, 'invoice': None, 'successful_payment': None, 'connected_website': None, 'reply_markup': None, 'json': {'message_id': 10038, 'from': {'id': 6122662956, 'is_bot': False, 'first_name': 'Jun Jie', 'language_code': 'en'}, 'chat': {'id': 6122662956, 'first_name': 'Jun Jie', 'type': 'private'}, 'date': 1692904010, 'text': 'led-on'}} False