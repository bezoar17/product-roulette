import sqlite3
import random
import logging

def create_db():
	db=sqlite3.connect('example.db')
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

def populate_val():
	db=sqlite3.connect('example.db')
	cursor=db.cursor()
	#put in values
	product_values = [('Github', 'Developer', 1),
				  ('Bitbucket', 'Developer', 1),
				  ('Perforce', 'Developer', 0),
				  ('Sublime Text', 'Developer', 1),
				  ('Atom', 'Developer', 0),
				  ('Vim', 'Developer', 1),
				  ('Xcode', 'Developer', 0),
				  ('RStudio', 'Developer', 0),
				  ('Cloud9', 'Developer', 0),
				  ('Koding', 'Developer', 1),
				  ('Unity', 'Developer', 0),
				  ('ImpactJS', 'Developer', 1),
				  ('FMOD', 'Developer', 0),
				  ('Sidekiq Pro', 'Developer', 1),
				  ('jQuery', 'Developer', 1),
				  ('Underscore.js', 'Developer', 0),
				  ('OpenGrok', 'Developer', 1),
				  ('Source Insight', 'Developer', 0),
				  ('FileZilla', 'Developer', 0),
				  ('MySQL', 'Developer', 1),
				  ('PostgreSQL', 'Developer', 0),
				  ('Amazon RDS', 'Developer', 0),
				  ('MongoDB', 'Developer', 1),
				  ('Neo4j', 'Developer', 0),
				  ('Apache Maven', 'Developer', 1),
				  ('CMake', 'Developer', 0),
				  ('Apache Ant', 'Developer', 1),
				  ('Microsoft Azure', 'Developer', 1),
				  ('Amazon EC2', 'Developer', 1),
				  ('DigitalOcean', 'Developer', 0),
				  ('WordPress', 'Developer', 0),
				  ('Medium', 'Developer', 1),
				  ('Bootstrap', 'Developer', 0),
				  ('Redis', 'Developer', 1),]				  
	cursor.executemany('INSERT INTO product_info_table(product_name,persona,trending) VALUES (?,?,?)', product_values)
	db.commit()
	db.close()

if __name__ == '__main__':
	create_db()
	populate_val()

