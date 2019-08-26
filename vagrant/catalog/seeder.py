from db_setup import Base, User, Item, ItemCategory
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine


engine = create_engine('sqlite:///item_catalog.db',
                       connect_args={'check_same_thread': False})

# Bind the above engine to a session.
Session = sessionmaker(bind=engine)

# Create a Session object.
session = Session()

user1 = User(
    name='test01',
    email='test01.usery@gmail.com',
    profile_image=''
)

session.add(user1)
session.commit()

category1 = ItemCategory(
    name='Beds & Mattresses',
    users=user1
)

session.add(category1)
session.commit()

item1 = Item(
    title='Bed Frames',
    description='There are lots of beds, but feeling good when you wake up starts with finding the right one.',
    item_categories=category1,
    users=user1
)

session.add(item1)
session.commit()

print('Complete seed into database!')