class MessageElement(object):

    def __init__(self, title=None, subtitle=None, image_url=None, buttons=None):
        self.title = title
        self.subtitle = subtitle
        self.image_url = image_url
        if buttons is not None:
            self.buttons = buttons

    def getdata(self):

        result = self.__dict__
        print result
        if 'buttons' in result:
            result['buttons'][:] = [button.getdata() for button in result['buttons']]
        elif self.subtitle is None and self.image_url is None:
            result['subtitle'] = self.title
        print result
        return result
