import random

from django.shortcuts import render


def index(request):
    greetings = ['Hello, world!', 'Greetings!', 'Hi there!', 'Yo!', 'Hey!', 'Hi!']
    return render(request, 'main/index.html', {'greeting': random.choice(greetings)})


def reserved(request):
    return render(request, 'main/reserved.html')
