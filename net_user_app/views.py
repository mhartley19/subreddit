from django.shortcuts import render, redirect, HttpResponseRedirect
from django.contrib import messages
from net.views import search_net, search_user
from net_user_app.models import NetUser
from net_user_app.forms import NetUserUpdateForm
from posts.models import Post
from net.forms import SearchForm, UserSearchForm

import os

def get_total_user_votes(posts):
    posts = posts
    total_votes = 0
    for post in posts:
        total_votes = total_votes + post.total_score
    return total_votes




def profile_view(request, username):
    context = {}
    if request.method == 'POST':
        return_url = search_net(request)
        searched_user_url = search_user(request)
        if return_url:
            return redirect(return_url)
        else:
            print("working")
            net_not_found = True
        if searched_user_url:
            return redirect(searched_user_url)
        else:
            user_not_found = True
        
    page_user = NetUser.objects.get(username=username)
    followers = page_user.followers.all().order_by("username")
    posts = Post.objects.filter(author=page_user).order_by('-timestamp')
    subs = page_user.subs.all().order_by('title')
    total_votes = get_total_user_votes(posts)
    is_followed = check_follow(request, username)
    search_form = SearchForm()
    user_form = UserSearchForm()
    context.update({
        "user": page_user,
        'followers': followers,
        'posts': posts,
        'subs': subs,
        'total_votes': total_votes,
        'is_followed': is_followed,
        'search_form': search_form,
        'user_form': user_form,
        })
    return render(request, 'profile.html', context)

def update_user(request, user_id):
    current_user = NetUser.objects.get(id=user_id)
    current_image = current_user.profile_image
    if current_image:
        image_path = current_user.profile_image.path
    else:
        image_path = "dummy string"
    if request.method == "POST":
        form = NetUserUpdateForm(request.POST, request.FILES, instance=current_user)
        if form.is_valid():
            if current_image != form.cleaned_data['profile_image']:
                if os.path.exists(image_path):
                    os.remove(image_path)
            form.save()
            messages.success(request, "User info updated successfully.")
            return redirect(f'/users/{current_user.username}/')
    else:
        form = NetUserUpdateForm(initial={'username':current_user.username ,'bio':current_user.bio ,'email':current_user.email , 'profile_image': current_user.profile_image})

    context = {'form': form}
    return render(request, 'forms.html', context)

def change_theme(request):
    current_user = request.user
    if current_user.site_theme == "Light":
        current_user.site_theme = 'Dark'
        current_user.save()
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    else:
        current_user.site_theme = 'Light'
        current_user.save()
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


def check_follow(request, username):
    user_info = NetUser.objects.get(username=username)
    current_user = request.user
    follows = current_user.followers
    if follows.filter(username=username).exists():
        is_followed =True
    else:
        is_followed =False
    return is_followed


def follow_user(request, username):
    current_user = request.user
    other_user = NetUser.objects.get(username=username)
    check_follower = current_user.followers
    is_followed = False
    if check_follower.filter(username=other_user).exists():
        check_follower.remove(other_user)
        is_followed = False
        return redirect(f'/users/{username}/')
    else:
        check_follower.add(other_user)
        is_followed = True
        return redirect(f'/users/{username}/')




