# -*- coding: utf-8 -*-


cta_en_ = [
    {
        "type": "postback",
        "title": "Ether Price",
        "payload": "GET_STARTED"
    },
    {
        "type": "postback",
        "title": "Open Orders",
        "payload": "SHOW_OPEN_ORDERS"
    }

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
