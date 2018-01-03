import csv
from .models import Order

def load_from_csv():
	order_list = []
	with open('import.csv') as csvfile:
	    reader = csv.DictReader(csvfile)	    
	    for row in reader:
	        # The header row values become your keys
	        student_name = row['Name']
	        course = row['Course']
	        date = row['Date']
	        price = row['Price']
	        discount = row['Discount']
	        sale_price = row ['Sale_Price']

	        order  = Order(name=student_name, course=course, date = date, price = price, discount = discount, sale_price = int(sale_price))
	        order_list.append(order)
		
	return order_list    
