from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UsernameField
from django.core.paginator import Paginator
from django.db.models import Count
from django.forms import ModelForm
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import CommentForm, PostForm
from .models import Category, Comment, Post

UserModel = get_user_model()


class EditUserForm(ModelForm):
    class Meta:
        model = UserModel
        fields = ['first_name', 'last_name', 'username', 'email']
        field_classes = {'username': UsernameField}


def paginate_queryset(queryset, request, per_page=10):
    paginator = Paginator(queryset, per_page)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


def index(request):
    posts = (Post.published.all()
             .annotate(comment_count=Count('comments'))
             .order_by('-pub_date'))
    page_obj = paginate_queryset(posts, request, per_page=10)
    return render(request, "blog/index.html", {"page_obj": page_obj})


def post_detail(request, post_id):
    post = get_object_or_404(Post.objects.select_related('category'), id=post_id)

    is_post_published = post.is_published and post.pub_date <= timezone.now()
    is_category_published = post.category is None or post.category.is_published
    if request.user != post.author and (not is_post_published or not is_category_published):
        raise Http404

    comments = post.comments.select_related("author").order_by("created_at")
    form = CommentForm()
    return render(request, "blog/detail.html", {"post": post, "form": form, "comments": comments})


def category_posts(request, category_slug):
    category = get_object_or_404(Category, slug=category_slug, is_published=True)
    posts = (Post.published.filter(category=category)
             .annotate(comment_count=Count('comments'))
             .order_by('-pub_date'))
    page_obj = paginate_queryset(posts, request, per_page=10)
    return render(request, 'blog/category.html', {'category': category, 'page_obj': page_obj})


def profile(request, username):
    User = get_user_model()
    profile_user = get_object_or_404(User, username=username)
    if request.user.is_authenticated and request.user == profile_user:
        qs = Post.objects.filter(author=profile_user)
    else:
        qs = Post.published.filter(author=profile_user)
    posts = qs.annotate(comment_count=Count('comments')).order_by('-pub_date')
    page_obj = paginate_queryset(posts, request, per_page=10)
    return render(request, 'blog/profile.html', {'profile': profile_user, 'page_obj': page_obj})


@login_required
def edit_profile(request, username):
    if request.user.username != username:
        return redirect('blog:profile', username=username)

    if request.method == 'POST':
        form = EditUserForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('blog:profile', username=request.user.username)
    else:
        form = EditUserForm(instance=request.user)
    return render(request, 'blog/user.html', {'form': form})


@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            if hasattr(form, 'save_m2m'):
                form.save_m2m()
            return redirect('blog:profile', username=request.user.username)
    else:
        form = PostForm()
    return render(request, 'blog/create.html', {'form': form})


@login_required
def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('blog:post_detail', post_id=post.id)

    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', post_id=post.id)
    else:
        form = PostForm(instance=post)
    return render(request, 'blog/create.html', {'form': form})


@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id, author=request.user)
    if request.method == "POST":
        post.delete()
        return redirect("blog:profile", username=request.user.username)
    form = PostForm(instance=post)
    return render(request, "blog/create.html", {"form": form})


@login_required
def add_comment(request, post_id):
    if request.method != 'POST':
        # Комментарии создаём только POST’ом
        raise Http404

    # Строгий queryset только для доступных постов
    post = get_object_or_404(
        Post.objects.filter(
            is_published=True,
            pub_date__lte=timezone.now(),
            category__is_published=True,
        ),
        id=post_id,
    )

    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()
        return redirect('blog:post_detail', post_id=post.id)

    # На невалидной форме — показать ту же страницу с ошибками
    comments = post.comments.select_related('author').order_by('created_at')
    return render(
        request, 'blog/detail.html',
        {'post': post, 'form': form, 'comments': comments},
    )


@login_required
def edit_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, post_id=post_id, author=request.user)
    form = CommentForm(request.POST or None, instance=comment)
    if form.is_valid():
        form.save()
        return redirect("blog:post_detail", post_id=post_id)
    return render(request, "blog/comment.html", {"form": form, "comment": comment})


@login_required
def delete_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, post_id=post_id, author=request.user)
    if request.method == "POST":
        comment.delete()
        return redirect("blog:post_detail", post_id=post_id)
    return render(request, "blog/comment.html", {"comment": comment})

