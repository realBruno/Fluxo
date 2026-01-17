class Node:
    def __init__(self, data):
        self.data = data
        self.next = None

class Stack:
    def __init__(self):
        self.top = None

    def push(self, data):
        new_item = Node(data)
        new_item.next = self.top
        self.top = new_item

    def pop(self):
        if self.top is None:
            return None
        val = self.top.data
        self.top = self.top.next
        return val

    def peek(self):
        if self.top is None:
            return None
        return self.top.data