import random
import string
import json
import requests
import httplib2
from flask import Flask, render_template, url_for, request
from flask import redirect, flash, jsonify, make_response
from sqlalchemy import create_engine
from db_setup import Base, User, Item, ItemCategory
from sqlalchemy.orm import sessionmaker
from flask import session as login_session

app = Flask(__name__)

# connect to db
engine = create_engine('sqlite:///item_catalog.db')
Base.metadata.bind = engine

Session = sessionmaker(bind=engine)
session = Session()

# redirect function


def redirect_url(default='home'):
    return request.args.get('next') or request.referrer or url_for(default)


# ------------------------------- CRUD Item -------------------------------
# show all category - JSON ENDPOINTS API
@app.route('/api/items/all/JSON')
def allItemsJson():
    items = session.query(Item).order_by(Item.id.desc())
    return jsonify(items=[i.serialize for i in items])


# Return particular item in particular category
@app.route('/api/categories/<int:category_id>/item/<int:item_id>/JSON')
def CategoryItemJson(category_id, item_id):
    if existsCategory('id', category_id) and existsItem('id', item_id):
        item = session.query(Item).filter_by(
            id=item_id, item_category_id=category_id).first()
        if item is not None:
            return jsonify(item=item.serialize)
        else:
            return jsonify(
                error='item {} does not belong to category {}.'
                .format(item_id, category_id))
    else:
        return jsonify(error='The item or the category does not exist.')


# Return all item in particular category
@app.route('/api/categories/<int:category_id>/items/JSON')
def CategoryAllItemJson(category_id):
    if existsCategory('id', category_id):
        item = session.query(Item).filter_by(
            item_category_id=category_id).first()
        if item is not None:
            return jsonify(item=item.serialize)
        else:
            return jsonify(error='Unable to reach that category item.')
    else:
        return jsonify(error='The category does not exist.')


# Create a new item.
@app.route("/item/new/", methods=['GET', 'POST'])
def createNewItem():
    if 'username' not in login_session:
        flash("Login to create new item.")
        return redirect(url_for('login'))
    elif request.method == 'POST':
        itemName = request.form['name']
        if existsItem('name', itemName):
            flash('The item already exists in the database!')
            return redirect(redirect_url())

        new_item = Item(
            title=itemName,
            description=request.form['description'],
            item_category_id=request.form['category_id'],
            author_id=login_session['user_id']
        )
        session.add(new_item)
        session.commit()
        flash('New item successfully created!')
        return redirect(url_for('home'))
    else:
        categories = session.query(ItemCategory).filter_by(
            user_id=login_session['user_id']).all()
        return render_template(
            'create-new-item.html',
            categories=categories
        )


# Edit existing item.
@app.route("/item/<int:item_id>/edit/", methods=['GET', 'POST'])
def editItem(item_id):
    if 'username' not in login_session:
        flash("Login to edit item.")
        return redirect(redirect_url('login'))

    if not existsItem('id', item_id):
        flash("Item is not existed")
        return redirect(redirect_url())

    item = session.query(Item).filter_by(id=item_id).first()
    if login_session['user_id'] != item.author_id:
        flash("You were not authorised to edit this item")
        return redirect(redirect_url('home'))

    if request.method == 'POST':
        if request.form['title']:
            item.name = request.form['title']
        if request.form['description']:
            item.description = request.form['description']
        if request.form['item_category_id']:
            item.category_id = request.form['item_category_id']
        session.add(item)
        session.commit()
        flash('Item successfully updated!')
        return redirect(url_for('edit_item', item_id=item_id))
    else:
        categories = session.query(ItemCategory).filter_by(
            user_id=login_session['user_id']).all()
        return render_template(
            'edit-item.html',
            item=item,
            categories=categories
        )


# Delete existing item.
@app.route("/item/<int:item_id>/delete/", methods='POST')
def deleteItem(item_id):
    if 'username' not in login_session:
        flash("Login to delete item")
        return redirect(redirect_url('login'))

    if not existsItem('id', item_id):
        flash("Unable to delete item")
        return redirect(redirect_url('home'))

    item = session.query(Item).filter_by(id=item_id).first()
    if login_session['user_id'] != item.user_id:
        flash("You were not authorised to delete this item.")
        return redirect(redirect_url('home'))

    if request.method == 'POST':
        session.delete(item)
        session.commit()
        flash("Item successfully deleted!")
        return redirect(redirect_url('home'))


# check category exist or not
def existsItem(attr, value):
    item = session.query(Item).filter(
        getattr(Item, attr) == value).first()
    if item is not None:
        return True
    else:
        return False


# ------------------------------ CRUD Category ---------------------------

# show all category - JSON ENDPOINTS API
@app.route('/api/categories/all/JSON')
def allCategoriesJson():
    categories = session.query(ItemCategory).all()
    return jsonify(categories=[i.serialize for i in categories])


# Add a new category.
@app.route("/category/new", methods=['GET', 'POST'])
def createNewCategory():
    if 'username' not in login_session:
        flash("Login to create new category")
        return redirect(url_for('login'))
    elif request.method == 'POST':
        categoryName = request.form['category-name']
        # validation category name
        if categoryName == '':
            flash('The category name field is required.')
            return redirect(redirect_url())

        # check category name is existed
        if not existsCategory('name', categoryName):
            flash('%s is already exists in categories.' % categoryName)
            return redirect(redirect_url())

        # insert new category
        new_category = ItemCategory(
            name=categoryName,
            user_id=login_session['user_id'])
        session.add(new_category)
        session.commit()
        flash('New category %s successfully created!' % categoryName)
        return redirect(redirect_url())
    else:
        return render_template('create-new-category.html')


# edit category
@app.route('/category/<int:category_id>/edit/', methods=['GET', 'POST'])
def editCategory(category_id):
    category = session.query(ItemCategory).filter_by(id=category_id).first()

    if 'username' not in login_session:
        flash("Login to edit category.")
        return redirect(redirect_url('login'))

    if not existsCategory('id', category_id):
        flash("Invalid category")
        return redirect(redirect_url())

    if login_session['user_id'] != category.author_id:
        flash("Your don't have permission to edit this category")
        return redirect(redirect_url('home'))

    if request.method == 'POST':
        categoryName = request.form['name']
        if categoryName:
            category.name = categoryName
            session.add(category)
            session.commit()
            flash('Category update successfully!')
            return redirect(url_for('show_items_in_category',
                                    category_id=category.id))
    else:
        return render_template('edit-category.html', category=category)


# check category exist or not
def existsCategory(attr, value):
    category = session.query(ItemCategory).filter(
        getattr(ItemCategory, attr) == value).first()
    if category is not None:
        return True
    else:
        return False


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=8080)
