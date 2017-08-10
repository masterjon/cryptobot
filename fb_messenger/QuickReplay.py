class QuickReplay(object):

    def __init__(self, recipient, text, quick_replies):
        self.recipient = recipient
        self.text = text
        self.quick_replies = quick_replies

    def getdata(self):
        result = {
            "recipient": {
                "id": self.recipient
            },
            "message": {
                "text": self.text
            }
        }
        result['message']['quick_replies'] = []
        for btn in self.quick_replies:
            result['message']['quick_replies'].append(btn.getdata())

        return result


class ButtonReplay(object):

    def __init__(self, title, payload, image_url=None):
        self.content_type = 'text'
        self.title = title
        self.payload = payload
        self.image_url = image_url

    def getdata(self):
        return self.__dict__
