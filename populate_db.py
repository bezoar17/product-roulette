import sqlite3
import random
import logging
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
	product_values=list()
	for row in reader:
		product_values.append((row['product_name'],row['persona'],row['trending']))

	db=sqlite3.connect('train.db')
	cursor=db.cursor()
	cursor.executemany('INSERT INTO product_info_table(product_name,persona,trending) VALUES (?,?,?)', product_values)
	db.commit()
	db.close()

	db=sqlite3.connect('test.db')
	cursor=db.cursor()
	cursor.executemany('INSERT INTO product_info_table(product_name,persona,trending) VALUES (?,?,?)', product_values)
	db.commit()
	cursor.execute('SELECT product_id,product_name FROM product_info_table')
	for i in cursor.fetchall():
		productids[i[1]]=i[0]
	db.commit()
	db.close()

def populate_trts():

	# populate the train and test db ,the user info and their likes go in 80:20 fashion
	global productids,useremailtoid,train_userids_back,test_userids_back
	
	reader = csv.DictReader(open('db/db_userinfo.csv'))
	all_users=list()
	
	for row in reader:
		all_users.append((row['user_id'],row['user_email'],row['persona']))
		useremailtoid[row['user_email']]=row['user_id']
	# all_users_safe=all_users
	random.shuffle(all_users) # comment this line for a fixed simulation of first 15 in training and last 5 in test set.
	train_userids=[i[0] for i in all_users[0:15]]
	test_userids=[i[0] for i in all_users[15:]]

	db=sqlite3.connect('train.db')
	cursor=db.cursor()
	cursor.executemany('INSERT INTO user_info_table(email_id,persona) VALUES (?,?)',[i[1:] for i in all_users[0:15]])
	db.commit()
	db.close()

	db=sqlite3.connect('test.db')
	cursor=db.cursor()
	cursor.executemany('INSERT INTO user_info_table(email_id,persona) VALUES (?,?)', [i[1:] for i in all_users[15:]])
	db.commit()
	db.close()

	db=sqlite3.connect('train.db')
	cursor=db.cursor()
	cursor.execute('SELECT user_id,email_id FROM user_info_table')
	
	for i in cursor.fetchall():
		train_userids_back[useremailtoid[i[1]]]=i[0]
	db.commit()
	db.close()

	db=sqlite3.connect('test.db')
	cursor=db.cursor()
	cursor.execute('SELECT user_id,email_id FROM user_info_table')
	
	for i in cursor.fetchall():
		test_userids_back[useremailtoid[i[1]]]=i[0]
	db.commit()
	db.close()
	
	reader = csv.DictReader(open('db/db_userinputs.csv'))
	train_userinputs=list()
	test_userinputs=list()

	for row in reader:
		if row['user_id'] in train_userids:
			train_userinputs.append((train_userids_back[row['user_id']],productids[row['product_name']],row['user_input']))
		elif row['user_id'] in test_userids:
			test_userinputs.append((test_userids_back[row['user_id']],productids[row['product_name']],row['user_input']))

	# push the datasets
	
	db=sqlite3.connect('train.db')
	cursor=db.cursor()
	cursor.executemany('INSERT INTO user_inputs_table(user_id,product_id,input_val) VALUES (?,?,?)', train_userinputs)
	db.commit()
	db.close()

	db=sqlite3.connect('test.db')
	cursor=db.cursor()
	cursor.executemany('INSERT INTO user_inputs_table(user_id,product_id,input_val) VALUES (?,?,?)', test_userinputs)
	db.commit()
	db.close()

def start():
	create_db('train')
	create_db('test')
	populate_products()
	populate_trts()

if __name__ == '__main__':
	start()

