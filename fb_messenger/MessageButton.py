class MessageButton(object):

    TYPE_WEB = "web_url"
    TYPE_POSTBACK = "postback"
    TYPE_PHONE = "phone_number"

    def __init__(self, type, title, url='', phone=None):
        self.type = type
        self.title = title
        if not url:
            url = title
        self.url = url
        if phone is not None:
            self.phone = phone

    def getdata(self):

        result = {'type': self.type, 'title': self.title, 'webview_height_ratio': 'tall'}

        if self.type == self.TYPE_POSTBACK:
            result['payload'] = self.url
        elif self.type == self.TYPE_WEB:
            result['url'] = self.url
        elif self.type == self.TYPE_PHONE:
            result['payload'] = self.phone
        return result
