from datetime import datetime
from main import app, db, Post, Contact

# Create tables
with app.app_context():

    print('Database connection successful .....')

    # db.create_all()
    # print("Tables created successfully or already exist.")

    # new_post = Post(title = 'post_2', content = 'content of second post', date = datetime.now())
    # db.session.add(new_post)
    # db.session.commit()
    # print("A new post has been added successfully ...")

    # posts = [
    #     Post(title = 'post_7', content = 'content of seventh post', date = datetime.now()),
    #     Post(title = 'post_8', content = 'content of eighth post', date = datetime.now()),
    #     Post(title = 'post_9', content = 'content of ninth post', date = datetime.now())
    # ]

    # db.session.add_all(posts)
    # db.session.commit()

    # print('Multiple posts have been added successfully')

    