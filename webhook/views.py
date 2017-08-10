# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import requests
from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from fb_messenger import bot
from fb_messenger.SenderAction import SenderAction
from fb_messenger.SimpleMessage import SimpleMessage
from fb_messenger.StructuredMessage import StructuredMessage
from fb_messenger.MessageButton import MessageButton
from fb_messenger.MessageElement import MessageElement
from fb_messenger.QuickReplay import QuickReplay, ButtonReplay
from fb_messenger.MessageReceipt import MessageReceiptElement, Address, Summary, Adjustment
from fb_messenger.PersistentMenu import persistent_menu


class UpdateMenu(APIView):

    def get(self, request):
        response = bot.set_menu(persistent_menu)
        return HttpResponse(response)


class Webhook(APIView):
    def get(self, request):
        hub_mode = request.GET.get('hub.mode', '')
        hub_verify_token = request.GET.get('hub.verify_token', '')
        if hub_mode == 'subscribe' and hub_verify_token == settings.FB_VERIFICATION_TOKEN:
            hub_challenge = request.GET.get('hub.challenge')
            print "Webook validation"
            return Response(int(hub_challenge), status=status.HTTP_200_OK)
        return Response(status=status.HTTP_403_FORBIDDEN)

    def post(self, request):

        data = request.data
        obj = data.get('object', '')
        if obj == 'page':
            entry = data.get('entry', [])
            for item in entry:
                for event in item['messaging']:
                    sender_id = event['sender']['id']
                    if 'message' in event:
                        received_message(request, event, sender_id)
                    elif 'postback' in event:
                        received_postback(request, event, sender_id)
        return Response(status=status.HTTP_200_OK)


def received_message(request, event, sender_id):
    recipient_id = event['recipient']['id']
    time_of_message = event['timestamp']
    message = event['message']
    print "Received message for user {} and page {} at {} with message:".format(sender_id, recipient_id, time_of_message)
    # print repr(message)
    command = None

    if "quick_reply" in message:
        command = message['quick_reply']['payload']
    elif 'text' in message:
        command = message['text']
    message_attachments = message['attachments'] if 'attachments' in message else None

    if command:
        if command == 'BUY_ETHER':
            bot.send(SimpleMessage(sender_id, "ok"))
        else:
            #bot.send(SenderAction(sender_id, SenderAction.TYPING_ON))
            #bot.send(SimpleMessage(sender_id, "command"))
            print "success"

    elif message_attachments:
        bot.send(SimpleMessage(sender_id, "Message with attachment"))


def received_postback(request, event, sender_id):
    sender_id = event['sender']['id']
    recipient_id = event['recipient']['id']
    time_of_message = event['timestamp']
    postback = event['postback']
    payload = postback['payload']
    print "Received postback for user {} and page {} at {} with payload: {}".format(sender_id, recipient_id, time_of_message, payload)
    if payload == 'GET_STARTED':
        bot.send(SimpleMessage(sender_id, "ok"))
        send_price_updates()
    else:
        print "no action"


def send_price_updates():
    import bitso
    api = bitso.Api()
    
    r = requests.get('https://coinmarketcap-nexuist.rhcloud.com/api/eth')
    r = r.json()
    ether_mxn = r['price']['mxn']
    message = "Ether mxn: {}".format(ether_mxn)
    bot.send(SimpleMessage(settings.FB_ADMIN_ID, message))
