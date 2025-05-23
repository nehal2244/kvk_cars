# views.py
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from car_rental.models import Car
from car_rental.forms import PaymentForm


# username = Admin
# password = Admin@123

def index(request):
    return render(request , 'index.html')



def browse_cars(request):
    cars = Car.objects.filter(is_available=True)
    
    # Get filter parameters from GET
    search_query = request.GET.get('search', '')
    car_type = request.GET.get('car_type', '')
    transmission = request.GET.get('transmission', '')
    sort = request.GET.get('sort', '')

    # Filter by search name
    if search_query:
        cars = cars.filter(name__icontains=search_query)

    # Filter by car_type
    if car_type:
        cars = cars.filter(car_type=car_type)

    # Filter by transmission
    if transmission:
        cars = cars.filter(transmission=transmission)

    # Sorting
    if sort == 'price_low':
        cars = cars.order_by('price_per_day')
    elif sort == 'price_high':
        cars = cars.order_by('-price_per_day')

    context = {
        'cars': cars,
        'search_query': search_query,
        'car_type': car_type,
        'transmission': transmission,
        'sort': sort,
    }
    return render(request, 'browse_cars.html', context)

def car_detail(request, pk):
    car = get_object_or_404(Car, pk=pk)
    return render(request, 'car_detail.html', {'car': car})

def car_book(request, pk):
    car = get_object_or_404(Car, pk=pk)
    # Your booking logic here or render a booking form
    return render(request, 'car_book.html', {'car': car})

def pay_online(request):
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            # Here you would handle payment processing logic
            # For demo, just redirect to a success page
            return redirect('payment_success')
    else:
        form = PaymentForm()
    return render(request, 'pay_online.html', {'form': form})

def payment_success(request):
    return render(request, 'payment_success.html')

def about(request):
    return render(request, "about.html")

