#! python3
from flask import Flask, render_template,g,session,abort
from config import DevConfig
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy import func
from flask_wtf import Form
from wtforms import StringField, TextAreaField
from wtforms.validators import DataRequired,Length
from flask.views import View
app=Flask(__name__)
app.config.from_object(DevConfig)
db=SQLAlchemy(app)

if __name__=='__main__':
    app.run()
class User(db.Model):
    id=db.Column(db.Integer(),primary_key=True)
    username=db.Column(db.String(255))
    password=db.Column(db.String(255))
    posts = db.relationship(
        'Post',
        backref='user',
        lazy='dynamic'
    )

tags=db.Table('post_tags',
     db.Column('post_id',db.Integer,db.ForeignKey('post.id')),
     db.Column('tag_id',db.Integer,db.ForeignKey('tag.id'))
)
class Post(db.Model):
    id=db.Column(db.Integer(),primary_key=True)
    title=db.Column(db.String(255))
    text=db.Column(db.Text())
    publish_date=db.Column(db.DateTime())
    comments=db.relationship(
       'Comment',
       backref='post',
       lazy='dynamic'
    )
    user_id=db.Column(db.Integer(),db.ForeignKey('user.id'))
    tags=db.relationship(
       'Tag',
       secondary=tags,
       backref=db.backref('posts',lazy='dynamic')
    )

    def __init__(self,title):
       self.title=title

    def __repr__(self):
        return "<Post '{}'>".format(self.title)


class Comment(db.Model):
    id=db.Column(db.Integer(),primary_key=True)
    name=db.Column(db.String(255))
    text=db.Column(db.Text())
    date=db.Column(db.DateTime())
    post_id=db.Column(db.Integer(),db.ForeignKey('post.id'))

    def __repr__(self):
        return "<Comment '{}'>".format(self.text[:15])

class Tag(db.Model):
     id=db.Column(db.Integer(),primary_key=True)
     title=db.Column(db.String(255))

     def __init__(self, title):
         self.title=title

     def __repr__(self):
         return "<Tag '{}'>".format(self.title)

class CommentForm(Form):
     name=StringField(
         'Name',
         validators=[DataRequired(),Length(max=255)]
     )
     text=TextAreaField(u'Command',validators=[DataRequired()])

def sidebar_data():
     recent=Post.query.order_by(
         Post.publish_date.desc()
     ).limit(5).all()
     top_tags=db.session.query(
         Tag, func.count(tags.c.post_id).label('total')
     ).join(
         tags
     ).group_by(Tag).order_by('total Desc').limit(5).all()

     return recent, top_tags

class GenericView(View):
    methods=['GET','POST']

    def __init__(self,template):
        self.template=template
        super(GenericView,self).__init__()

    def dispatch_request(self):
        if request.method=='GET':
             return render_template(self.template)
        elif request.method=='POST':
             app.add_url_rule(
               '/',view_func=GenericView.as_view(
                   'home',template='home.html'
               )
             )
    
@app.route('/')
@app.route('/<int:page>')
def home(page=1):
    posts=Post.query.order_by(
       Post.publish_date.desc()
    ).paginate(page, 10)
    recent, top_tags = sidebar_data()


    return render_template(
         'home.html',
         posts=posts,
         recent=recent,
         top_tags=top_tags
     )

@app.route('/post/<int:post_id>')
def post(post_id):
    post=Post.query.get_or_404(post_id)
    tags=post.tags
    comment=post.comments.order_by(Comment.date.desc()).all()
    recent, top_tags = sidebar_data()


    return render_template(
         'post.html',
         post=post,
         tags=tags,
         comments=comments,
         recent=recent,
         top_tags=top_tags
     )

@app.route('/tag/<string:tag_name>')
def tag(tag_name):
    tag=Tag.query.filter_by(title=tag_name).first_or_404()
    posts=tag.posts.order_by(
       Post.publish_date.desc()
    ).all()
    recent, top_tags = sidebar_data()


    return render_template(
         'tag.html',
         tag=tag,
         posts=posts,
         recent=recent,
         top_tags=top_tags
     )

@app.route('/user/<string:username>')
def user(username):
    user=User.query.filter_by(username=username).first_or_404()
    posts=user.posts.order_by(
       Post.publish_date.desc()
    ).all()
    recent, top_tags = sidebar_data()


    return render_template(
         'user.html',
         user=user,
         posts=posts,
         recent=recent,
         top_tags=top_tags
     )

@app.route('/post/<int:post_id>', methods=('GET','POST'))
def post1(post_id):
   form = CommentForm()
   if form.validate_on_submit():
      new_comment=Comment()
   new_comment.name=form.name.data
   new_comment.text=form.text.data
   new_comment.post_id=post_id
   new_comment.date=datetime.datetime.now()
   db.session.add(new_comment)
   db.session.commit()
   post=Post.query.get_or_404(post_id)
   tags=post.tags
   comments=post.comments.order_by(Comment.date.desc()).all()
   recent,top_tags=sidebar_data()


   return render_template(
      'post.html',
      post=post,
      tags=tags,
      comments=comments,
      recent=recent,
      top_tags=top_tags,
      form=form
   )

@app.before_request
def before_request():
    if'user_id' in session:
        g.user=User.query.get(session['user_id'])

@app.route('/restricted')
def admin():
    if g.user is None:
        abort(403)
    return render_template('admin.html')

@app.errorhandler(404)
def page_not_found(error):
    return render_template('page_not_found.html'),404
