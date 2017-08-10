import json


class MediaAttachment(object):

    TYPE_IMAGE = 'image'
    TYPE_AUDIO = 'audio'
    TYPE_VIDEO = 'video'
    TYPE_FILE = 'file'

    def __init__(self, recipient, type, file):
        self.recipient = recipient
        self.type = type
        self.file = file

    def getdata(self):
        return json.dumps({
            "recipient": {
                "id": self.recipient
            },
            "message": {
                "attachment": {
                    "type": self.type,
                    "payload": {
                        "url": self.file
                    }
                }
            }
        })
