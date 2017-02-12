import random
import sqlite3
import logging

# uncomment the 2 lines below to clear the log
target=open('app.log','w')
target.close()

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

''' GLOBALS FOR MODULE '''

current_set_l=None
new_set_l=None
current_set_d=None
new_set_d=None
user_id=None
user_email=None
user_persona=None
current_product=None
current_product_name=None
n_users=None
n_users_lset=None
n_users_dset=None
n_users_jset=None
trending_set=None
fallback_set=None
valid_choice=None
menu_val=None
db=None
cursor=None
all_suggestions=None

''' GLOBALS FOR MODULE '''

''' FUNCTION DEFINITIONS START'''

def showProduct():
	"""
	Brief: Call update on current_product and then show the name of current_product
	
	Args: None
	
	Description: 
		If function is called with valid_choice=0(happens after wrong user input)
		the function just shows the name for the current_product(id)

		When called with valid_choice=1, it calls update_current_product().
		IF the update function is successful,it prints the name of current_product
		ELSE sets current_product=None
	"""
	global logger
	global current_product,db,cursor,current_product_name,all_suggestions
	logger.info('Fn: showProduct() called with valid_choice=%d',valid_choice)
	
	if valid_choice==0:
		logger.info('Returning to menu, user choice was invalid')
		# print(current_product_name)
		logger.info('Fn: showProduct() exited')
		return
	
	if not update_current_product():			#true if function was a success(i.e returned 0)
		#get product name from db
		logger.info('DB Query: selecting product name for product_id %d',current_product)
		cursor.execute('''SELECT product_name FROM product_info_table WHERE product_id=?''',(current_product,))
		logger.info('DB Query: SUCCESS')
		
		current_product_name=cursor.fetchone()[0]
		all_suggestions.add(current_product)
		# print(current_product_name)
		logger.info('current product value set to %s',current_product_name)
	else:
		#update product failed
		logger.info('Current product being set to None')
		current_product=None
		current_product_name=None
	logger.info('Fn: showProduct() exited')

def update_new_input():
	""" Add the liked/disliked item in the user's like/dislike set """
	global logger
	global current_set_l, current_set_d, current_product, menu_val,new_set_l,new_set_d
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
	"""	Push the new like/dislike data collected for the current user to the DB	"""
	global logger
	global db,cursor,user_id,new_set_l,new_set_d
	logger.info('Fn: push_user_data_to_db() called')
	
	# if no data has been collected,exit 
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

		logger.info('DB Commit: commiting to db')
		db.commit()
		logger.info('DB Commit: SUCCESS')
	logger.info('Fn: push_user_data_to_db() exited')

def get_user_id():
	"""
	Brief: Get the unique user_id and the like & dislike set of the user
	
	Description:
		If user_persona is not None(indicates user has to be added to DB) when this function is called,
		the user is added to the DB and unique user id is fetched.

		If user_persona is None(indicates user has to be checked in DB) when this function is called,
		user email is checked in DB, if not found user_id is set to None and function returns.
		and if found, the like & dislike set for the user are also updated from DB.
	"""
	global logger
	global user_email,user_persona,user_id,current_set_l,current_set_d,db,cursor,new_set_l,new_set_d
	current_set_l=set()
	new_set_l=set()
	current_set_d=set()
	new_set_d=set()

	logger.info('Fn: get_user_id() called')
	if user_persona == None:
		logger.info('Checking if user exists')
		
		logger.info('DB Query: Select user id and persona for email : %s',user_email)
		cursor.execute('''SELECT user_id,persona FROM user_info_table WHERE email_id=?''',(user_email,))
		user_selection=cursor.fetchone()
		logger.info('DB QUery: Success, selection is %s',repr(user_selection))
		
		if user_selection==None:
			logger.info('User was not found, set user_id to None and exit')
			user_id=None
			logger.info('Fn: get_user_id() exited')
			return 
		else:
			#user already present ,update user's like and dislike profile
			user_id=user_selection[0] #fetchone returns a tuple, so in this case first element is what we need
			user_persona=user_selection[1]
			logger.info('User found in db with id %d and persona:%s',user_id,user_persona)
			
			#like set
			logger.info('DB Query: Selecting the like set for user %d',user_id)
			cursor.execute('''SELECT product_id FROM user_inputs_table WHERE user_id=? AND input_val=1''',(user_id,))
			logger.info('DB Query: SUCCESS')
			current_set_l=set([i[0] for i in cursor.fetchall()])
			logger.info('Like set for user %d is %s',user_id,repr(current_set_l))
			
			#dislike set
			logger.info('DB Query: Selecting the dislike set for user %d',user_id)
			cursor.execute('''SELECT product_id FROM user_inputs_table WHERE user_id=? AND input_val=-1''',(user_id,))
			logger.info('DB Query: SUCCESS')
			current_set_d=set([i[0] for i in cursor.fetchall()])
			logger.info('DisLike set for user %d is %s',user_id,repr(current_set_d))

	else:
		logger.info('Adding new user to user info table')
		
		logger.info('DB Query : Insert user with email: %s and persona :%s',user_email,user_persona)
		cursor.execute('''INSERT INTO user_info_table(email_id,persona) VALUES(?,?)''',(user_email,user_persona))
		logger.info('DB Query: Success')
		
		logger.info('DB Query: Select the user id form the user info table')
		cursor.execute('''SELECT user_id FROM user_info_table WHERE email_id=? AND persona=?''',(user_email,user_persona))
		user_id=cursor.fetchone()[0]
		logger.info('DB Query: Success , user id is %d',user_id)
		
		db.commit()
		logger.info('DB Commit:Successful')
	logger.info('Fn: get_user_id() exited')

def update_current_product():
		return trial4()

def populate_previous_data():
		""" 
		Get the list of previous users, their like/dislike set and populate trending and random sets
		"""
		global logger
		global db,cursor,n_users_lset,n_users_dset,n_users_jset,n_users,trending_set,user_persona,fallback_set,user_id
		global n_products,n_pr_dset,n_pr_pval,n_pr_lset,all_suggestions
		logger.info('Fn: populate_previous_data() called')
				
		# users data
		n_users_lset=dict()
		n_users_dset=dict()
		n_users_jset=dict()
		n_users=list()
		
		n_pr_lset=dict()
		n_pr_dset=dict()
		n_pr_pval=dict()
		n_products=list()

		trending_set=set()
		fallback_set=set()
		all_suggestions=set()
		#true_sample_set=set()
		
		#get list of previous products,trending and random sets
		logger.info('DB Query: Selecting all previous products for persona:%s',user_persona)
		cursor.execute('''SELECT product_id,trending FROM product_info_table WHERE persona=?''',(user_persona,))
		logger.info('DB Query: SUCCESS')
		n_products=[i[0] for i in cursor.fetchall()] # converting [(1,), (2,), (3,)] to [1, 2, 3]
		# no products found exit the application , LOL 
		if len(n_products)<1:
			# print('Ohh shoot, we dont have any products for your persona, are you sure you entered your persona correctly ??')
			return 1

		trending_set=set([i[0] for i in cursor.fetchall() if i[1]==1])
		logger.info('Trending set LEN:%d and set is :%s',len(trending_set),repr(trending_set))
		logger.info('Products are LEN:%d and list is :%s',len(n_products),repr(n_products))

		#populate truesampleset
		# true_sample_set=set(random.sample(trending_set | fallback_set,10))
				
		#iterate and populate product's like and dislike sets
		logger.info('Starting population of products liked/disliked set')
		for elem in n_products:
			#populate like set
			logger.info('DB Query: Fetching like set of product %d',elem)
			cursor.execute('''SELECT user_id FROM user_inputs_table WHERE product_id=? AND input_val=1''',(elem,))
			logger.info('DB Query: SUCCESS')
			n_pr_lset[elem]=set([i[0] for i in cursor.fetchall()])
			logger.info('Like set of product %d is of LEN:%d and set is :%s',elem,len(n_pr_lset[elem]),repr(n_pr_lset[elem]))
			
			#populate dislikes set
			logger.info('DB Query: Fetching dislike set of product %d',elem)
			cursor.execute('''SELECT user_id FROM user_inputs_table WHERE product_id=? AND input_val=-1''',(elem,))
			logger.info('DB Query: SUCCESS')
			n_pr_dset[elem]=set([i[0] for i in cursor.fetchall()])
			logger.info('disLike set of product %d is of LEN:%d and set is :%s',elem,len(n_pr_dset[elem]),repr(n_pr_dset[elem]))
			#initialize the similarity index value
			n_pr_pval[elem]=None
		

		#get list of previous users
		logger.info('DB Query: Selecting all previous users for persona:%s',user_persona)
		cursor.execute('''SELECT user_id FROM user_info_table WHERE persona=?''',(user_persona,))
		logger.info('DB Query: SUCCESS')
		n_users=[i[0] for i in cursor.fetchall()] # converting [(1,), (2,), (3,)] to [1, 2, 3]
		n_users.remove(user_id)
		logger.info('Users are LEN:%d and list is :%s',len(n_users),repr(n_users))

		#if no users found, exit 
		if len(n_users)<1:
			# print('Looks like you are first in this category!!')
			logger.info('No previous users')
			logger.info('Fn: populate_previous_data() exited')
			return 0
		
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
		
		templist=list()
		templist=[(elem,len(n_pr_lset[elem])) for elem in n_products]
		templist.sort(key=lambda tup: tup[1],reverse=True)
		logger.info('templist is %s',repr(templist))
		fallback_set=set([i[0] for i in templist[0:40]])
		logger.info('Fallback set LEN:%d and set is :%s',len(fallback_set),repr(fallback_set))

		logger.info('Fn: populate_previous_data() exited')
		return 0

def print_personas():
	''' Print all the different persona's of products present in the product_info_table '''
	global cursor
	cursor.execute('''SELECT DISTINCT persona from product_info_table''')
	product_personas=set([i[0] for i in cursor.fetchall()])
	#  print 3 personas in a line
	# it = iter(product_personas)
	for elem in product_personas:
		print(elem)

def set_user(arg1,arg2):
	
	global user_email,user_persona
	user_email=arg1
	user_persona=arg2
	get_user_id()

def set_user_input(arg1):
	
	global menu_val

	if arg1 == 1:
		menu_val='y';update_new_input()
	elif arg1 == -1:
		menu_val='n';update_new_input()
	else :
		menu_val='e'
		push_user_data_to_db()	

def getProduct():
	showProduct()
	return current_product

def start():
	global db,cursor,logger,handler

	#connect to db
	logger.info('Connecting to train.db')
	db=sqlite3.connect('train.db')
	cursor=db.cursor()
	logger.info('Connected to db')

def end():
	global db,cursor

	db.commit() #make sure any pending transactions are comitted
	db.close() #close db
	logger.info('DB committed and closed')

	logger.info('Exited application')
	logging.shutdown()

''' FUNCTION DEFINITIONS END'''

# probability method
def trial1():
	"""
	Returns 0 for a successful attempt, else returns 1 and prints the error message
	"""
	global logger
	global current_product,n_users,n_users_dset,n_users_jset,n_users_lset,current_set_l,current_set_d
	global n_products,n_pr_dset,n_pr_pval,n_pr_lset
	global trending_set,fallback_set
	logger.info('Fn: update_current_product() called')
	
	if len(n_users) <1 :
		#show trending products
		logger.info('No previous dataset of users,show trending products')
		probable_set=set((trending_set - (current_set_d | current_set_l | all_suggestions)))
		logger.info('Probable set is %s',repr(probable_set))
		
		if len(probable_set) <1:
			# print('Phew!! we are all exhausted here, thank you for your inputs. See you next time.')
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
			
			# take only those that user has not seen for calc probabilities.
			concerned_list = list(set(n_products) - (current_set_d | current_set_l | all_suggestions) )
			
			''' original '''
			# for elem in concerned_list:
			# 	calc_val=0
			# 	for val in n_pr_lset[elem]:
			# 		calc_val+= n_users_jset[val]
			# 	for val in n_pr_dset[elem]:
			# 		calc_val-= n_users_jset[val]

			# 	if (len(n_pr_lset[elem]) + len(n_pr_dset[elem])) <1:
			# 		n_pr_pval[elem]=-1000000
			# 	else:
			# 		calc_val/= (len(n_pr_lset[elem]) + len(n_pr_dset[elem]))
			# 		n_pr_pval[elem]=calc_val
			''' original '''

			for elem in concerned_list:
				calc_val=0
				for val in n_pr_lset[elem]:
					calc_val+= n_users_jset[val]
				if (len(n_pr_lset[elem]) + len(n_pr_dset[elem])) <1:
					n_pr_pval[elem]=-10
				else:
					# calc_val/= (len(n_pr_lset[elem]) + len(n_pr_dset[elem]))
					n_pr_pval[elem]=calc_val
			# for elem in concerned_list:
			# 	calc_val=0
			# 	calc_val+=len(n_pr_lset[elem])
			# 	n_pr_pval[elem]=calc_val
					
			concerned_list.sort(key=n_pr_pval.get,reverse=True)
			logger.info('The sorted list of products is %s',repr([(elem,n_pr_pval[elem]) for elem in concerned_list]))
			# we now have the sorted list of products based on their probabilities  not in all_suggestions
			if len(concerned_list) > 0: 
				current_product=concerned_list[0]
				return 0
			
		else:
			# show a random product to build user profile
			# or show a product from the top/least number of inputs				
			logger.info('NOW showing random product as user inputs were not enough')
			probable_set=set((fallback_set - (current_set_d | current_set_l | all_suggestions)))
			logger.info('Probable set for random product is %s',repr(probable_set))
			if len(probable_set) <1:
				print('2Phew!! we are all exhausted here, thank you for your inputs. See you next time.')
				logger.info('random probable set size was less than 1')
				logger.info('Fn: update_current_product() exited with return value 1')
				return 1
			else:
				current_product=random.sample(probable_set,1)[0]
				logger.info('current_product is set to %d',current_product)
				logger.info('Fn: update_current_product() exited with return value 0')
				return 0
	logger.info('Fn: update_current_product() exited with return value None')

# nearest user method
def trial2():

	"""
	Returns 0 for a successful attempt, else returns 1 and prints the error message
	"""
	global logger
	global current_product,n_users,n_users_dset,n_users_jset,n_users_lset,current_set_l,current_set_d
	global n_products,n_pr_dset,n_pr_pval,n_pr_lset
	global trending_set,fallback_set
	logger.info('Fn: update_current_product() called')
	
	if len(n_users) <1 :
		#show trending products
		logger.info('No previous dataset of users,show trending products')
		probable_set=set((trending_set - (current_set_d | current_set_l | all_suggestions)))
		logger.info('Probable set is %s',repr(probable_set))
		
		if len(probable_set) <1:
			# print('Phew!! we are all exhausted here, thank you for your inputs. See you next time.')
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
			
							
			# for all nearest neighbours in descending order of similarity index
			nearest_order=sorted(n_users_jset, key=n_users_jset.get,reverse=True)
			logger.info('Nearest users order is %s',repr(nearest_order))
			for elem in nearest_order:
				# try their like set
				probable_set=set((n_users_lset[elem] - (current_set_d | current_set_l | all_suggestions)))
				logger.info('Probable set with user %d is %s',elem,repr(probable_set))
				if len(probable_set)>0:
					current_product=random.sample(probable_set,1)[0] #choose any one from nearest user's like set
					logger.info('current_product is set to %d',current_product)
					logger.info('Fn: update_current_product() exited with return value 0')
					return 0
			
			#if reached here, means in loop anywhere we could not find a product,show user more products from the fallback set 
			# show a fallback product to build better user profile
			logger.info('NOW showing fallback product, no user product matched')
			probable_set=set((fallback_set - (current_set_d | current_set_l | all_suggestions)))
			logger.info('Probable set for fallback product is %s',repr(probable_set))
			if len(probable_set) <1:
				print('1Phew!! we are all exhausted here, thank you for your inputs. See you next time.')
				logger.info('fallback probable set size was less than 1')
				logger.info('Fn: update_current_product() exited with return value 1')
				return 1
			else:
				current_product=random.sample(probable_set,1)[0]
				logger.info('current_product is set to %d',current_product)
				logger.info('Fn: update_current_product() exited with return value 0')
				return 0
			''' OLD '''
		else:
			# show a fallback product to build user profile
			# or show a product from the top/least number of inputs				
			logger.info('NOW showing fallback product as user inputs were not enough')
			probable_set=set((fallback_set - (current_set_d | current_set_l | all_suggestions)))
			logger.info('Probable set for fallback product is %s',repr(probable_set))
			if len(probable_set) <1:
				print('2Phew!! we are all exhausted here, thank you for your inputs. See you next time.')
				logger.info('fallback probable set size was less than 1')
				logger.info('Fn: update_current_product() exited with return value 1')
				return 1
			else:
				current_product=random.sample(probable_set,1)[0]
				logger.info('current_product is set to %d',current_product)
				logger.info('Fn: update_current_product() exited with return value 0')
				return 0
	logger.info('Fn: update_current_product() exited with return value None')

#item-item similarity
def trial3():
	"""
	Returns 0 for a successful attempt, else returns 1 and prints the error message
	"""
	global logger
	global current_product,n_users,n_users_dset,n_users_jset,n_users_lset,current_set_l,current_set_d
	global n_products,n_pr_dset,n_pr_pval,n_pr_lset
	global trending_set,fallback_set
	logger.info('Fn: update_current_product() called')
	
	if len(n_users) <1 :
		#show trending products
		logger.info('No previous dataset of users,show trending products')
		probable_set=set((trending_set - (current_set_d | current_set_l | all_suggestions)))
		logger.info('Probable set is %s',repr(probable_set))
		
		if len(probable_set) <1:
			# print('Phew!! we are all exhausted here, thank you for your inputs. See you next time.')
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
			
			# take only those that user has not seen for calc probabilities.
			concerned_list = list(set(n_products) - (current_set_d | current_set_l | all_suggestions) )

			for elem in concerned_list:
				calc_val=0
				for val in n_pr_lset[elem]:
					calc_val+= n_users_jset[val]
				for val in n_pr_dset[elem]:
					calc_val-= n_users_jset[val]

				if (len(n_pr_lset[elem]) + len(n_pr_dset[elem])) <1:
					n_pr_pval[elem]=-1000000
				else:
					calc_val/= (len(n_pr_lset[elem]) + len(n_pr_dset[elem]))
					n_pr_pval[elem]=calc_val
					
			concerned_list.sort(key=n_pr_pval.get,reverse=True)
			logger.info('The sorted list of products is %s',repr([(elem,n_pr_pval[elem]) for elem in concerned_list]))
			# we now have the sorted list of products based on their probabilities  not in all_suggestions
			if len(concerned_list) > 0: 
				current_product=concerned_list[0]
				return 0
			
			''' OLD '''				
			#for all nearest neighbours in descending order of similarity index
			# nearest_order=sorted(n_users_jset, key=n_users_jset.get,reverse=True)
			# logger.info('Nearest users order is %s',repr(nearest_order))
			# for elem in nearest_order:
			# 	# try their like set
			# 	probable_set=set((n_users_lset[elem] - (current_set_d | current_set_l | all_suggestions)))
			# 	logger.info('Probable set with user %d is %s',elem,repr(probable_set))
			# 	if len(probable_set)>0:
			# 		current_product=random.sample(probable_set,1)[0] #choose any one from nearest user's like set
			# 		logger.info('current_product is set to %d',current_product)
			# 		logger.info('Fn: update_current_product() exited with return value 0')
			# 		return 0
			
			# #if reached here, means in loop anywhere we could not find a product,show user more products from the random set 
			# # show a random product to build better user profile
			# logger.info('NOW showing random product, no user product matched')
			# probable_set=set((fallback_set - (current_set_d | current_set_l | all_suggestions)))
			# logger.info('Probable set for random product is %s',repr(probable_set))
			# if len(probable_set) <1:
			# 	print('1Phew!! we are all exhausted here, thank you for your inputs. See you next time.')
			# 	logger.info('random probable set size was less than 1')
			# 	logger.info('Fn: update_current_product() exited with return value 1')
			# 	return 1
			# else:
			# 	current_product=random.sample(probable_set,1)[0]
			# 	logger.info('current_product is set to %d',current_product)
			# 	logger.info('Fn: update_current_product() exited with return value 0')
			# 	return 0
			''' OLD '''
		else:
			# show a random product to build user profile
			# or show a product from the top/least number of inputs				
			logger.info('NOW showing random product as user inputs were not enough')
			probable_set=set((fallback_set - (current_set_d | current_set_l | all_suggestions)))
			logger.info('Probable set for random product is %s',repr(probable_set))
			if len(probable_set) <1:
				print('2Phew!! we are all exhausted here, thank you for your inputs. See you next time.')
				logger.info('random probable set size was less than 1')
				logger.info('Fn: update_current_product() exited with return value 1')
				return 1
			else:
				current_product=random.sample(probable_set,1)[0]
				logger.info('current_product is set to %d',current_product)
				logger.info('Fn: update_current_product() exited with return value 0')
				return 0
	logger.info('Fn: update_current_product() exited with return value None')

# calc aggregate product based on nearest users 
def trial4():
	"""
	Returns 0 for a successful attempt, else returns 1 and prints the error message
	"""
	global logger
	global current_product,n_users,n_users_dset,n_users_jset,n_users_lset,current_set_l,current_set_d
	global n_products,n_pr_dset,n_pr_pval,n_pr_lset
	global trending_set,fallback_set
	logger.info('Fn: update_current_product() called')
	
	if len(n_users) <1 :
		#show trending products
		logger.info('No previous dataset of users,show trending products')
		probable_set=set((trending_set - (current_set_d | current_set_l | all_suggestions)))
		logger.info('Probable set is %s',repr(probable_set))
		
		if len(probable_set) <1:
			# print('Phew!! we are all exhausted here, thank you for your inputs. See you next time.')
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
			
			# for all nearest neighbours in descending order of similarity index
			nearest_order=sorted(n_users_jset, key=n_users_jset.get,reverse=True)
			logger.info('Nearest users order is %s',repr(nearest_order))
			probable_dict=dict()
			# take the product with most frequency in nearest 5 users
			for elem in nearest_order[0:5]:
				for each in (n_users_lset[elem] - (current_set_d | current_set_l | all_suggestions)):
					probable_dict[each]=probable_dict.get(each,0)+1
			logger.info('pdd dict is %s',repr(probable_dict))
			pdd=sorted(probable_dict, key=probable_dict.get,reverse=True)
			logger.info('pdd is %s',repr(pdd))
			if len(pdd)>0:
				current_product=pdd[0] #choose any one from nearest user's like set
				logger.info('current_product is set to %d',current_product)
				logger.info('Fn: update_current_product() exited with return value 0')
				return 0
			
			#if reached here. product not found
			# show a random product to build better user profile
			logger.info('NOW showing random product, no user product matched')
			probable_set=set((fallback_set - (current_set_d | current_set_l | all_suggestions)))
			logger.info('Probable set for random product is %s',repr(probable_set))
			if len(probable_set) <1:
				print('1Phew!! we are all exhausted here, thank you for your inputs. See you next time.')
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
			# or show a product from the top/least number of inputs				
			logger.info('NOW showing random product as user inputs were not enough')
			probable_set=set((fallback_set - (current_set_d | current_set_l | all_suggestions)))
			logger.info('Probable set for random product is %s',repr(probable_set))
			if len(probable_set) <1:
				print('2Phew!! we are all exhausted here, thank you for your inputs. See you next time.')
				logger.info('random probable set size was less than 1')
				logger.info('Fn: update_current_product() exited with return value 1')
				return 1
			else:
				current_product=random.sample(probable_set,1)[0]
				logger.info('current_product is set to %d',current_product)
				logger.info('Fn: update_current_product() exited with return value 0')
				return 0
	logger.info('Fn: update_current_product() exited with return value None')

#  START of APPLICATION
'''
logger.info('Application Started')
print("Welcome to Product Roulette")

#connect to db
logger.info('Connecting to train.db')
db=sqlite3.connect('train.db')
cursor=db.cursor()
logger.info('Connected to db')

logger.info('Taking user input')
user_email=input('Enter your email-id : ')
user_persona=None
get_user_id()
if user_id==None:
	#  ask for persona and add to db 
	print('Looks like you are here for the first time.')
	user_persona=input('Enter your persona (for suggestions press \'x\'):')
	if user_persona=='x':
		print_personas()
		user_persona=input('Enter your persona :')
	get_user_id()
	print('Registered you ! Getting products for your persona')
else:
	print('Found you ! Getting products for your persona:',user_persona)

# all previous user input data 
populate_previous_data()

# variable to check if user input is valid
valid_choice=1
while(1):
	showProduct(valid_choice)
	#if error happened in showProduct,current_product is set to None
	if current_product == None:
		logger.info('current_product was set to None')
		push_user_data_to_db() #before exit , users input are pushed to Db
		break
	logger.info('Product shown is :%d',current_product)
	menu_val=input('Press \'y\' if you like product, \'n\' if you don;t like the product , \'p\' to pass and \'e\' to exit application : ')
	if(menu_val =='e'):
		logger.info('User entered valid choice:exit command')
		valid_choice=1
		push_user_data_to_db() #before exit , users input are pushed to Db
		break
	elif(menu_val =='y' or menu_val =='n' or menu_val=='p'):
		logger.info('User entered valid choice')
		valid_choice=1
		update_new_input() # user input added to newset(user's inputs in this session) and user's overall like/dislike set if input is y or n
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

#  END of APPLICATION
'''

# if __name__ == '__main__':
