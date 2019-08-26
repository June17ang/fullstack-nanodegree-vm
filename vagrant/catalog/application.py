import random
import string
import json
import requests
import httplib2
import datetime
from flask import Flask, render_template, url_for, request
from flask import redirect, flash, jsonify, make_response
from sqlalchemy import create_engine
from db_setup import Base, User, Item, ItemCategory
from sqlalchemy.orm import sessionmaker
from flask import session as login_session
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError

app = Flask(__name__)

# connect to db
engine = create_engine('sqlite:///item_catalog.db')
Base.metadata.bind = engine

Session = sessionmaker(bind=engine)
session = Session()

CLIENT_ID = json.loads(open('client_secret.json', 'r').read())[
    'web']['client_id']


# redirect function
def redirect_url(default='home'):
    return request.args.get('next') or request.referrer or url_for(default)


# ------------------------------ Login ------------------------------------

# Redirect to login page.
@app.route('/')
@app.route('/category')
@app.route('/item')
def home():
    categories = session.query(ItemCategory).all()
    items = session.query(Item).all()
    return render_template(
        'index.html', categories=categories, items=items)


# Create state token
@app.route('/login')
def login():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(32))
    login_session['state'] = state
    return render_template("login.html", STATE=state, client_id=CLIENT_ID)


# Connect to the Google Sign-in oAuth method.
@app.route('/google-login', methods=['POST'])
def google_login(request):
    token_request_uri = "https://accounts.google.com/o/oauth2/v2/auth"
    response_type = "code"
    redirect_uri = "http://localhost:5000/login/google/auth"
    scope = "https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/userinfo.email"
    url = "{token_request_uri}?response_type={response_type}&client_id={client_id}&redirect_uri={redirect_uri}&scope={scope}".format(
        token_request_uri = token_request_uri,
        response_type = response_type,
        client_id = CLIENT_ID,
        redirect_uri = redirect_uri,
        scope = scope)
    return url(url)


# Connect to the Google Sign-in oAuth method.
@app.route('/login/google/auth', methods=['POST'])
def googleConnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v2/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    google_id = credentials.id_token['sub']
    if result['user_id'] != google_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_google_id = login_session.get('google_id')
    if stored_access_token is not None and google_id == stored_google_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['google_id'] = google_id

    # Get user info.
    userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    # Assing Email as name if User does not have Google+
    if "name" in data:
        login_session['username'] = data['name']
    else:
        name_corp = data['email'][:data['email'].find("@")]
        login_session['username'] = name_corp
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # See if the user exists. If it doesn't, make a new one.
    user_id = getUserId(data["email"])
    if not user_id:
        user_id = createNewUser(login_session)
    login_session['user_id'] = user_id

    # Show a welcome screen upon successful login.
    output = ''
    output += '<h2>Welcome, '
    output += login_session['username']
    output += '!</h2>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px; '
    output += 'border-radius: 150px;'
    output += '-webkit-border-radius: 150px;-moz-border-radius: 150px;">'
    flash("You are now logged in as %s!" % login_session['username'])
    print("Done!")
    return output


# Disconnect Google Account.
def googleDisconnect():
    """Disconnect the Google account of the current logged-in user."""

    # Only disconnect the connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(
            json.dumps('Failed to revoke token for given user.'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response


# Log out the currently connected user.
@app.route('/logout')
def logout():
    """Log out the currently connected user."""

    if 'username' in login_session:
        googleDisconnect()
        del login_session['google_id']
        del login_session['access_token']
        del login_session['username']
        del login_session['email']
        del login_session['profile_image']
        del login_session['user_id']
        flash("You have been successfully logged out!")
        return redirect(redirect_url())
    else:
        flash("You were not logged in!")
        return redirect(redirect_url())


# Create new user.
def createNewUser(login_session):
    new_user = User(
        name=login_session['username'],
        email=login_session['email'],
        profile_image=login_session['picture']
    )
    session.add(new_user)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserId(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except BaseException:
        return None


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
            item_category_id=category_id).all()
        if item is not None:
            return jsonify(item=item.serialize)
        else:
            return jsonify(error='Unable to reach that category item.')
    else:
        return jsonify(error='The category does not exist.')


# View an item by its ID.
@app.route('/item/<int:item_id>/')
def viewItem(item_id):
    if existsItem('id', item_id):
        item = session.query(Item).filter_by(id=item_id).first()
        category = session.query(ItemCategory).filter_by(id=item.category_id).first()
        owner = session.query(User).filter_by(id=item.author_id).first()
        return render_template(
            "view-item.html",
            item=item,
            category=category,
            owner=owner
        )
    else:
        flash('We are unable to process your request right now.')
        return redirect(url_for('home'))


# Create a new item.
@app.route("/item/new/", methods=['GET', 'POST'])
def createNewItem():
    if 'username' not in login_session:
        flash("Login to create new item.")
        return redirect(url_for('login'))
    elif request.method == 'POST':
        itemTitle = request.form['title']
        if existsItem('name', itemTitle):
            flash('The item already exists in the database!')
            return redirect(redirect_url())

        new_item = Item(
            title=itemTitle,
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

        item.updated_at = datetime.datetime.utcnow
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
@app.route("/item/<int:item_id>/delete/", methods=['DELETE'])
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
@app.route("/category/create", methods=['GET', 'POST'])
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
            category.updated_at = datetime.datetime.utcnow()
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
    app.secret_key = 'secret key'
    app.config['SESSION_TYPE'] = 'filesystem'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
