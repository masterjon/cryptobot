# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from decimal import *
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
import bitso
from coinbase.wallet.client import Client

class UpdateMenu(APIView):

    def get(self, request):
        response = bot.set_menu(persistent_menu)
        return HttpResponse(response)


class WebhookCrypt(APIView):
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
        send_price_updates()
    elif payload == 'SHOW_OPEN_ORDERS':
        show_open_orders()
    else:
        print "no action"


def send_price_updates():
    #COINBASE
    client = Client('WJrZZsSpBThLAmQh','dk8eB5PwAdGzc3zhT6xLUxtOTK22B8au', api_version='YYYY-MM-DD')
    price_btc_usd = client.get_spot_price(currency_pair='BTC-USD')
    price_eth_usd = client.get_spot_price(currency_pair='ETH-USD')

    #BITSO
    api = bitso.Api()
    # api = bitso.Api(settings.BITSO_KEY, settings.BITSO_SECRET)
    ether = api.ticker('eth_mxn')
    bitcoin = api.ticker('btc_mxn')
    ether_percent = percentage_change(ether.last, 'eth')
    ether_percent_2 = percentage_change(ether.last, 'eth2')
    ether_percent_3 = percentage_change(ether.last, 'eth3')
    bitcoin_percent = percentage_change(bitcoin.last, 'btc')
    message_btc = "1 BTC = {} MXN | {} USD {}".format("{:,}".format(bitcoin.last), price_btc_usd.amount, percentage_rep(bitcoin_percent))
    message_eth = "1 ETH = {} MXN | {} USD {}".format("{:,}".format(ether.last), price_eth_usd.amount, percentage_rep(ether_percent))
    message_eth2 = "25K => {} MXN {}".format("{:,f}".format(25000 * ((ether_percent_2 / 100) + 1)), percentage_rep(ether_percent_2))
    message_eth3 = "25K => {} MXN {}".format("{:,f}".format(25000 * ((ether_percent_3 / 100) + 1)), percentage_rep(ether_percent_3))

    bot.send(SimpleMessage(settings.FB_ADMIN_ID, message_btc))
    #bot.send(SimpleMessage(settings.FB_ADMIN_ID, message_eth2))
    #bot.send(SimpleMessage(settings.FB_ADMIN_ID, message_eth3))
    bot.send(SimpleMessage(settings.FB_ADMIN_ID, message_eth))


def percentage_change(amount, currency):
    getcontext().prec = 3
    old_value = 0
    if currency == 'eth':
        old_value = Decimal(5117.17)
    if currency == 'eth2':
        old_value = Decimal(8800.00)
    if currency == 'eth3':
        old_value = Decimal(8330.00)
    elif currency == 'btc':
        old_value = Decimal(70000)

    return ((amount / old_value) - 1) * 100


def percentage_rep(p):
    if p < 0:
        return "🔴 {}% ⇩".format(p)

    return "🔵 {}% ⇧".format(p)


def buy_sell(amount, operation):
    if operation in ['buy', 'sell']:
        xrp = api.ticker('xrp_mxn').last
        order = api.place_order(book='xrp_mxn', side=operation, order_type='limit', major=amount, price=xrp)
        print order
    else:
        print "Please provide a valid operation"


def show_open_orders():
    print "ooooooo-"
    api = bitso.Api("osPvNyiYwc", "d7109d5566e3c7ca8cbf4b92cd438eed")
    oobtc = api.open_orders('btc_mxn')
    ooeth = api.open_orders('eth_mxn')
    oo = oobtc + ooeth

    for o in oobtc:
        message = "{} BTC, por {} MXN a {} MXN por BTC".format(o.original_amount, "{:,}".format(o.original_value), "{:,}".format(o.price))
        bot.send(SimpleMessage(settings.FB_ADMIN_ID, message))

    for o in ooeth:
        message = "{} ETH, por {} MXN a {} MXN por ETH".format(o.original_amount, "{:,}".format(o.original_value), "{:,}".format(o.price))
        bot.send(SimpleMessage(settings.FB_ADMIN_ID, message))

    if len(oo) == 0:
        bot.send(SimpleMessage(settings.FB_ADMIN_ID, "No hay ordenes abiertas"))


    # r = requests.get('https://coinmarketcap-nexuist.rhcloud.com/api/eth')
    # r = r.json()
    # ether_mxn = r['price']['mxn']
    # message = "Ether mxn: {}".format(ether_mxn)
