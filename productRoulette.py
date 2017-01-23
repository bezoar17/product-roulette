import random
import sqlite3
import logging

# uncomment the 2 lines below to clear the log
# target=open('app.log','w')
# target.close()

'''Logging setup'''

logging.StreamHandler(stream=None)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# create a file handler
handler = logging.FileHandler('app.log')
handler.setLevel(logging.INFO)

# create a logging format
formatter = logging.Formatter('[%(asctime)s ms] %(levelname)s => %(funcName)s(Line:%(lineno)d) >> %(message)s')
handler.setFormatter(formatter)

# add the handlers to the logger
logger.addHandler(handler)

'''Logging setup'''

def productRoulette():

	''' FUNCTION DEFINITIONS START'''

	def showProduct(valid_choice):
		"""
		Show the name of current_product by a DB call
		Based on the success or failure of update_current_product() function call, 
		this function shows the name of product or sets current_product to None
		"""
		global logger
		nonlocal current_product,db,cursor
		logger.info('Fn: showProduct() called with valid_choice=%d',valid_choice)
		if valid_choice==0:
			logger.info('Returning to menu, user choice was invalid')
			print(current_product)
			logger.info('Fn: showProduct() exited')
			return
		if not update_current_product():			#true is function was a success(i.e returned 0)
			#get product name from db
			logger.info('DB Query: selecting product name for product_id %d',current_product)
			cursor.execute('''SELECT product_name FROM product_info_table WHERE product_id=?''',(current_product,))
			logger.info('DB Query: SUCCESS')
			pr_value=cursor.fetchone()[0]
			print(pr_value)
			logger.info('current product value set to %s',pr_value)
		else:
			#update product failed
			logger.info('Current product being set to None')
			current_product=None
		logger.info('Fn: showProduct() exited')
	
	def update_new_input():
		""" Add the liked/disliked item in the user's like/dislike set """
		global logger
		nonlocal current_set_l, current_set_d, current_product, menu_val,new_set_l,new_set_d
		logger.info('Fn: update_new_input() called with menu_val: %s',menu_val)
		if menu_val == 'y':
			current_set_l.add(current_product)
			new_set_l.add(current_product)
			logger.info('%d added to like set of current user, like set size:%d',current_product,len(current_set_l))
		elif menu_val == 'n':
			current_set_d.add(current_product)
			new_set_d.add(current_product)
			logger.info('%d added to dislike set of current user, dislike set size:%d',current_product,len(current_set_d))
		logger.info('Fn: update_new_input() exited')
	
	def push_user_data_to_db():
		"""
		Push the new like/dislike data collected for the current user to the DB
		This function is called just before exiting the application 
		"""
		# iterate over each in new like and dislike set and add to the likes table, only if any data has been collected
		global logger
		nonlocal db,cursor,user_id,new_set_l,new_set_d
		logger.info('Fn: push_user_data_to_db() called')
		
		if(len(new_set_l)+len(new_set_d)<1):
			logger.info('size of user like dislike set is 0')
			logger.info('Fn: push_user_data_to_db() exited')
			return
		else:
			# iterate over each in new like and dislike set and add to the likes table
			for elem in new_set_l:
				logger.info('DB Query: Inserting product:%d in new like set of user:%d',elem,user_id)
				cursor.execute('''INSERT INTO user_inputs_table(user_id,product_id,input_val) VALUES (?,?,1)''', (user_id,elem))
				logger.info('DB Query: SUCCESS')				
			
			for elem in new_set_d:
				logger.info('DB Query: Inserting product:%d in new dislike set of user:%d',elem,user_id)
				cursor.execute('''INSERT INTO user_inputs_table(user_id,product_id,input_val) VALUES (?,?,-1)''', (user_id,elem))
				logger.info('DB Query: SUCCESS')

			logger.info('DB COmmit: commiting to db')
			db.commit()
			logger.info('DB COmmit: SUCCESS')
		logger.info('Fn: push_user_data_to_db() exited')
	
	def get_user_id():
		"""
		Brief: Get the unique user_id and the like & dislike set of the user
		
		Description: 
		Initialize the user's like and dislike sets
		Check if user already exists , if NO: add user to DB,get unique id
		if YES: populate the user's like and dislike sets
		"""
		global logger
		nonlocal user_email,user_persona,user_id,current_set_l,current_set_d,db,cursor,new_set_l,new_set_d
		logger.info('Fn: get_user_id() called')
		
		current_set_l=set()
		new_set_l=set()
		current_set_d=set()
		new_set_d=set()
		logger.info('DB Query: Get id for email:%s and persona:%s',user_email,user_persona)
		cursor.execute('''SELECT user_id FROM user_info_table WHERE email_id=? AND persona=?''',(user_email,user_persona))
		# return will be None if user was not present and unique user_id if user was present
		logger.info('DB Query: SUCCESS')
		user_id=cursor.fetchone() 
		
		if user_id==None:
			#2) if user not present :: add user to db and get unique id
			#insert user
			logger.info('User id was not found, making another query')
			logger.info('DB Query: inserting user with email:%s and persona:%s',user_email,user_persona)
			cursor.execute('''INSERT INTO user_info_table(email_id,persona) VALUES(?,?)''',(user_email,user_persona))
			logger.info('DB Query: SUCCESS')
			
			logger.info('DB Query: getting id for user with email:%s and persona:%s',user_email,user_persona)
			cursor.execute('''SELECT user_id FROM user_info_table WHERE email_id=? AND persona=?''',(user_email,user_persona))
			logger.info('DB Query: SUCCESS')
			# or user_id=cursor.lastrowid , have to try 
			user_id=cursor.fetchone()[0]
			logger.info('User id fetched %d',user_id)
			logger.info('DB COmmit: commiting to db')
			db.commit()
			logger.info('DB COmmit: SUCCESS')
		else:
			#user already present ,update user's like and dislike profile
			# Same:		for elem in cursor.execute('''SELECT product_id FROM user_inputs_table WHERE user_id=? AND input_val=1''',(user_id,)):
			# 				current_set_l.add(elem[0])
			user_id=user_id[0] #fetchone returns a tuple, so in this case first element is what we need
			logger.info('User id fetched %d',user_id)
			logger.info('DB Query: Selecting the like set for user %d',user_id)
			cursor.execute('''SELECT product_id FROM user_inputs_table WHERE user_id=? AND input_val=1''',(user_id,))
			logger.info('DB Query: SUCCESS')
			current_set_l=set([i[0] for i in cursor.fetchall()])
			logger.info('Like set for user %d is %s',user_id,repr(current_set_l))
			logger.info('DB Query: Selecting the dislike set for user %d',user_id)
			cursor.execute('''SELECT product_id FROM user_inputs_table WHERE user_id=? AND input_val=-1''',(user_id,))
			logger.info('DB Query: SUCCESS')
			current_set_d=set([i[0] for i in cursor.fetchall()])
			logger.info('DisLike set for user %d is %s',user_id,repr(current_set_d))
		logger.info('Fn: get_user_id() exited')
		
	def update_current_product():
		"""
		Returns 0 for a successful attempt, else returns 1 and prints the error message
		"""
		global logger
		nonlocal current_product,n_users,n_users_dset,n_users_jset,n_users_lset,current_set_l,current_set_d
		nonlocal trending_set,random_set
		logger.info('Fn: update_current_product() called')
		
		if len(n_users) <1 :
			#show trending products
			logger.info('No previous dataset of users,show trending products')
			probable_set=set((trending_set - (current_set_d | current_set_l)))
			logger.info('Probable set is %s',repr(probable_set))
			if len(probable_set) <1:
				print('Phew!! we are all exhausted here, thank you for your inputs. See you next time.')
				logger.info('Fn: update_current_product() exited with return value 1')
				return 1
			else:
				current_product=random.sample(probable_set,1)[0]
				logger.info('current product value is %d',current_product)
				logger.info('Fn: update_current_product() exited with return value 0')
				return 0
		else:
			#prev data is present, if user input is more than 2
			if (len(current_set_d)+len(current_set_l)) > 2:
				#the user has put in atleast 2 inputs till now
				logger.info('user input is greater than 2. calculating similarity values')
				for elem in n_users:
					calc_val=0					
					# jaccard index calculation
					calc_val+= len(n_users_lset[elem] & current_set_l)
					calc_val+= len(n_users_dset[elem] & current_set_d)
					logger.info('The agreement total for user %d is %d',elem,calc_val)
					calc_val-= len(n_users_lset[elem] & current_set_d)
					calc_val-= len(n_users_dset[elem] & current_set_l)
					logger.info('The numerator value for user %d is %d',elem,calc_val)
					logger.info('The denominator value for user %d is %d',elem,(len(current_set_d)+len(current_set_l)))
					calc_val/= (len(current_set_d)+len(current_set_l))
					logger.info('The similarity value for user %d is %.4f',elem,calc_val)
					n_users_jset[elem]=calc_val;

				#find product value
				#for all nearest neighbours in descending order of similarity index
				nearest_order=sorted(n_users_jset, key=n_users_jset.get,reverse=True)
				logger.info('Nearest users order is %s',repr(nearest_order))
				for elem in nearest_order:
					#try their like set
					probable_set=set((n_users_lset[elem] - (current_set_d | current_set_l)))
					logger.info('Probable set with user %d is %s',elem,repr(probable_set))
					if len(probable_set)>0:
						current_product=random.sample(probable_set,1)[0]
						logger.info('current_product is set to %d',current_product)
						logger.info('Fn: update_current_product() exited with return value 0')
						return 0
				#if reached here, means nested loop anywhere we could not find a product,show user more products from the trending and random set 
				# for staring users very low predictive products will be shown
				# show a random product to build user profile
				logger.info('NOW showing random product, no user product matched')
				probable_set=set((random_set - (current_set_d | current_set_l)))
				logger.info('Probable set for random product is %s',repr(probable_set))
				if len(probable_set) <1:
					print('Phew!! we are all exhausted here, thank you for your inputs. See you next time.')
					logger.info('random probable set size was less than 1')
					logger.info('Fn: update_current_product() exited with return value 1')
					return 1
				else:
					current_product=random.sample(probable_set,1)[0]
					logger.info('current_product is set to %d',current_product)
					logger.info('Fn: update_current_product() exited with return value 0')
					return 0
			else:
				# show a random product to build user profile
				logger.info('NOW showing random product as user inputs were not enough')
				probable_set=set((random_set - (current_set_d | current_set_l)))
				logger.info('Probable set for random product is %s',repr(probable_set))
				if len(probable_set) <1:
					print('Phew!! we are all exhausted here, thank you for your inputs. See you next time.')
					logger.info('random probable set size was less than 1')
					logger.info('Fn: update_current_product() exited with return value 1')
					return 1
				else:
					current_product=random.sample(probable_set,1)[0]
					logger.info('current_product is set to %d',current_product)
					logger.info('Fn: update_current_product() exited with return value 0')
					return 0
		logger.info('Fn: update_current_product() exited with return value None')
				
	def populate_previous_data():
		""" 
		Get the list of previous users, their like/dislike set and populate trending and random sets
		"""
		global logger
		nonlocal db,cursor,n_users_lset,n_users_dset,n_users_jset,n_users,trending_set,user_persona,random_set,user_id
		logger.info('Fn: populate_previous_data() called')
				
		n_users_lset=dict()
		n_users_dset=dict()
		n_users_jset=dict()
		n_users=list()
		trending_set=set()
		random_set=set()
		#true_sample_set=set()

		#populate the trending set
		logger.info('DB Query: Selecting trending products for persona:%s',user_persona)
		cursor.execute('''SELECT product_id FROM product_info_table WHERE persona=? AND trending=1''',(user_persona,))
		logger.info('DB Query: SUCCESS')
		trending_set=set([i[0] for i in cursor.fetchall()])
		logger.info('Trending set LEN:%d and set is :%s',len(trending_set),repr(trending_set))

		#populate the random_set , try last n modified and user random from python
		logger.info('DB Query: Selecting maximum 15 random products for persona:%s',user_persona)
		cursor.execute('''SELECT product_id FROM product_info_table WHERE persona=? ORDER BY RANDOM() LIMIT 15''',(user_persona,))
		logger.info('DB Query: SUCCESS')
		random_set=set([i[0] for i in cursor.fetchall()])
		logger.info('Random set LEN:%d and set is :%s',len(random_set),repr(random_set))

		#populate truesampleset
		# true_sample_set=set(random.sample(trending_set | random_set,10))

		#get list of previous users
		logger.info('DB Query: Selecting all previous users for persona:%s',user_persona)
		cursor.execute('''SELECT user_id FROM user_info_table WHERE persona=?''',(user_persona,))
		logger.info('DB Query: SUCCESS')
		n_users=[i[0] for i in cursor.fetchall()] # converting [(1,), (2,), (3,)] to [1, 2, 3]
		n_users.remove(user_id)
		logger.info('Users are LEN:%d and list is :%s',len(n_users),repr(n_users))

		#if no users found, exit 
		if len(n_users)<1:
			print('Looks like you are first in this category!!')
			logger.info('No previous users')
			logger.info('Fn: populate_previous_data() exited')
			return
		#iterate and populate user's like and dislike sets
		logger.info('Starting selection of all users like and dislike sets')
		for elem in n_users:
			#populate like set
			logger.info('DB Query: Fetching like set of user %d',elem)
			cursor.execute('''SELECT product_id FROM user_inputs_table WHERE user_id=? AND input_val=1''',(elem,))
			logger.info('DB Query: SUCCESS')
			n_users_lset[elem]=set([i[0] for i in cursor.fetchall()])
			logger.info('Like set of user %d is of LEN:%d and set is :%s',elem,len(n_users_lset[elem]),repr(n_users_lset[elem]))
			
			#populate dislikes set
			logger.info('DB Query: Fetching dislike set of user %d',elem)
			cursor.execute('''SELECT product_id FROM user_inputs_table WHERE user_id=? AND input_val=-1''',(elem,))
			logger.info('DB Query: SUCCESS')
			n_users_dset[elem]=set([i[0] for i in cursor.fetchall()])
			logger.info('disLike set of user %d is of LEN:%d and set is :%s',elem,len(n_users_dset[elem]),repr(n_users_dset[elem]))
			#initialize the similarity index value
			n_users_jset[elem]=None
		logger.info('Fn: populate_previous_data() exited')

	''' FUNCTION DEFINITIONS END'''

	#  START of APPLICATION
	global logger,logging
	logger.info('Application Started')
	print("Welcome to Product Roulette")
	#connect to db
	logger.info('Connecting to db') 
	db=sqlite3.connect('example.db')
	cursor=db.cursor()
	logger.info('Connected to db')
	#define and declare the set values
	current_set_l=None
	new_set_l=None
	current_set_d=None
	new_set_d=None
	user_id=None
	current_product=None
	n_users=None
	n_users_lset=None
	n_users_dset=None
	n_users_jset=None
	trending_set=None
	random_set=None
	# true_sample_set=None  # for diversity

	logger.info('Taking user input')
	#get user input
	user_email=input('Enter your email-id : ')
	user_persona=input('Enter your persona : ')
	logger.info('User email:\'%s\' and persona:\'%s\'',user_email,user_persona)
	
	get_user_id()
	populate_previous_data()
	valid_choice=1
	while(1):
		showProduct(valid_choice)
		#if error happened in showProduct,current_product is set to none
		if current_product == None:
			logger.info('current_product was set to None')
			push_user_data_to_db()
			break
		logger.info('Product shown is :%d',current_product)
		menu_val=input('Press \'y\' if you like product, \'n\' if you don;t like the product and \'e\' to exit application : ')
		if(menu_val =='e'):
			logger.info('User entered exit command')
			logger.info('User entered valid choice')
			valid_choice=1
			push_user_data_to_db()
			break
		elif(menu_val =='y' or menu_val =='n'):
			logger.info('User entered valid choice')
			valid_choice=1
			update_new_input()
		else:
			logger.info('User entered invalid choice')
			valid_choice=0
			print('Please enter a valid choice')
	logger.info('Exiting application')
	print('See you later! Alligator!')
	db.commit() #make sure any pending transactions are comitted
	db.close() #close db
	logger.info('DB committed and closed')
	logger.info('Exited application')
	logging.shutdown()
	return
	#  END of APPLICATION

if __name__ == '__main__':
	productRoulette()