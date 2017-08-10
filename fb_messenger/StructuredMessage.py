
class StructuredMessage(object):
    TYPE_BUTTON = "button"
    TYPE_GENERIC = "generic"
    TYPE_RECEIPT = "receipt"

    def __init__(self, recipient, type, data):
        self.recipient = recipient
        self.type = type
        if self.type == self.TYPE_BUTTON:
            self.title = data['text']
            self.buttons = data['buttons']

        elif self.type == self.TYPE_GENERIC:
            self.elements = data['elements']

        elif self.type == self.TYPE_RECEIPT:
            self.recipient_name = data['recipient_name']
            self.order_number = data['order_number']
            self.currency = data['currency']
            self.payment_method = data['payment_method']
            self.timestamp = data['timestamp']
            self.elements = data['elements']
            if 'address' in data:
                self.address = data['address']
            if 'order_url' in data:
                self.order_url = data['order_url']
            self.summary = data['summary']
            self.adjustments = data['adjustments']

    def getdata(self):
        result = {
            'attachment': {
                'type': 'template',
                'payload': {
                    'template_type': self.type
                }
            }
        }

        if self.type == self.TYPE_BUTTON:
            result['attachment']['payload']['text'] = self.title
            result['attachment']['payload']['buttons'] = []
            for btn in self.buttons:
                result['attachment']['payload']['buttons'].append(btn.getdata())

        elif self.type == self.TYPE_GENERIC:
            result['attachment']['payload']['elements'] = []
            for btn in self.elements:
                result['attachment']['payload']['elements'].append(btn.getdata())

        elif self.type == self.TYPE_RECEIPT:
            result['attachment']['payload']['recipient_name'] = self.recipient_name
            result['attachment']['payload']['order_number'] = self.order_number
            result['attachment']['payload']['currency'] = self.currency
            result['attachment']['payload']['payment_method'] = self.payment_method
            result['attachment']['payload']['timestamp'] = self.timestamp
            result['attachment']['payload']['elements'] = []
            for btn in self.elements:
                result['attachment']['payload'][
                    'elements'].append(btn.getdata())
            if hasattr(self, 'address'):
                result['attachment']['payload']['address'] = self.address.getdata()
            if hasattr(self, 'order_url'):
                result['attachment']['payload']['order_url'] = self.order_url
            result['attachment']['payload']['summary'] = self.summary.getdata()
            result['attachment']['payload']['adjustments'] = []

            for adjustment in self.adjustments:
                result['attachment']['payload'][
                    'adjustments'].append(adjustment.getdata())
        return {
            "recipient": {
                "id": self.recipient
            },
            "message": result
        }
