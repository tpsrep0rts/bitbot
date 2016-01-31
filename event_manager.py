
class Event(object):
  def __init__(self, code, params = [], metadata = {}):
    self.code = code
    self.params = params
    self.metadata = metadata

  def __str__(self):
    string = self.code
    if self.params:
      string += ", " + ", ".join(self.params)
    if self.metadata:
      string += ", [" + str(self.metadata) + "]"
    return string

class EventSubscription(object):
  def __init__(self, event, callback):
    self.event = event
    self.callback = callback

  def should_notify(self, event):
    should_notify = False
    params_count = len(event.params)
    if(self.event.code == event.code and params_count >= len(self.event.params)):
      should_notify = True
      for index, param in enumerate(self.event.params):
        if(self.event.params[index] != event.params[index]):
          should_notify = False
          break
    return should_notify

  def notify(self, event):
    if self.should_notify(event):
      self.callback(event)
  
class EventManager(object):
  subscriptions = {}

  @staticmethod
  def add_subscription(code, params, callback):
    if(not code in EventManager.subscriptions):
      EventManager.subscriptions[code] = []
    EventManager.subscriptions[code].append(EventSubscription(Event(code, params), callback))

  @staticmethod
  def notify(event):
    if(event.code in EventManager.subscriptions):
      for subscriber in EventManager.subscriptions[event.code]:
        subscriber.notify(event)


#class TestSubscriber(object):
#  def register_callbacks(self):
#    EventManager.add_subscription("test", ["one"], self.test_callback)
#
#  def test_callback(self, event):
#    print "got a callback!" + str(event)
#
#subscriber = TestSubscriber()
#subscriber.register_callbacks()
#    EventManager.add_subscription("test", ["one"], self.test_callback)
#EventManager.notify("test", ["one", "two"])
