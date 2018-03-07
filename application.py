from flask import Flask, url_for, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from elasticsearch import Elasticsearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import requests
import pymongo

application = Flask(__name__)
application.secret_key = '2515'
application.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://saumya1510:Password@saumya1510.chykpfxkowj1.us-east-1.rds.amazonaws.com/enerknol'
#application.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(application)

def getCollectionObject(collectionName):
    connection = pymongo.MongoClient("ds153978.mlab.com", 53978)
    print(connection)
    db = connection['enerknol']
    status = db.authenticate('admin', 'admin')
    print(status)
    if status == True:
        return db[collectionName]
    else:
        print("Authentication Error!")
        return 
    return

def connectToEs():
    aws_access_key = aws_access_key
    aws_secret_key = aws_secret_key
    region = 'us-east-1'
    service = 'es'
    awsauth = AWS4Auth(aws_access_key, aws_secret_key, region, service)
    host = HOST
    es = Elasticsearch(
        hosts = [{'host': host, 'port': 443}],
        http_auth = awsauth,
        use_ssl = True,
        verify_certs = True,
        connection_class = RequestsHttpConnection
        )
    return es

class User(db.Model):
    username = db.Column(db.String(25), primary_key = True)
    password = db.Column(db.String(20))
    def __init__(self, username, password):
        print(username)
        self.username = username
        self.password = password
        
@application.route('/details/<objectId>')
def getDetails(objectId):
    collection = getCollectionObject('userLoginDetails')
    #objectId = request.form['id']
    details = {}
    item = collection.find_one({'_id': int(objectId)})
    return render_template('details.html', item = item)

@application.route('/search', methods = ['GET', 'POST'])
def search():
    if request.method == 'GET':
        if 'username' in session:
            return render_template('search.html')
        else:
            return render_template('login.html')
    else:
        keywords = request.form['searchQuery']
        es = connectToEs()
        results = es.search(q = keywords)
        resultsList = []
        for item in results['hits']['hits']:
            result = {}
            result['id'] = item['_id']
            result['main_title'] = item['_source']['main_title']
            if 'title' in item['_source']:
                result['title'] = item['_source']['title']
            result['score'] = item['_score']
            resultsList.append(result)
        return render_template('results.html', results = resultsList)

@application.route('/register', methods = ['GET', 'POST'])
def register():
    if request.method == 'POST':
        #print(request.form['username'])
        try:
            newUser = User(username = request.form['username'], password = request.form['password'])
            db.session.add(newUser)
            db.session.commit()
            session['username'] = username
            return render_template('search.html')
        except Exception as e:
            assert e.__class__.__name__ == 'IntegrityError'
            return 'Use a different username'
        return 'Failed'
    else:
        return render_template('register.html')

@application.route('/login', methods = ['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    else:
        name = request.form['username']
        password = request.form['password']
        try:
            data = db.session.query(User).filter_by(username = name, password = password).first()
            if data is not None:
                session['username'] = name
                return render_template('search.html')
            else:
                return "Username doesn't exist or Password was incorrect"
        except:
            return "Something bad happened, I think"

@application.route('/logout')
def logout():
    session.pop('username', None)
    return render_template('login.html')

@application.route('/')
def home():
    if 'username' not in session:
        return render_template('login.html')
    else:
        return render_template('search.html')
    
if __name__ == '__main__':
    db.create_all()
    application.run()
    