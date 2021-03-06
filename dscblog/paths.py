from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from dscblog.common import to_json, apiRespond
from dscblog.models import User, Blog
import markdown

md = markdown.Markdown(extensions=['extra'])

def index(request):
    opts = {'header': {
        'is_loggedin': False, 'is_empty': False}}
    if request.user.is_authenticated:
        opts['header']['is_loggedin'] = True
    opts['blogs'] = []
    blogs = Blog.top25()
    for b in blogs:
        opts['blogs'].append(b.get_obj_min())
    res = render(request, 'index.html', opts)
    return res


@login_required
def my_profile(request):
    return redirect(to='/@'+request.user.username)


def profile(request, username):
    opts = {'header': {
        'is_loggedin': False, 'is_empty': False},
        'is_owner': request.user.is_authenticated and request.user.username == username}
    if request.user.is_authenticated:
        opts['header']['is_loggedin'] = True
    try:
        user = User.get_by_username(username)
    except:
        return page404(request)
    else:
        opts['user'] = user.get_profile(request.user)
        print(opts['user'])
        res = render(request, 'profile.html', opts)
        return res


def blog(request, slug, id):
    try:
        b = Blog.get_by_id(id)
    except:
        return page404(request)
    else:
        if b.get_slug() == slug:
            if b.is_published or (request.user.is_authenticated and request.user == b.author):
                opts = {'header': {
                    'is_loggedin': False, 'is_empty': True},
                    'blog': b.get_obj(),
                    'html':md.convert(b.content),
                    'is_owner': request.user.is_authenticated and request.user == b.author}
                if request.user.is_authenticated:
                    opts['header']['is_loggedin'] = True
                res = render(request, 'blog.html', opts)
                return res
            else:
                return page404(request)
        else:
            return redirect(to=b.get_url())


@login_required
def create(request):
    if request.method == 'GET':
        res = render(request, 'create.html')
    else:
        if 'title' in request.POST:
            title = request.POST['title'].strip()
            if len(title) > 2:
                b = Blog.create(request.user, title)
                res = redirect(to='/blog/'+str(b.id)+'/settings')
            else:
                res = render(request, 'create.html', {
                             'error': 'Title too small (min 3 characters)'})
        else:
            res = render(request, 'create.html', {
                         'error': 'Title field missing'})
    return res


@login_required
def blog_settings(request, id):
    try:
        b = Blog.get_by_id(id)
    except:
        return page404(request)
    else:
        if request.user == b.author:
            opts = {'header': {'is_loggedin': True, 'is_empty': False},
                    'blog': b.get_obj_min()}
            return render(request, 'blogSettings.html', opts)
        else:
            return page404(request)


@login_required
def blog_edit(request, id):
    try:
        b = Blog.get_by_id(id)
    except:
        return page404(request)
    else:
        if request.user == b.author:
            opts = {'header': {'is_loggedin': True, 'is_empty': False},
                    'blog': b.get_obj()}
            return render(request, 'blogEditor.html', opts)
        else:
            return page404(request)


@require_http_methods(["POST"])
def set_blog_title(request):
    if request.user.is_authenticated:
        if 'blog_id' in request.POST and 'title' in request.POST:
            try:
                b = Blog.get_by_id(request.POST['blog_id'])
            except:
                return apiRespond(400, msg='Blog not found')
            else:
                if b.author == request.user:
                    title = request.POST['title'].strip()
                    if len(title) > 2:
                        b.update_title(title)
                        return apiRespond(201, title=title)
                    else:
                        return apiRespond(400, msg='Title too short')
                else:
                    return apiRespond(400, msg='Access denied')
        else:
            return apiRespond(400, msg='Required fields missing')
    else:
        return apiRespond(401, msg='User not logged in')


@require_http_methods(["POST"])
def set_blog_img(request):
    if request.user.is_authenticated:
        if 'blog_id' in request.POST and 'img_url' in request.POST:
            try:
                b = Blog.get_by_id(request.POST['blog_id'])
            except:
                return apiRespond(400, msg='Blog not found')
            else:
                if b.author == request.user:
                    img_url = request.POST['img_url'].strip()
                    if len(img_url) > 2:
                        b.update_img(img_url)
                        return apiRespond(201, img_url=img_url)
                    else:
                        return apiRespond(400, msg='img_url too short')
                else:
                    return apiRespond(400, msg='Access denied')
        else:
            return apiRespond(400, msg='Required fields missing')
    else:
        return apiRespond(401, msg='User not logged in')


@require_http_methods(["POST"])
def publish_blog(request):
    if request.user.is_authenticated:
        if 'blog_id' in request.POST:
            try:
                b = Blog.get_by_id(request.POST['blog_id'])
            except:
                return apiRespond(400, msg='Blog not found')
            else:
                if b.author == request.user:
                    b.publish()
                    return apiRespond(201, is_published=b.is_published)
                else:
                    return apiRespond(400, msg='Access denied')
        else:
            return apiRespond(400, msg='Required fields missing')
    else:
        return apiRespond(401, msg='User not logged in')


@require_http_methods(["POST"])
def unpublish_blog(request):
    if request.user.is_authenticated:
        if 'blog_id' in request.POST:
            try:
                b = Blog.get_by_id(request.POST['blog_id'])
            except:
                return apiRespond(400, msg='Blog not found')
            else:
                if b.author == request.user:
                    b.unpublish()
                    return apiRespond(201, is_published=b.is_published)
                else:
                    return apiRespond(400, msg='Access denied')
        else:
            return apiRespond(400, msg='Required fields missing')
    else:
        return apiRespond(401, msg='User not logged in')


@require_http_methods(["POST"])
def delete_blog(request):
    if request.user.is_authenticated:
        if 'blog_id' in request.POST:
            try:
                b = Blog.get_by_id(request.POST['blog_id'])
            except:
                return apiRespond(400, msg='Blog not found')
            else:
                if b.author == request.user:
                    b.remove()
                    return apiRespond(201, removed=True)
                else:
                    return apiRespond(400, msg='Access denied')
        else:
            return apiRespond(400, msg='Required fields missing')
    else:
        return apiRespond(401, msg='User not logged in')


@require_http_methods(["POST"])
def set_blog_content(request):
    if request.user.is_authenticated:
        if 'blog_id' in request.POST and 'content' in request.POST:
            try:
                b = Blog.get_by_id(request.POST['blog_id'])
            except:
                return apiRespond(400, msg='Blog not found')
            else:
                if b.author == request.user:
                    b.update_content(request.POST['content'])
                    return apiRespond(201)
                else:
                    return apiRespond(400, msg='Access denied')
        else:
            return apiRespond(400, msg='Required fields missing')
    else:
        return apiRespond(401, msg='User not logged in')


def page404(request, exception=None):
    response = render(request, '404.html')
    response.status_code = 404
    return response
