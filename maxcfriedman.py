import cgi
import datetime
import logging
import os
import re
import urllib
import webapp2

from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext.webapp import template

class Project(db.Model):
  # Ancestor = Author ID
  author_id   = db.StringProperty()
  date        = db.DateTimeProperty(auto_now=True)
  content     = db.TextProperty()
  name        = db.StringProperty()


def get_user():
  return users.get_current_user()

def login(handler):
  handler.redirect(users.create_login_url(handler.request.uri))

def user_key():
  return db.Key.from_path('User', get_user().user_id())

def get_proj(name):
  if not name:
    return None
  q = Project.all()
  q.ancestor(user_key())
  q.filter('author_id = ', get_user().user_id())
  q.filter('name = ', name)
  return q.get()


class Menu(webapp2.RequestHandler):
  # List current projects. Name, Edit, Run
  # + a form to create a new project
  def get(self):
    user = get_user()
    if not user: return login(self)

    projects = Project.all()
    projects.ancestor(user_key())
    projects.filter('author_id = ', user.user_id())
    projects.order('-date');

    if projects == None:
      projects = []

    template_values = {'projects': list(projects)}
    path = os.path.join(os.path.dirname(__file__), 'menu.html')
    self.response.out.write(template.render(path, template_values))

  # Make a new project then redirect back to the menu
  def post(self):
    user = get_user()
    if not user: return login(self)

    proj_name = self.request.get('n')
    action = self.request.get('a')

    if (action == 'n') {
      if re.match('^[a-zA-Z0-9._-]+$', proj_name) == None:
        self.redirect('/')

      if "\n" in proj_name or "\r" in proj_name:
        self.redirect('/')

      if get_proj(proj_name):
        self.redirect('/')

      proj = Project(parent=user_key())
      proj.author_id = str(user.user_id())
      proj.content = ''
      proj.name = proj_name
      proj.put()

      self.redirect('/')
    }


class Edit(webapp2.RequestHandler):
  def get(self):
    user = get_user()
    if not user: return login(self)

    proj_name = re.search('/~(.*)$', urllib.unquote(self.request.url)).group(1)
    proj = get_proj(proj_name)

    if proj == None:
      self.redirect('/')
      return

    template_values = {'project': proj}
    path = os.path.join(os.path.dirname(__file__), 'edit.html')
    self.response.out.write(template.render(path, template_values))

  def post(self):
    user = get_user()
    if not user: return login(self)

    proj_name = re.search('/~(.*)$', urllib.unquote(self.request.url)).group(1)
    proj = get_proj(proj_name)
    proj.content = self.request.get('content')
    proj.put()


class Run(webapp2.RequestHandler):
  def get(self):
    user = get_user()
    if not user: return login(self)

    proj_name = self.request.uri.split('/')[-1]
    proj = get_proj(proj_name)
    if not proj:
      self.redirect('/')
      return

    self.response.out.write(proj.content)


app = webapp2.WSGIApplication([('/', Menu),
                               ('/~.*', Edit),
                               ('/.*', Run)],
                              debug=True)
