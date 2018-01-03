class Order(object):
	"""docstring for Order"""
	def __init__(self, name,course,date,price,discount,sale_price):
		super(Order, self).__init__()
		self.name = name
		self.course = course
		self.date = date
		self.price = price
		self.discount = discount
		self.sale_price = sale_price
		