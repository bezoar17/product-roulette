import sqlite3
import random
import csv

productids=dict()
useremailtoid=dict()
train_userids_back=dict()
test_userids_back=dict()

def create_db(db_name):
	
	db=sqlite3.connect(db_name+'.db')
	cursor=db.cursor()
	#drop previous tables
	cursor.execute('''DROP TABLE IF EXISTS user_info_table''')
	cursor.execute('''DROP TABLE IF EXISTS product_info_table''')
	cursor.execute('''DROP TABLE IF EXISTS user_inputs_table''')
	db.commit()
	#creating 3 tables
	cursor.execute('''CREATE TABLE user_info_table(user_id INTEGER PRIMARY KEY, email_id TEXT unique, persona TEXT)''')
	cursor.execute('''CREATE TABLE product_info_table(product_id INTEGER PRIMARY KEY, product_name TEXT, persona TEXT,trending INTEGER)''')
	cursor.execute('''CREATE TABLE user_inputs_table(s_no INTEGER PRIMARY KEY, user_id INTEGER, product_id INTEGER, input_val INTEGER)''') 
	db.commit()
	db.close()
	
def populate_products():
	
	# get products in the product_values list 
	global productids
	reader = csv.DictReader(open('db/db_products.csv'))
	product_values=list()		# local variable
	for row in reader:
		product_values.append((row['product_name'],row['persona'],row['trending']))
	
	#add product info to train and test db
	insert_many_to_db('train.db','INSERT INTO product_info_table(product_name,persona,trending) VALUES (?,?,?)', product_values)
	insert_many_to_db('test.db','INSERT INTO product_info_table(product_name,persona,trending) VALUES (?,?,?)', product_values)
	
	db=sqlite3.connect('test.db')
	cursor=db.cursor()
	cursor.execute('SELECT product_id,product_name FROM product_info_table')			# build the product's name -> id dictionary
	for i in cursor.fetchall():
		productids[i[1]]=i[0]
	db.commit()
	db.close()

def populate_trts(train_set_size):

	global productids,useremailtoid,train_userids_back,test_userids_back
	
	reader = csv.DictReader(open('db/db_userinfo.csv'))
	all_users=list()	# list of tuple(id,email,persona) of user-info
	
	for row in reader:
		all_users.append((row['user_id'],row['user_email'],row['persona']))
		useremailtoid[row['user_email']]=row['user_id']
	
	random.shuffle(all_users) 		# randomize before parting the training and testing sets
	train_userids=[i[0] for i in all_users[0:train_set_size]]		# list of original user id's in training set
	test_userids=[i[0] for i in all_users[train_set_size:]]			# list of original user id's in training set

	insert_many_to_db('train.db','INSERT INTO user_info_table(email_id,persona) VALUES (?,?)',[i[1:] for i in all_users[0:train_set_size]])
	insert_many_to_db('test.db','INSERT INTO user_info_table(email_id,persona) VALUES (?,?)', [i[1:] for i in all_users[train_set_size:]])
	
	db=sqlite3.connect('train.db')
	cursor=db.cursor()
	cursor.execute('SELECT user_id,email_id FROM user_info_table')
	for i in cursor.fetchall():
		train_userids_back[useremailtoid[i[1]]]=i[0]			#  build the user's original id ->  training set id dictionary
	db.commit()
	db.close()

	db=sqlite3.connect('test.db')
	cursor=db.cursor()
	cursor.execute('SELECT user_id,email_id FROM user_info_table')
	for i in cursor.fetchall():
		test_userids_back[useremailtoid[i[1]]]=i[0]				#  build the user's original id ->  testing set id dictionary
	db.commit()
	db.close()
	
	reader = csv.DictReader(open('db/db_userinputs.csv'))
	train_userinputs=list()					# list of user inputs to go in training set
	test_userinputs=list()					# list of user inputs to go in testing set

	for row in reader:						# build the user inputs list to add to train and test db
		if row['user_id'] in train_userids:
			train_userinputs.append((train_userids_back[row['user_id']],productids[row['product_name']],row['user_input']))
		elif row['user_id'] in test_userids:
			test_userinputs.append((test_userids_back[row['user_id']],productids[row['product_name']],row['user_input']))

	# push the user inputs to train and test db
	insert_many_to_db('train.db','INSERT INTO user_inputs_table(user_id,product_id,input_val) VALUES (?,?,?)', train_userinputs)
	insert_many_to_db('test.db','INSERT INTO user_inputs_table(user_id,product_id,input_val) VALUES (?,?,?)', test_userinputs)
	
def start(test_set_size=5):
	create_db('train')
	create_db('test')
	populate_products()
	populate_trts(20-test_set_size)

def insert_many_to_db(db_name,sql_query,list_val):
	
	db=sqlite3.connect(db_name)
	cursor=db.cursor()
	cursor.executemany(sql_query,list_val)
	db.commit()
	db.close()
	
if __name__ == '__main__':
	start()
