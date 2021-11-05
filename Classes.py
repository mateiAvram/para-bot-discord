class Queue:
	def __init__(self):
		self.queue = []

	def is_empty(self):
		return len(self.queue) == 0

	def front(self):
		return self.queue[-1]

	def rear(self):
		return self.queue[0]

	def enqueue(self, element):
		self.queue.insert(0, element)

	def dequeue(self):
		element = self.queue[-1]
		self.queue.pop()
		return element

	def empty(self):
		while len(self.queue) > 0:
			self.queue.pop()

	def list(self):
		queue_list = list(self.queue)
		return queue_list
