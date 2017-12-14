# -*- coding: utf-8 -*-


cta_en_ = [
    {
        "type": "postback",
        "title": "Get Prices",
        "payload": "GET_STARTED"
    },
    {
        "type": "postback",
        "title": "Open Orders",
        "payload": "SHOW_OPEN_ORDERS"
    },
    {
        "type": "postback",
        "title": "Trade",
        "payload": "TRADE"
    },

]

persistent_menu = {
    "persistent_menu": [
        {
            "locale": "default",
            "composer_input_disabled": False,
            "call_to_actions": cta_en_
        }
    ]
}
