class SenderAction(object):
    TYPING_ON = 'typing_on'
    TYPING_OFF = 'typing_off'

    def __init__(self, recipient, sender_action):
        self.recipient = recipient
        self.sender_action = sender_action

    def getdata(self):
        return {
            "recipient": {
                "id": self.recipient
            },
            "sender_action": self.sender_action
        }
