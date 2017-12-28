# -*- coding: utf-8 -*-


cta_en_ = [
    {
        "type": "postback",
        "title": "Get Prices",
        "payload": "GET_STARTED"
    },
    {
        "type": "nested",
        "title": "Orders",
        "call_to_actions": [
            {
                "type": "postback",
                "title": "Show Open Orders",
                "payload": "SHOW_OPEN_ORDERS"
            },
            {
                "type": "postback",
                "title": "Cancel Order",
                "payload": "CANCEL_ORDER"
            }

        ]
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
