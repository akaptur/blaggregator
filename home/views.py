from django.http import HttpResponse, Http404
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.template import Context, loader, RequestContext
from django.core.context_processors import csrf
from django.shortcuts import render_to_response
from home.models import Hacker
import requests

def login(request):
    ''''''
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        user = authenticate(username=email, password=password)

        if user is not None:
            # if user exists locally:
            if user.is_active:
                return HttpResponse("Welcome back, returning user %s!" % (email))
            else:
                return HttpResponse("Your account is disabled. Please contact administrator for help.")

        else:
            # this is an unknown user, try to auth against Hacker School
            resp = requests.get('https://www.hackerschool.com/auth', params={'email':email, 'password':password})

            if resp.status_code == requests.codes.ok:
                r = resp.json()
                try:
                    User.objects.get(id = r['hs_id'])
                    return HttpResponse("Welcome back %s! Returning user %s" % (r['first_name'], r['hs_id']))
                except:
                    # create a new account
                    username = r['first_name']+r['last_name']
                    user = User.objects.create_user(username, email, password, id=r['hs_id'])
                    Hacker.objects.create(user=User.objects.get(id=r['hs_id']))
                    user.first_name = r['first_name']
                    user.last_name = r['last_name']
                    user.hacker.github = r['github']
                    user.hacker.twitter = r['twitter']
                    user.hacker.irc = r['irc']
                    user.save()
                    user.hacker.save()
                    return HttpResponse("Just created user %s with id %s" % (r['first_name'], r['hs_id']))
                return render_to_response('home/new.html')
            else:
                return HttpResponse("Auth Failed! (%s). Please hit 'back' and try again." % resp.status_code)
    else:
        # todo: serve error!
        return render_to_response('home/login.html', {},
                                   context_instance=RequestContext(request))

def profile(request, user_id):
    try:
        current_user = User.objects.get(id=user_id)
        template = loader.get_template('home/index.html')
        context = Context({
            'current_user': current_user,
        })
    except User.DoesNotExist:
        raise Http404
    return HttpResponse(template.render(context))

def new(request):
    return render_to_response('home/new.html')
