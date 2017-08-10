class MessageReceiptElement(object):

    def __init__(self, title, subtitle, image_url='', quantity=1, price=0, currency="MXN"):

        self.title = title
        self.subtitle = subtitle
        self.image_url = image_url
        self.quantity = quantity
        self.price = price
        self.currency = currency

    def getdata(self):
        return self.__dict__


class Address(object):

    def __init__(self, country, state, city, postal_code, street_1, street_2=''):
        self.country = country
        self.state = state
        self.city = city
        self.postal_code = postal_code
        self.street_1 = street_1
        self.street_2 = street_2

    def getdata(self):
        return self.__dict__


class Summary(object):

    def __init__(self, total_cost, subtotal=None, shipping_cost=None, total_tax=None):
        self.total_cost = total_cost
        self.subtotal = subtotal
        self.shipping_cost = shipping_cost
        self.total_tax = total_tax

    def getdata(self):
        return self.__dict__


class Adjustment(object):

    def __init__(self, name=None, amount=None):
        self.name = name
        self.amount = amount

    def getdata(self):
        return self.__dict__
