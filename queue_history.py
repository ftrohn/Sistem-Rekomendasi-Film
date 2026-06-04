class Queue:
  def __init__(self):
    self.items = []
    
  def enqueue(self, item):
    self.items.append(item)
    
  def dequeue(self):
    if len(self.items) > 0:
      return self.items.pop(0)
    return None
    
  def show(self):
    return self.items
