class SimpleMessage(object):
    TYPE_TEXT = 'text'
    TYPE_IMAGE = 'image'

    def __init__(self, recipient, content, type='text'):
        self.recipient = recipient
        self.content = content
        self.type = type

    def getdata(self, metadata=None):
        result = {
            "recipient": {
                "id": self.recipient
            },
            "message": {}
        }
        if self.type == self.TYPE_TEXT:
            result['message']['text'] = self.content
        elif self.type == self.TYPE_IMAGE:
            result['message'] = {
                "attachment": {
                    "type": "image",
                    "payload": {
                        "url": self.content
                    }
                }
            }
        if metadata is not None:
            result['message']['metadata'] = metadata

        return result
