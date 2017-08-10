import requests
from django.conf import settings


class FbApp(object):

    def __init__(self, token):
        self.apiUrl = 'https://graph.facebook.com/v2.6/'
        self.token = token

    def send(self, message):
        return self.call('me/messages', message.getdata())

    def set_menu(self, menu):
        return self.call('me/messenger_profile', menu)

    def pass_thread_control(self, thread):
        return self.call('me/pass_thread_control', thread)

    def call(self, url, data):
        params = {'access_token': self.token}
        r = requests.post(
            self.apiUrl + url,
            params=params,
            json=data)
        response = r.json()
        if 'error' not in response and r.status_code == 200:
            # recipient_id = response['recipient_id']
            # recipient_id = response['recipient_id'] if 'recipient_id' in response else None
            # message_id = response['message_id'] if 'message_id' in response else None
            # print "Successfully sent generic message with id {} to recipient {}".format(recipient_id, message_id)
            print response
        else:
            print "Unable to send message."
            print r.reason
            print response
        return response

cocobot_token = settings.FB_PAGE_ACCESS_TOKENS['cocobot']
bot = FbApp(cocobot_token)
