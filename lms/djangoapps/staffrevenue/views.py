from django.shortcuts import render_to_response
from .load_from_csv import load_from_csv

def index(request):    
    order_list = load_from_csv()
    total_revenue = 0
    courses = {}
    for order in order_list:
    	total_revenue = total_revenue + order.sale_price
    	if(order.course not in courses):
    		courses[order.course] = 0
        for course in courses:
        	if(order.course == course):
        		courses[course] += order.sale_price
    taxes = total_revenue *0.12
    your_revenue = (total_revenue - taxes)/2
    context = {
        'order_list' : order_list,
        'total_revenue': total_revenue,
        'taxes':taxes,
        'your_revenue':your_revenue,
        'courses':courses
    }
    return render_to_response("staffrevenue/revenue.html", context)