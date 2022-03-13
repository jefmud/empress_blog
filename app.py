# Empress, a minimal blogging application
# based on the Minimus Framework by @jeffmuday
# Copyright (C) 2022 by Jeff Muday

from minimus import (Minimus, ClassView, render_template, parse_formvars,
                     Session, redirect, g, url_for, csrf_token, validate_csrf)
from minimus_users import (render_login, authenticate, initialize, 
                           CLIENT, user_services_cli)

from utils import validate_post

import sys

import pymongo

app = Minimus(__name__)
session = Session(app)

# initialize the default database
DB = 'blogs'

@app.before_request()
def before_request(env):
    session.connect()
    # pass session data to the template
    g.session = session.data
    if g.brand is None:
        # lookup blog title "brand identity" is no title is set
        brand = CLIENT[DB].idents.find_one()
        g.brand = brand

@app.route('/')
def index_view(env):
    """do the index view, renders all blog posts"""
    query = {'is_published': True}
    if g.session.get('username'):
        # if logged in, show all posts
        query = {}
    posts = CLIENT[DB].posts.find(query).sort('created_at', pymongo.DESCENDING)
    return render_template('clean-blog/index.html', posts=posts)


@app.route('/about')
def about_view(env):
    """show the about page"""
    return render_template('clean-blog/about.html')


@app.route('/contact')
def contact_view(env):
    """show the contact page"""
    return render_template('clean-blog/contact.html')


@app.route('/edit', methods=['GET', 'POST'])
@app.route('/post/<slug>/edit', methods=['GET', 'POST'])
class EditPostView(ClassView):
    """edit a post, use ClassView to handle both GET and POST"""
    def get(self, env, slug=None):
        # make sure user is logged in
        if session.data.get('username') is None:
            return redirect('/login')
        # get existing post by slug name
        post = CLIENT[DB].posts.find_one({'slug': slug})
        if post is None:
            # it's a new post, so make it blank
            post = {}
        fields = post
        # add a (valid) CSRF token
        fields['csrf_token'] = csrf_token(session)
        return render_template('utility/edit_post.html', fields=post)
    
    def post(self, env, slug=None):
        """save post"""
        # make sure user is logged in
        if session.data.get('username') is None:
            return redirect('/login')
        fields = parse_formvars(env)
        if validate_csrf(session, fields.get('csrf_token')):
            errors = validate_post(fields)          
            session.data['errors'] = errors
            session.commit()
            if errors == []:
                # if the post was marked to publish, publish it
                fields['is_published'] = fields.get('is_published','') == 'on'
                if slug is None:
                    # it's a new post, so insert it
                    CLIENT[DB].posts.insert_one(fields)
                else:
                    # else update it
                    CLIENT[DB].posts.update_one({'slug': slug}, {'$set': fields})
                return redirect("/post/" + fields.get('slug'))
        
        return render_template('utility/edit_post.html', fields=fields)

@app.route('/post/<slug>/delete', methods=['GET'])
def post_delete(env, slug):
    """delete a post"""
    if session.data.get('username') is None:
        return redirect('/login')
    
    post = CLIENT[DB].posts.find_one({'slug': slug})
    if post:
        CLIENT[DB].posts.delete_one({'slug': slug})
    
    return redirect('/')
    
@app.route('/post')
def post_general_view(env):
    """handle post LATEST view"""
    # get latest post (search in reverse chronological order)
    posts = CLIENT[DB].posts.find({'is_published':True}).sort('created_at', pymongo.DESCENDING)
    if posts.count() < 1:
        return render_template('clean-blog/404.html', post={})
        
    # get the first post
    post = posts.next()
    return redirect('/post/' + post['slug'])

@app.route('/post/<slug>')
def post_view(env, slug):
    """handle post view"""
    post = CLIENT[DB].posts.find_one({'slug': slug})
    if post is None:
        return render_template('clean-blog/404.html', post={})

    if post.get('image_url','') == '':
        post['image_url'] = '/static/clean-blog/assets/img/post-bg.jpg'
        
    if post.get('is_published', False) == False:
        if session.data.get('username') is None:
            return render_template('clean-blog/404.html', post={})
        #if session.data.get('username') != post.get('author', ''):
        #    return render_template('clean-blog/404.html', post={})
        
    return render_template('clean-blog/post.html', post=post)

@app.route('/identity', methods=['GET', 'POST'])
class IdentityView(ClassView):
    
    def get(self, env):
        """show the identity page"""
        if session.data.get('username') is None:
            return redirect('/login')

        fields = CLIENT[DB].idents.find_one()
        return render_template('utility/identity.html', fields=fields)
    
    def post(self, env):
        """save identity info"""
        if session.data.get('username') is None:
            return redirect('/login')
        
        fields = parse_formvars(env)
        CLIENT[DB].idents.update_one({}, {'$set': fields}, upsert=True)
        g.brand = CLIENT[DB].idents.find_one()
        return redirect('/')


@app.route('/login', methods=['GET', 'POST'])
class LoginView(ClassView):
    """handle login view, use ClassView to handle both GET and POST"""
    def get(self, env):
        return render_login()

    def post(self, env):
        fields = parse_formvars(env)
        if authenticate(fields.get('username'), fields.get('password')):
            session.data['username'] = fields.get('username')
            session.commit()
            return redirect('/')
        return render_login()


@app.route('/logout')
def logout_view(env):
    """handle logout view, very simply disables session"""
    session.clear()
    return redirect('/')

    
if __name__ == '__main__':
    initialize()
    if user_services_cli(sys.argv):
        # invoking user services on CLI if needed --createuser, --deleteuser, --listusers, etc.
        # this can be run when the app is running, or when the app is not running
        print('operation completed')
        sys.exit(0)

    app.run(server="paste")