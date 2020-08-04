# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from decimal import *
import re
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
from webhook.models import redisCli

my_sender_id = settings.FB_ADMIN_ID
CURRENCIES = ['BTC', 'ETH', 'XRP']
trade_dict = {
    'BUY': 'Comprar',
    'SELL': 'Vender',
}
up_gif_url = 'https://media.giphy.com/media/BT33Hk6FMYHV6/giphy.gif'
down_gif_url = 'https://media.giphy.com/media/3ohs7HdhQA4ffttvrO/giphy.gif'

# TODO
# Optimizar send_price_updates para agregar facilmente mas monedas


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
    print "Received message for user {} and page {} at {} with message:".format(my_sender_id, recipient_id, time_of_message)
    # print repr(message)
    command = None

    if "quick_reply" in message:
        command = message['quick_reply']['payload']
    elif 'text' in message:
        command = message['text']
    message_attachments = message['attachments'] if 'attachments' in message else None
    step = redisCli.get_value_dict(my_sender_id, 'step')
    if command:
        if parseNumber(command) and step == "1":
            redisCli.append_to_dict(my_sender_id, "trade_amount", command)
            redisCli.append_to_dict(my_sender_id, "step", "2")
            trade_side = redisCli.get_value_dict(my_sender_id, 'trade_side')
            trade_currency = redisCli.get_value_dict(my_sender_id, 'trade_currency')

            api = bitso.Api()
            currency_price = api.ticker(trade_currency + '_mxn')

            bot.send(StructuredMessage(
                my_sender_id,
                StructuredMessage.TYPE_BUTTON,
                {
                    'text': "¿A que precio quieres " + trade_dict[trade_side.upper()] + " " + trade_currency.upper() + "?"+". El precio actual es de "+'{:,}'.format(currency_price.last)+" MXN",
                    'buttons': [
                        MessageButton(MessageButton.TYPE_POSTBACK, 'Fijar precio de ' + trade_currency.upper(), 'LIMIT'),
                        MessageButton(MessageButton.TYPE_POSTBACK, 'Precio de mercado', 'MARKET'),
                    ]
                }
            ))
        elif command.isdigit() and step == "3":
            redisCli.append_to_dict(my_sender_id, "trade_limit", command)
            trade_side = redisCli.get_value_dict(my_sender_id, 'trade_side')
            trade_amount = parseNumber(redisCli.get_value_dict(my_sender_id, 'trade_amount'))
            trade_currency = redisCli.get_value_dict(my_sender_id, 'trade_currency')
            trade_limit = parseNumber(redisCli.get_value_dict(my_sender_id, 'trade_limit'))
            cur_format = ""
            if trade_side == 'buy':
                cur_format = "${} MXN de ".format("{:,}".format(float(trade_amount)))
            elif trade_side == 'sell':
                cur_format = "{:,}".format(float(trade_amount))

            confirmation_msg = "Estas a punto de {} {} {} cuando tenga un valor de ${} MXN. ¿Estas seguro?".format(trade_dict[trade_side.upper()],cur_format,trade_currency.upper(),"{:,}".format(int(trade_limit)))
            bot.send(QuickReplay(
                my_sender_id,
                confirmation_msg,
                [ButtonReplay('✅ Si, seguro 😎', 'TRADE_CONFIRMATION'),
                 ButtonReplay('❌ Nooooo 😱', 'TRADE_CANCEL')]
            ))
            redisCli.append_to_dict(my_sender_id, "step", "4")
        elif command == 'TRADE_CONFIRMATION' and step == '4':
            if sender_id == my_sender_id:
                trade_process()
                redisCli.delete(my_sender_id)
        elif command == 'TRADE_CANCEL':
            redisCli.delete(my_sender_id)
            bot.send(SimpleMessage(my_sender_id, "Operación cancelada"))
        elif step == "10":
            api = bitso.Api(settings.BITSO_KEY, settings.BITSO_SECRET)
            if api.cancel_order(command):
                bot.send(SimpleMessage(my_sender_id, "Orden cancelada exitosamente"))
            else:
                bot.send(SimpleMessage(my_sender_id, "La orden ingresada no existe"))

            redisCli.append_to_dict(my_sender_id, "step", "0")
        else:
            #bot.send(SenderAction(my_sender_id, SenderAction.TYPING_ON))
            #bot.send(SimpleMessage(my_sender_id, "command"))
            print "success"

    elif message_attachments:
        bot.send(SimpleMessage(my_sender_id, "Message with attachment"))


def received_postback(request, event, sender_id):

    recipient_id = event['recipient']['id']
    time_of_message = event['timestamp']
    postback = event['postback']
    payload = postback['payload']
    print "Received postback for user {} and page {} at {} with payload: {}".format(my_sender_id, recipient_id, time_of_message, payload)
    if payload == 'GET_STARTED':
        send_price_updates()
    elif payload == 'SHOW_OPEN_ORDERS':
        show_open_orders()
    elif payload == 'CANCEL_ORDER':
        bot.send(SimpleMessage(my_sender_id,"Ingresa el ID de la orden que deseas cancelar"))
        redisCli.append_to_dict(my_sender_id, "step", "10")
    elif payload == 'TRADE':
        bot.send(StructuredMessage(
            my_sender_id,
            StructuredMessage.TYPE_BUTTON,
            {
                'text': "¿Qué quieres hacer?",
                'buttons': [
                    MessageButton(MessageButton.TYPE_POSTBACK, 'Comprar', 'BUY'),
                    MessageButton(MessageButton.TYPE_POSTBACK, 'Vender', 'SELL'),
                ]
            }
        ))
    elif payload in ['BUY', 'SELL']:
        redisCli.append_to_dict(my_sender_id, "trade_side", payload.lower())
        bot.send(StructuredMessage(
            my_sender_id,
            StructuredMessage.TYPE_BUTTON,
            {
                'text': "¿Qué moneda quieres " + trade_dict[payload] + "?",
                'buttons': [
                    MessageButton(MessageButton.TYPE_POSTBACK, 'Bitcoin', 'BTC'),
                    MessageButton(MessageButton.TYPE_POSTBACK, 'Ether', 'ETH'),
                    MessageButton(MessageButton.TYPE_POSTBACK, 'Ripple', 'XRP'),
                ]
            }
        ))
    elif payload in CURRENCIES:
        redisCli.append_to_dict(my_sender_id, "trade_currency", payload.lower())
        redisCli.append_to_dict(my_sender_id, "step", "1")
        trade_side = redisCli.get_value_dict(my_sender_id, 'trade_side')

        api = bitso.Api(settings.BITSO_KEY, settings.BITSO_SECRET)
        balances = api.balances()
        balance = None
        print trade_side
        cur = 'MXN'
        if trade_side == 'buy':
            balance = balances.mxn.available
        else:
            cur = payload
            if payload == 'BTC':
                balance = balances.btc.available
            elif payload == 'ETH':
                balance = balances.eth.available
            elif payload == 'XRP':
                balance = balances.xrp.available

        bot.send(SimpleMessage(my_sender_id, "¿Cuanto " + payload + " quieres " + trade_dict[trade_side.upper()] + "?"))
        bot.send(SimpleMessage(my_sender_id, "Ingresa el monto en " + cur + ", \nSaldo en " + cur + ": "))
        if balance:
            bot.send(SimpleMessage(my_sender_id, str(balance)))

    elif payload in ['LIMIT', 'MARKET']:
        redisCli.append_to_dict(my_sender_id, "trade_type", payload.lower())

        trade_currency = redisCli.get_value_dict(my_sender_id, 'trade_currency')
        trade_side = redisCli.get_value_dict(my_sender_id, 'trade_side')
        trade_amount = parseNumber(redisCli.get_value_dict(my_sender_id, 'trade_amount'))

        if payload == 'LIMIT':
            bot.send(SimpleMessage(my_sender_id, "Ingresa el precio en pesos que debe alcanzar el " + trade_currency.upper() + " para " + trade_dict[trade_side.upper()]))
            redisCli.append_to_dict(my_sender_id, "step", "3")
        elif payload == 'MARKET':
            cur_format = ""
            if trade_side == 'buy':
                cur_format = "${} MXN de ".format("{:,}".format(float(trade_amount)))
            elif trade_side == 'sell':
                cur_format = "{:,}".format(float(trade_amount))

            confirmation_msg = "Estas a punto de {} {} {} a precio de mercado. ¿Estas seguro?".format(trade_dict[trade_side.upper()], cur_format, trade_currency.upper())
            bot.send(QuickReplay(
                my_sender_id,
                confirmation_msg,
                [ButtonReplay('✅ Si, seguro 😎', 'TRADE_CONFIRMATION'),
                 ButtonReplay('❌ Nooooo 😱', 'TRADE_CANCEL')]
            ))
            redisCli.append_to_dict(my_sender_id, "step", "4")

    else:
        print "no action"


def send_price_updates():
    # #COINBASE
    # client = Client(settings.COINBASE_KEY, settings.COINBASE_SECRET, api_version='YYYY-MM-DD')
    # price_btc_usd = client.get_spot_price(currency_pair='BTC-USD')
    # price_eth_usd = client.get_spot_price(currency_pair='ETH-USD')

    # r = requests.get('https://coinmarketcap-nexuist.rhcloud.com/api/eth')
    # r = r.json()
    # ether_mxn = r['price']['mxn']
    # message = "Ether mxn: {}".format(ether_mxn)
    # BITSO
    api = bitso.Api()
    percent_treshold = 5.0

    for currency in CURRENCIES:
        # PRICE MXN
        currency_price = api.ticker(currency.lower() + '_mxn')

        # PRICE USD
        # r = requests.get('https://api.cryptonator.com/api/ticker/' + currency.lower() + '-usd')
        # r = r.json()
        #currency_price_usd = r['ticker']['price']

        last_currency_percent = percentage_change(currency_price.last, 'last_' + currency.lower())
        if last_currency_percent > percent_treshold:
            bot.send(SimpleMessage(my_sender_id, '{} {}'.format(currency, last_currency_percent)))
            bot.send(SimpleMessage(my_sender_id, up_gif_url, 'image'))
        elif last_currency_percent < (percent_treshold * -1):
            bot.send(SimpleMessage(my_sender_id, '{} {}'.format(currency, last_currency_percent)))
            bot.send(SimpleMessage(my_sender_id, down_gif_url, 'image'))
        redisCli.append_to_dict(my_sender_id, "saved_price_last_" + currency.lower(), currency_price.last)
        # currency_percent = percentage_change(currency_price.last, currency)
        #message = "1 {} = {} MXN | {} USD {}".format(currency, "{:,}".format(currency_price.last), "{:,.2f}".format(float(currency_price_usd)), percentage_rep(last_currency_percent))
        message = "1 {} = {} MXN {}".format(currency, "{:,}".format(currency_price.last), percentage_rep(last_currency_percent))
        bot.send(SimpleMessage(my_sender_id, message))

    # ether = api.ticker('eth_mxn')
    # bitcoin = api.ticker('btc_mxn')

    
    # last_eth_percent = percentage_change(ether.last, 'last_eth')
    # last_btc_percent = percentage_change(bitcoin.last, 'last_btc')
    

    # if last_eth_percent > percent_treshold:
    #     bot.send(SimpleMessage(my_sender_id, 'ETH {}'.format(last_eth_percent)))
    #     bot.send(SimpleMessage(my_sender_id, up_gif_url, 'image'))
    # elif last_eth_percent < (percent_treshold * -1):
    #     bot.send(SimpleMessage(my_sender_id, 'ETH {}'.format(last_eth_percent)))
    #     bot.send(SimpleMessage(my_sender_id, down_gif_url, 'image'))

    # if last_btc_percent > percent_treshold:
    #     bot.send(SimpleMessage(my_sender_id, 'BTC {}'.format(last_btc_percent)))
    #     bot.send(SimpleMessage(my_sender_id, up_gif_url, 'image'))
    # elif last_btc_percent < (percent_treshold * -1):
    #     bot.send(SimpleMessage(my_sender_id, 'BTC {}'.format(last_btc_percent)))
    #     bot.send(SimpleMessage(my_sender_id, down_gif_url, 'image'))

    # redisCli.append_to_dict(my_sender_id, "saved_price_eth", ether.last)
    # redisCli.append_to_dict(my_sender_id, "saved_price_btc", bitcoin.last)

    # ether_percent = percentage_change(ether.last, 'eth')
    # ether_percent_2 = percentage_change(ether.last, 'eth2')
    # ether_percent_3 = percentage_change(ether.last, 'eth3')
    # bitcoin_percent = percentage_change(bitcoin.last, 'btc')
    # message_btc = "1 BTC = {} MXN | {} USD {}".format("{:,}".format(bitcoin.last), price_btc_usd.amount, percentage_rep(bitcoin_percent))
    # message_eth = "1 ETH = {} MXN | {} USD {}".format("{:,}".format(ether.last), price_eth_usd.amount, percentage_rep(ether_percent))
    # message_eth2 = "25K => {} MXN {}".format("{:,f}".format(25000 * ((ether_percent_2 / 100) + 1)), percentage_rep(ether_percent_2))
    # message_eth3 = "25K => {} MXN {}".format("{:,f}".format(25000 * ((ether_percent_3 / 100) + 1)), percentage_rep(ether_percent_3))

    # bot.send(SimpleMessage(my_sender_id, message_btc))
    # #bot.send(SimpleMessage(my_sender_id, message_eth2))
    # #bot.send(SimpleMessage(my_sender_id, message_eth3))
    # bot.send(SimpleMessage(my_sender_id, message_eth))


def percentage_change(amount, currency):
    getcontext().prec = 3
    old_value = amount
    if currency == 'eth':
        old_value = Decimal(5117.17)
    elif currency == 'eth2':
        old_value = Decimal(8800.00)
    elif currency == 'eth3':
        old_value = Decimal(8330.00)
    elif currency == 'btc':
        old_value = Decimal(70000)
    else:
        val = redisCli.get_value_dict(my_sender_id, 'saved_price_' + currency)
        if val:
            int_val = parseNumber(val)
            old_value = Decimal(int_val)

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
    api = bitso.Api(settings.BITSO_KEY, settings.BITSO_SECRET)
    order_count = 0
    for currency in CURRENCIES:
        orders = api.open_orders(currency.lower() + '_mxn')
        for order in orders:
            order_count += 1
            message = "{} {} {}, por ${} MXN a ${} MXN por {}. OID:".format(trade_dict[order.side.upper()], order.original_amount, currency, "{:,}".format(order.original_value), "{:,}".format(order.price), currency)
            bot.send(SimpleMessage(my_sender_id, message))
            bot.send(SimpleMessage(my_sender_id,order.oid))

    if order_count == 0:
        bot.send(SimpleMessage(my_sender_id, "No hay ordenes abiertas"))


def trade_process():
    api = bitso.Api(settings.BITSO_KEY, settings.BITSO_SECRET)
    trade_side = redisCli.get_value_dict(my_sender_id, 'trade_side')
    trade_amount = parseNumber(redisCli.get_value_dict(my_sender_id, 'trade_amount'))
    trade_currency = redisCli.get_value_dict(my_sender_id, 'trade_currency')
    trade_type = redisCli.get_value_dict(my_sender_id, 'trade_type')
    order = None
    if trade_type == 'limit':
        trade_limit = parseNumber(redisCli.get_value_dict(my_sender_id, 'trade_limit'))
        if trade_side == 'buy':
            if trade_currency == 'xrp':
                major = "{0:.6f}".format(trade_amount / trade_limit)
            else:
                major = "{0:.8f}".format(trade_amount / trade_limit)

        elif trade_side == 'sell':
            major = str(trade_amount)
        try:
            order = api.place_order(book=trade_currency + '_mxn', side=trade_side, order_type=trade_type, major=major, price=str(trade_limit))
        except Exception as e:
            bot.send(SimpleMessage(my_sender_id, "⛔ " + e.args[0]['message']))

    elif trade_type == 'market':
        try:
            if trade_side == 'buy':
                order = api.place_order(book=trade_currency + '_mxn', side=trade_side, order_type=trade_type, minor=str(trade_amount))
            elif trade_side == 'sell':
                order = api.place_order(book=trade_currency + '_mxn', side=trade_side, order_type=trade_type, major=str(trade_amount))
        except Exception as e:
            bot.send(SimpleMessage(my_sender_id, "⛔ " + e.args[0]['message']))

    if order:
        if 'oid' in order:
            bot.send(SimpleMessage(my_sender_id, "¡Orden exitosa! OID: " + order['oid']))


def parseNumber(value, as_int=False):
    try:
        number = float(re.sub('[^.\-\d]', '', value))
        if as_int:
            return int(number)
        else:
            return number
    except ValueError:
        return None
    # r = requests.get('https://coinmarketcap-nexuist.rhcloud.com/api/eth')
    # r = r.json()
    # ether_mxn = r['price']['mxn']
    # message = "Ether mxn: {}".format(ether_mxn)
