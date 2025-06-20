from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, render, redirect
from car_rental.models import Car, Booking
from car_rental.forms import PaymentForm, BookingForm
from datetime import datetime
from django.utils.timezone import make_aware, timezone
from django.core.mail import send_mail
from django.conf import settings
from decimal import Decimal
from django.http import JsonResponse
from django.urls import reverse
from django.utils import timezone
import uuid

# ...
timezone.now()



def index(request):
    return render(request, 'index.html')

def browse_cars(request):
    cars = Car.objects.all()
    error = None

    search_query = request.GET.get('search', '')
    car_type = request.GET.get('car_type', '')
    transmission = request.GET.get('transmission', '')
    sort = request.GET.get('sort', '')

    start_date = request.GET.get('start_date')
    start_time = request.GET.get('start_time')
    end_date = request.GET.get('end_date')
    end_time = request.GET.get('end_time')

    # Filter cars based on booking availability
    if all([start_date, start_time, end_date, end_time]):
        try:
            start_datetime = make_aware(datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %I:%M %p"))
            end_datetime = make_aware(datetime.strptime(f"{end_date} {end_time}", "%Y-%m-%d %I:%M %p"))

            if end_datetime <= start_datetime:
                error = "Drop-off must be after pickup."
            else:
                booked_car_ids = Booking.objects.filter(
                    start_datetime__lt=end_datetime,
                    end_datetime__gt=start_datetime
                ).values_list('car_id', flat=True)

                cars = cars.exclude(id__in=booked_car_ids)

                rental_hours = (end_datetime - start_datetime).total_seconds() / 3600
                rental_hours_decimal = Decimal(str(rental_hours))
                extra_hours = max(Decimal('0'), rental_hours_decimal - Decimal('12'))

                for car in cars:
                    car.dynamic_price_150km = float(car.calculate_price(rental_hours_decimal, '150km'))
                    car.dynamic_price_unlimited = float(car.calculate_price(rental_hours_decimal, 'unlimited'))
                    car.allowed_kms_150 = int(150 + extra_hours * car.extra_km_per_hour_150km)

        except ValueError:
            error = "Invalid date or time format."
        except Exception:
            pass  # Optionally log exceptions

    # Apply search and filters
    if search_query:
        cars = cars.filter(name__icontains=search_query)

    if car_type:
        cars = cars.filter(car_type=car_type)

    if transmission:
        cars = cars.filter(transmission__iexact=transmission)

    if sort == 'price_low':
        cars = cars.order_by('price_100km')
    elif sort == 'price_high':
        cars = cars.order_by('-price_100km')

    # Prepare prices for template
    calculated_prices = {}
    if all([start_date, start_time, end_date, end_time]) and not error:
        try:
            start_datetime = make_aware(datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %I:%M %p"))
            end_datetime = make_aware(datetime.strptime(f"{end_date} {end_time}", "%Y-%m-%d %I:%M %p"))
            rental_hours = (end_datetime - start_datetime).total_seconds() / 3600
            rental_hours_decimal = Decimal(str(rental_hours))
            extra_hours = max(Decimal('0'), rental_hours_decimal - Decimal('12'))

            for car in cars:
                allowed_kms = int(150 + extra_hours * car.extra_km_per_hour_150km)
                calculated_prices[car.id] = {
                    '150km': round(float(car.calculate_price(rental_hours_decimal, '150km')), 2),
                    'unlimited': round(float(car.calculate_price(rental_hours_decimal, 'unlimited')), 2),
                    'allowed_kms_150': allowed_kms  # ✅ added line
                }

        except Exception:
            pass

    context = {
        'cars': cars,
        'search_query': search_query,
        'car_type': car_type,
        'transmission': transmission,
        'sort': sort,
        'start_date': start_date,
        'start_time': start_time,
        'end_date': end_date,
        'end_time': end_time,
        'error': error,
        'calculated_prices': calculated_prices,
    }
    return render(request, 'browse_cars.html', context)



def car_detail(request, pk):
    car = get_object_or_404(Car, pk=pk)
    return render(request, 'car_detail.html', {'car': car})


def pay_online(request):
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            # Payment processing logic here
            return redirect('payment_success')
    else:
        form = PaymentForm()
    return render(request, 'pay_online.html', {'form': form})


def payment_success(request):
    return render(request, 'payment_success.html')


def about(request):
    return render(request, "about.html")


def car_book(request, pk):
    car = get_object_or_404(Car, pk=pk)

    start_date = request.GET.get('start_date')
    start_time = request.GET.get('start_time') or "10:00 AM"
    end_date = request.GET.get('end_date')
    end_time = request.GET.get('end_time') or "10:00 AM"
    kms = request.GET.get('kms') or "100km"

    hours_float = 0.0
    try:
        start_datetime = make_aware(datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %I:%M %p"))
        end_datetime = make_aware(datetime.strptime(f"{end_date} {end_time}", "%Y-%m-%d %I:%M %p"))
        hours_float = round((end_datetime - start_datetime).total_seconds() / 3600, 2)
    except Exception:
        start_datetime = None
        end_datetime = None

    try:
        price = float(car.calculate_price(hours_float, kms))
    except Exception:
        price = 0.0

    price_150 = price_unlimited = 0.0
    try:
        price_150 = round(car.calculate_price(hours_float, '150km'), 2)
        price_unlimited = round(car.calculate_price(hours_float, 'unlimited'), 2)
    except Exception:
        pass

    initial_data = {}
    if start_datetime:
        initial_data['start_datetime'] = start_datetime
    if end_datetime:
        initial_data['end_datetime'] = end_datetime

    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            hours_float_post = round((data['end_datetime'] - data['start_datetime']).total_seconds() / 3600, 2)
            kms_post = request.POST.get('kms') or kms

            try:
                price_post = float(car.calculate_price(hours_float_post, kms_post))
            except Exception:
                price_post = 0.0

            if data['end_datetime'] <= data['start_datetime']:
                form.add_error('end_datetime', 'End datetime must be after start datetime.')
            elif data['start_datetime'] < timezone.now():
                form.add_error('start_datetime', 'Start datetime cannot be in the past.')
            else:
                approval_token = str(uuid.uuid4())

                # ✅ Save booking info in session instead of database
                request.session[f'pending_booking_{approval_token}'] = {
                    'car_id': car.id,
                    'start_datetime': data['start_datetime'].isoformat(),
                    'end_datetime': data['end_datetime'].isoformat(),
                    'full_name': data['full_name'],
                    'phone': data['phone'],
                    'email': data['email'],
                    'kms_plan': kms_post,
                }

                approval_link = request.build_absolute_uri(
                    reverse('approve_booking', args=[approval_token])
                )

                # Calculate allowed kms
                if kms_post == '150km':
                    extra_hours = max(0, hours_float_post - 12)
                    allowed_kms = int(150 + extra_hours * car.extra_km_per_hour_150km)
                else:
                    allowed_kms = "Unlimited"

                message = (
                    f"🚗 Booking Request: {car.name}\n\n"
                    f"Full Name: {data['full_name']}\n"
                    f"Email: {data['email']}\n"
                    f"Phone: {data['phone']}\n\n"
                    f"Pickup Date & Time: {data['start_datetime'].strftime('%d-%m-%Y %H:%M')}\n"
                    f"Drop-off Date & Time: {data['end_datetime'].strftime('%d-%m-%Y %H:%M')}\n"
                    f"Kilometers Plan: {kms_post}\n"
                    f"Allowed KMs: {allowed_kms}\n"
                    f"Rental Hours: {hours_float_post} hours\n"
                    f"Estimated Price: ₹{price_post:.2f}\n\n"
                    f"✅ Approve here: {approval_link}"
                )

                send_mail(
                    subject=f"New Booking Request - {car.name}",
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[settings.MANAGER_EMAIL],
                    fail_silently=False,
                )

                return redirect('booking_pending')
    else:
        form = BookingForm(initial=initial_data)

    return render(request, 'car_book.html', {
        'car': car,
        'form': form,
        'start_date': start_date,
        'start_time': start_time,
        'end_date': end_date,
        'end_time': end_time,
        'hours': hours_float,
        'kms': kms,
        'price': price,
        'price_150': price_150,
        'price_unlimited': price_unlimited,
    })



def booking_pending(request):
    return render(request, 'booking_pending.html')


def approve_booking(request, token):
    session_key = f'pending_booking_{token}'
    pending_data = request.session.get(session_key)

    if not pending_data:
        return render(request, 'booking_approved.html', {
            'error': 'Booking data not found or already approved.'
        })

    try:
        car = Car.objects.get(id=pending_data['car_id'])
        start_datetime = make_aware(datetime.fromisoformat(pending_data['start_datetime']))
        end_datetime = make_aware(datetime.fromisoformat(pending_data['end_datetime']))
        kms_plan = pending_data.get('kms_plan', '150km')

        # ✅ Check for overlapping bookings again (optional but good practice)
        overlapping = Booking.objects.filter(
            car=car,
            end_datetime__gt=start_datetime,
            start_datetime__lt=end_datetime,
            is_approved=True
        )
        if overlapping.exists():
            return render(request, 'booking_approved.html', {
                'error': 'Another approved booking already exists for this time slot.'
            })

        # ✅ Create the actual booking now
        booking = Booking.objects.create(
            car=car,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            user_email=pending_data['email'],
            full_name=pending_data['full_name'],
            phone=pending_data['phone'],
            is_approved=True
        )

        # ✅ Remove booking from session after saving
        del request.session[session_key]

        # ✅ Calculate price
        rental_hours = (end_datetime - start_datetime).total_seconds() / 3600
        try:
            price = car.calculate_price(rental_hours, kms_plan)
        except Exception:
            price = 0.0

        # ✅ Send confirmation email
        success_link = request.build_absolute_uri(
            reverse('booking_success', args=[booking.id])
        )
        send_mail(
            subject="Your booking is approved!",
            message=(
                f"Dear {booking.full_name},\n\n"
                f"Your booking for {car.name} has been approved.\n"
                f"Pickup: {start_datetime.strftime('%d-%m-%Y %H:%M')}\n"
                f"Drop-off: {end_datetime.strftime('%d-%m-%Y %H:%M')}\n"
                f"Kilometers Plan: {kms_plan}\n"
                f"Estimated Price: ₹{float(price):.2f}\n\n"
                f"You can view confirmation details here:\n{success_link}"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[booking.user_email],
            fail_silently=False,
        )

        return render(request, 'booking_approved.html', {'booking': booking})

    except Exception as e:
        return render(request, 'booking_approved.html', {
            'error': f"Error while approving booking: {str(e)}"
        })



def booking_success(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    if not booking.is_approved:
        return render(request, 'booking_pending.html', {'car': booking.car})

    return render(request, 'booking_success.html', {'booking': booking})



def get_dynamic_prices(request):
    def parse_datetime_flexible(date_str, time_str):
        """Tries to parse datetime from 12-hour or 24-hour formats."""
        try:
            return make_aware(datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %I:%M %p"))
        except ValueError:
            try:
                return make_aware(datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M"))
            except ValueError:
                return None

    # Get request parameters
    start_date = request.GET.get('start_date')
    start_time = request.GET.get('start_time')
    end_date = request.GET.get('end_date')
    end_time = request.GET.get('end_time')
    car_id = request.GET.get('car_id')

    # Validate required fields
    if not all([start_date, start_time, end_date, end_time, car_id]):
        return JsonResponse({'error': 'Missing data'}, status=400)

    try:
        # Fetch car
        car = Car.objects.get(id=car_id)

        # Parse datetime objects
        start_datetime = parse_datetime_flexible(start_date, start_time)
        end_datetime = parse_datetime_flexible(end_date, end_time)

        if not start_datetime or not end_datetime:
            return JsonResponse({'error': 'Invalid date/time format'}, status=400)

        # Calculate rental hours
        rental_hours = (end_datetime - start_datetime).total_seconds() / 3600
        rental_hours_decimal = Decimal(str(rental_hours))

        # Calculate allowed kms for 150km plan (12-hour base + extra)
        extra_hours = max(Decimal('0'), rental_hours_decimal - Decimal('12'))
        allowed_kms_150 = int(150 + extra_hours * car.extra_km_per_hour_150km)

        prices = {
            '150km': f"{car.calculate_price(rental_hours_decimal, '150km'):.0f}",
            'unlimited': f"{car.calculate_price(rental_hours_decimal, 'unlimited'):.0f}",
            'allowed_kms_150': allowed_kms_150
        }

        return JsonResponse({'prices': prices})

    except Car.DoesNotExist:
        return JsonResponse({'error': 'Car not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


def contactus(request):
    return render(request, "contactus.html")
