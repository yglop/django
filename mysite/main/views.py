from django.shortcuts import render, redirect
from .forms import *
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .decorators import unauthenticated_user, allowed_users
import random


def home(request):
    books = Book.objects.all()
    if books:
        book1, book2, book3, book4 = random.choice(books), random.choice(books), random.choice(books), random.choice(books)
        book5, book6, book7, book8 = random.choice(books), random.choice(books), random.choice(books), random.choice(books)
        return render(request, 'main/home.html', {'book1': book1, 'book2': book2, 'book3': book3, 'book4': book4,
                                                  'book5': book5, 'book6': book6, 'book7': book7, 'book8': book8,
                                                  })
    else:
        return render(request, 'main/home.html', {})


@unauthenticated_user
def registerPage(response):
    form = RegisterForm()
    if response.method == 'POST':
        form = RegisterForm(response.POST)
        if form.is_valid():
            form.save()
            return redirect('/login')

    return render(response, 'main/register.html', {'form': form})


@unauthenticated_user
def loginPage(request):
    form = AuthForm()
    if request.method == 'POST':
        form = AuthForm(request.POST)
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('home')

    return render(request, 'main/login.html', {'form': form})


def logoutUser(request):
    logout(request)
    return redirect('/')


@login_required(login_url='login')
@allowed_users(allowed_roles=['Customer'])
def user_settings(request):
    customer = request.user.customer
    customer_settings_form = CustomerSettingsForm(instance=customer)

    user = request.user
    user_settings_form = UserSettingsForm(instance=user)

    if request.method == 'POST':
        customer_settings_form = CustomerSettingsForm(request.POST, request.FILES, instance=customer)
        user_settings_form = UserSettingsForm(request.POST, instance=user)

        if customer_settings_form.is_valid():
            customer_settings_form.save()
        if user_settings_form.is_valid():
            user_settings_form.save()

            msave = Customer.objects.get(user=user)
            msave.name = request.user.username
            msave.email = request.user.email
            msave.save()

    context = {'customer_settings_form': customer_settings_form, 'user_settings_form': user_settings_form}
    return render(request, 'main/user_settings.html', context)


@login_required(login_url='login')
@allowed_users(allowed_roles=['Customer'])
def become_seller(request):
    customer = request.user.customer

    if request.method == "POST":
        customer.is_seller = True
        customer.save()
        return redirect('/book_management')

    return render(request, 'main/become_seller.html', {'customer': customer})


def user_page(request, id):
    customer = Customer.objects.get(id=id)

    books_have = [i.book for i in BooksHave.objects.all() if i.owner == customer]
    data_have = {}
    for i in books_have:
        data_have[i.name] = i.id

    books_sale = [i for i in Book.objects.all() if i.seller == customer]
    data_sale = {}
    for i in books_sale:
        data_sale[i.name] = i.id

    context = {'customer': customer, 'data_have': data_have, 'data_sale': data_sale}
    return render(request, 'main/user_page.html', context)


@login_required(login_url='login')
@allowed_users(allowed_roles=['Customer'])
def book_creation(request):
    form = BookCreationForm()
    if request.method == 'POST':
        form = BookCreationForm(request.POST, request.FILES)

        if form.is_valid():
            book_name = form.cleaned_data.get('name')
            book_author = form.cleaned_data.get('author')
            book_price = form.cleaned_data.get('price')
            book_category = form.cleaned_data.get('category')
            book_description = form.cleaned_data.get('description')
            book_picture = form.cleaned_data.get('picture')
            book_file = form.cleaned_data.get('book_file')

            if ',' in book_name:
                a = book_name.count(',')
                for i in range(a):
                    book_name = book_name.replace(',', ';')

            books = Book.objects.all()
            if book_name not in books:
                Book.objects.create(
                    seller=request.user.customer,
                    name=book_name,
                    author=book_author,
                    price=book_price,
                    category=book_category,
                    description=book_description,
                    picture=book_picture,
                    book_file=book_file,
                )

                return redirect('/book_management')
            else:
                form = BookCreationForm()

    return render(request, 'main/book_creation.html', {'form': form})


@login_required(login_url='login')
@allowed_users(allowed_roles=['Customer'])
def book_redaction(request, id):
    book = Book.objects.get(id=id)
    form = BookRedactionForm(instance=book)
    user = book.seller.user
    old_book_name = book.name

    if request.method == 'POST':
        form = BookRedactionForm(request.POST, request.FILES, instance=book)

        if form.is_valid():
            book_name = form.cleaned_data.get('name')
            if ',' in book_name:
                a = book_name.count(',')
                for i in range(a):
                    book_name = book_name.replace(',', ';')

            form.instance.name = book_name
            form.save()

            return redirect('/book_management')

    context = {'seller': user, 'form': form, 'pic': book.picture.url}
    return render(request, 'main/book_redaction.html', context)


def book_page(request, id):
    book = Book.objects.get(id=id)
    return render(request, 'main/book_page.html', {'book': book})


@login_required(login_url='login')
@allowed_users(allowed_roles=['Customer'])
def book_buy(request, id):
    customer = request.user.customer
    book = Book.objects.get(id=id)
    books_have = [i.book for i in BooksHave.objects.all() if i.owner == customer]

    dummi_flag = False
    if (book in books_have) or (book.seller == customer):
        dummi_flag = True

    if request.method == "POST":
        BooksHave.objects.create(
            owner=customer,
            book=book,
        )
        return redirect('/book_management')

    context = {'book': book, 'customer': customer, 'dummi_flag': dummi_flag}
    return render(request, 'main/book_buy.html', context)


@login_required(login_url='login')
@allowed_users(allowed_roles=['Customer'])
def book_management(request):
    user = request.user

    books_have = [i.book for i in BooksHave.objects.all() if i.owner == user.customer]
    books_sale = [i for i in Book.objects.all() if i.seller == user.customer]
    print(books_have)
    context = {'books_have': books_have, 'books_sale': books_sale}
    return render(request, 'main/book_management.html', context)


@login_required(login_url='login')
@allowed_users(allowed_roles=['Customer'])
def book_delete(request, id):
    book = Book.objects.get(id=id)

    if request.method == "POST":
        book.delete()
        return redirect('/book_management')

    context = {'book': book}
    return render(request, 'main/book_delete.html', context)


def search(request):
    books = Book.objects.all()

    searched = []
    if request.method == "POST":
        s_input = request.POST.get("search-input").lower()

        for i in books:
            if s_input in i.name.lower():
                searched.append(i)
        if len(searched) == 0:
            for i in books:
                if s_input in i.author.lower():
                    searched.append(i)
    context = {'searched': searched}
    return render(request, 'main/search.html', context)

