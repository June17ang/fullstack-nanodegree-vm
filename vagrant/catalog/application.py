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


# ------------------------------ CRUD Category ---------------------------

# show all category - JSON ENDPOINTS API
@app.route('/api/categories/all/JSON')
def categories_json():
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
        category = session.query(ItemCategory).filter_by(
            name=categoryName).first()
        if not exists_category('name', categoryName):
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

    if not exists_category('id', category_id):
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
        return render_template('edit_category.html', category=category)


# check category exist or not
def exists_category(attr, value):
    category = session.query(ItemCategory).filter(
        getattr(ItemCategory, attr) == value).first()
    if category is not None:
        return True
    else:
        return False


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=8080)
