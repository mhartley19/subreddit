from django.shortcuts import render, redirect, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from posts.forms import PostForm, CommentForm, PostImage
from posts.models import Post
from net.models import Net
from notification.utilities import create_notification


def individual_post_view(request, post_id):
    context = {'header': "Post Details"}
    post = Post.objects.get(id=post_id)
    comments = Post.objects.filter(parent=post).order_by('timestamp')
    root_post = post.get_root()
    if request.method == 'POST':
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            data = comment_form.cleaned_data
            new_post = Post.objects.create(
                header = data['header'],
                author = request.user,
                post_type = 'Comment',
                parent = post,
                subnet = post.subnet
            )
            return redirect(f"/posts/{root_post.id}/")
    comment_form = CommentForm()
    comment_form.fields['header'].label = ""
    time = (post.timestamp - timezone.now())
    time_ago = round(time.total_seconds()/3600 *(-1))
    if time_ago > 24:
        time_ago = round(time_ago/24)
        time_ago = f"{time_ago} days ago"
    elif time_ago <= 1:
        time_ago = f"less than {time_ago} hour ago"
    else:
        time_ago = f"{time_ago} hours ago"
    context.update({'post': post, 'comments': comments, 'comment_form': comment_form, 'time': time_ago})
    return render(request, 'individual_posts.html', context)

@login_required
def create_post_view(request, net_title):
    context = {'header': "Post a Post"}
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            subnet = Net.objects.get(title=net_title)
            new_post = Post.objects.create(
                post_type = 'Post',
                author = request.user,
                subnet = subnet,
                header = data['header'],
                content = data['content'],
            )
            return HttpResponseRedirect(f'/nets/{net_title}')
    form = PostForm()
    context.update({'form':form})
    return render(request, 'forms.html', context)

@login_required
def post_image_view(request, net_title):
    context = {'header': "Post an Image"}
    user = request.user
    if request.method == 'POST':
        form = PostImage(request.POST, request.FILES, instance=user)
        if form.is_valid():
            data = form.cleaned_data
            subnet = Net.objects.get(title=net_title)
            new_post = Post.objects.create(
                post_type = 'Post',
                author = user,
                subnet = subnet,
                header = data['header'],
                image = data['image'],
            )
            form.save()
            return HttpResponseRedirect(f'/nets/{net_title}')
    form = PostImage()
    context.update({'form':form})
    return render(request, 'forms.html', context)

@login_required
def post_comment_view(request, post_id):
    post = Post.objects.filter(id=post_id).first()
    post.created_by = request.user
    root_post = post.get_root()
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            new_post = Post.objects.create(
                header = data['header'],
                author = request.user,
                post_type = 'Comment',
                parent = post,
                subnet = post.subnet
            )
            create_notification(request, post.created_by, 'new_post', extra_id=new_post.id)
            return redirect(f"/posts/{root_post.id}/")
    form = CommentForm()
    header = f'Post a comment on \"{post.header}\":'
    return_link = f"/posts/{root_post.id}/"
    context = {'form': form, 'header': header, "root_link":return_link}
    return render(request, "forms.html", context)

@login_required
def upvotes_view(request, post_id):
    current_user = request.user
    post = Post.objects.filter(id=post_id).first()
    for liked_posts in current_user.has_liked.all():
        if liked_posts == post:
            return redirect('/')
    current_user.has_liked.add(post)
    current_user.has_disliked.remove(post)
    post.upvotes +=1
    current_user.save()
    post.save()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@login_required
def downvotes_view(request, post_id):
    current_user = request.user
    post = Post.objects.filter(id=post_id).first()
    for disliked_post in current_user.has_disliked.all():
        if disliked_post == post:
            return redirect('/')
    current_user.has_disliked.add(post)
    current_user.has_liked.remove(post)
    post.downvotes +=1
    current_user.save()
    post.save()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
