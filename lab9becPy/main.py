"""импорт"""
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse

# Строка подключения к PostgreSQL
DATABASE_URL = "postgresql://postgres:1234@localhost:5432/lab9"

engine = create_engine(DATABASE_URL)
Base = declarative_base()


class User(Base):
    """класс пользователя"""
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    posts = relationship("Post", back_populates="user", cascade="all, delete-orphan")


class Post(Base):
    """класс пост"""
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String, nullable=False)
    content = Column(Text)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="posts")



def create_tables():
    Base.metadata.create_all(engine)


def get_db():
    db = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
    try:
        yield db
    finally:
        db.close()


def add_user(db, username, email, password):
    db_user = User(username=username, email=email, password=password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def add_post(db, title, content, user_id):
    db_post = Post(title=title, content=content, user_id=user_id)
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post


def get_all_users(db):
    return db.query(User).all()


def get_all_posts(db):
    return db.query(Post).all()


def get_posts_by_user(db, user_id):
    return db.query(Post).filter(Post.user_id == user_id).all()


def update_user_email(db, user_id, new_email):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user:
        db_user.email = new_email
        db.commit()
        db.refresh(db_user)
        return db_user
    return None


def update_post_content(db, post_id, new_content):
    db_post = db.query(Post).filter(Post.id == post_id).first()
    if db_post:
        db_post.content = new_content
        db.commit()
        db.refresh(db_post)
        return db_post
    return None


def delete_post(db, post_id):
    db_post = db.query(Post).filter(Post.id == post_id).first()
    if db_post:
        db.delete(db_post)
        db.commit()
        return True
    return False


def delete_user(db, user_id):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user:
        # Удаляем все посты пользователя
        db.query(Post).filter(Post.user_id == user_id).delete()

        # Удаляем пользователя
        db.delete(db_user)
        db.commit()
        return True
    return False

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def home():
    return HTMLResponse(content="""
    <html>
        <head><title>Home</title></head>
        <body>
        <h1>Welcome to the Simple CRUD App</h1>
        <p>Go to <a href="/users">Users</a> or <a href="/posts">Posts</a> to manage data.</p>
        </body>
    </html>
    """)


@app.get("/users", response_class=HTMLResponse)
async def read_users(db=Depends(get_db)):
    users = get_all_users(db)
    user_list = "".join(
        f"<li>ID: {user.id}, Username: {user.username}, Email: {user.email}</li>"
        for user in users
    )

    return HTMLResponse(content=f"""
    <html>
        <head><title>Users</title></head>
        <body>
        <h1>Users:</h1>
        <ul>{user_list}</ul>
        <p><a href="/add_user_form">Add User</a></p>
         <p><a href="/">Home</a></p>
        </body>
    </html>
    """)


@app.get("/add_user_form", response_class=HTMLResponse)
async def add_user_form():
    return HTMLResponse(content="""
    <html>
        <head><title>Add User</title></head>
        <body>
            <h1>Add New User</h1>
            <form method="post" action="/users/add">
                <label>Username: <input type="text" name="username"></label><br>
                <label>Email: <input type="email" name="email"></label><br>
                <label>Password: <input type="password" name="password"></label><br>
                <button type="submit">Add User</button>
            </form>
             <p><a href="/users">Back to Users</a></p>
        </body>
    </html>
    """)


@app.post("/users/add")
async def create_user(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db=Depends(get_db),
):
    user = add_user(db, username, email, password)
    if user:
         return HTMLResponse(content=f"""
            <html>
                <head><title>User Added</title></head>
                <body>
                <h1>User Added Successfully</h1>
                <p>User {user.username} has been added.</p>
                <p><a href="/users">Back to User List</a></p>
                </body>
            </html>
        """)
    raise HTTPException(status_code=400, detail="User not created")


@app.get("/users/{user_id}/edit_form", response_class=HTMLResponse)
async def edit_user_form(user_id: int, db=Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if user:
       return HTMLResponse(content=f"""
            <html>
                <head><title>Edit User</title></head>
                <body>
                    <h1>Edit User</h1>
                    <form method="post" action="/users/{user_id}/edit">
                        <label>Email: <input type="email" name="email" value="{user.email}"></label><br>
                        <button type="submit">Update User</button>
                    </form>
                    <p><a href="/users">Back to User List</a></p>
                </body>
            </html>
        """)
    raise HTTPException(status_code=404, detail="User not found")


@app.post("/users/{user_id}/edit")
async def update_user(user_id: int, email: str = Form(...), db=Depends(get_db)):
    user = update_user_email(db, user_id, email)
    if user:
         return HTMLResponse(content=f"""
            <html>
                <head><title>User Updated</title></head>
                <body>
                <h1>User Updated Successfully</h1>
                <p>User {user.username} has been updated.</p>
                <p><a href="/users">Back to User List</a></p>
                </body>
            </html>
        """)
    raise HTTPException(status_code=404, detail="User not found")

# Post routes
@app.get("/posts", response_class=HTMLResponse)
async def read_posts(db=Depends(get_db)):
    posts = get_all_posts(db)
    post_list = "".join(
        f"<li>ID: {post.id}, Title: {post.title}, Content: {post.content}, "
        f"User: {post.user.username if post.user else 'N/A'}</li>"
        for post in posts
    )

    return HTMLResponse(content=f"""
    <html>
        <head><title>Posts</title></head>
        <body>
        <h1>Posts:</h1>
        <ul>{post_list}</ul>
         <p><a href="/add_post_form">Add Post</a></p>
        <p><a href="/">Home</a></p>
        </body>
    </html>
    """)

@app.get("/add_post_form", response_class=HTMLResponse)
async def add_post_form(db=Depends(get_db)):
    users = get_all_users(db)
    user_options = "".join(f"<option value='{user.id}'>{user.username}</option>" for user in users)
    return HTMLResponse(content=f"""
    <html>
        <head><title>Add Post</title></head>
        <body>
            <h1>Add New Post</h1>
            <form method="post" action="/posts/add">
               <label>Title: <input type="text" name="title"></label><br>
                <label>Content: <textarea name="content"></textarea></label><br>
                <label>User:
                <select name="user_id">
                    {user_options}
                </select>
            </label>
                <button type="submit">Add Post</button>
            </form>
              <p><a href="/posts">Back to Post List</a></p>
        </body>
    </html>
    """)

@app.post("/posts/add")
async def create_post(
    title: str = Form(...),
    content: str = Form(...),
    user_id: int = Form(...),
    db=Depends(get_db),
):
    post = add_post(db, title, content, user_id)
    if post:
        return HTMLResponse(content=f"""
            <html>
                <head><title>Post Added</title></head>
                <body>
                <h1>Post Added Successfully</h1>
                <p>Post {post.title} has been added.</p>
                  <p><a href="/posts">Back to Post List</a></p>
                </body>
            </html>
        """)
    raise HTTPException(status_code=400, detail="Post not created")

@app.get("/posts/{post_id}/edit_form", response_class=HTMLResponse)
async def edit_post_form(post_id: int, db=Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id).first()
    if post:
       return HTMLResponse(content=f"""
            <html>
                <head><title>Edit Post</title></head>
                <body>
                    <h1>Edit Post</h1>
                    <form method="post" action="/posts/{post_id}/edit">
                        <label>Content: <textarea name="content">{post.content}</textarea></label><br>
                        <button type="submit">Update Post</button>
                    </form>
                     <p><a href="/posts">Back to Post List</a></p>
                </body>
            </html>
        """)
    raise HTTPException(status_code=404, detail="Post not found")


@app.post("/posts/{post_id}/edit")
async def update_post(
    post_id: int, content: str = Form(...), db=Depends(get_db)
):
    post = update_post_content(db, post_id, content)
    if post:
        return HTMLResponse(content=f"""
            <html>
                <head><title>Post Updated</title></head>
                <body>
                <h1>Post Updated Successfully</h1>
                <p>Post {post.title} has been updated.</p>
                  <p><a href="/posts">Back to Post List</a></p>
                </body>
            </html>
        """)
    raise HTTPException(status_code=404, detail="Post not found")

@app.get("/users/{user_id}/delete_form", response_class=HTMLResponse)
async def delete_user_form(user_id: int, db=Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        return HTMLResponse(content=f"""
            <html>
                <head><title>Delete User</title></head>
                <body>
                    <h1>Delete User</h1>
                    <p>Are you sure you want to delete user: <b>{user.username}</b>?</p>
                    <form method="post" action="/users/{user_id}/delete">
                        <button type="submit">Delete User</button>
                    </form>
                     <p><a href="/users">Back to User List</a></p>
                </body>
            </html>
        """)
    raise HTTPException(status_code=404, detail="User not found")
@app.post("/users/{user_id}/delete")
async def delete_user_post(user_id: int, db=Depends(get_db)):
    if delete_user(db, user_id):
        return HTMLResponse(content=f"""
            <html>
                <head><title>User Deleted</title></head>
                <body>
                    <h1>User Deleted Successfully</h1>
                    <p>User with ID {user_id} has been deleted.</p>
                      <p><a href="/users">Back to User List</a></p>
                </body>
            </html>
        """)
    raise HTTPException(status_code=404, detail="User not found")

@app.get("/posts/{post_id}/delete_form", response_class=HTMLResponse)
async def delete_post_form(post_id: int, db=Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id).first()
    if post:
        return HTMLResponse(content=f"""
            <html>
                <head><title>Delete Post</title></head>
                <body>
                    <h1>Delete Post</h1>
                    <p>Are you sure you want to delete post: <b>{post.title}</b>?</p>
                    <form method="post" action="/posts/{post_id}/delete">
                        <button type="submit">Delete Post</button>
                    </form>
                       <p><a href="/posts">Back to Post List</a></p>
                </body>
            </html>
        """)
    raise HTTPException(status_code=404, detail="Post not found")

@app.post("/posts/{post_id}/delete")
async def delete_post_post(post_id: int, db=Depends(get_db)):
    if delete_post(db, post_id):
        return HTMLResponse(content=f"""
            <html>
                <head><title>Post Deleted</title></head>
                <body>
                    <h1>Post Deleted Successfully</h1>
                     <p>Post with ID {post_id} has been deleted.</p>
                       <p><a href="/posts">Back to Post List</a></p>
                </body>
            </html>
        """)
    raise HTTPException(status_code=404, detail="Post not found")

if __name__ == "__main__":
    create_tables()
    db = next(get_db())
    """
    # создание пользователей и постов
    add_user (db, "Ivan", "iva@mail.ru","1234")
    add_user (db, "Vova", "vova@mail.ru","1234")
    add_post (db, "Post_Form_Ivan", "Hi I am Ivan","1")
    add_post (db, "Post_Form_Ivan_2", "Hi I am Ivan and it my second post","1")
    add_post (db, "Post_Form_Vova", "Hi I am Vova","2")
    delete_post(db, "2")
    # Обновление email пользователя Vova
    update_user_email(db, "2", "vovaUpdate@mail.ru" )

    # Обновление content поста Vova
    update_post_content(db, "1", "Hi I am Vova updated")
    # Вывод данных
    print ("All Users:")
    all_users = get_all_users(db)
    for user in all_users:
        print(f" ID: {user.id}, Username: {user.username}, Email:{user.email}")
    print("\nAll Posts:")
    all_posts = get_all_posts(db)
    for post in all_posts:
        print(f"  ID: {post.id}, Title: {post.title}, Content: {post.content}, User: {post.user.username}")
        
    user_posts = get_posts_by_user(db, 1)
    print("\nAll Ivan's Posts:")
    for post in user_posts:
        print(f"  ID: {post.id}, Title: {post.title}, Content: {post.content}")
    delete_user(db, "2")
    print("\nAll Users (after deletion):")
    all_users = get_all_users(db)
    for user in all_users:
        print(f"  ID: {user.id}, Username: {user.username}, Email: {user.email}")"""
    uvicorn.run(app, host="127.0.0.1", port=8000)
