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
all_suggestions=None

n_users=None
n_users_lset=None
n_users_dset=None
n_users_jset=None

n_products=None
n_pr_dset=None
n_pr_lset=None
n_pr_pval=None

trending_set=None
fallback_set=None

valid_choice=None
menu_val=None
db=None
cursor=None


model_value=None
fall_back_count=None
item_item_sim_matrix=None		# for model 4, zero based but 0 has empty list
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
	
	if valid_choice==0:
		logger.info('User choice was invalid')
		# print(current_product_name)
		return
	
	if not update_current_product():			#true if function was a success(i.e returned 0)
		#get product name from db
		cursor.execute('''SELECT product_name FROM product_info_table WHERE product_id=?''',(current_product,))
		current_product_name=cursor.fetchone()[0]
		all_suggestions.add(current_product)
		# print(current_product_name)
		logger.info('current product value set to %s',current_product_name)
	else:
		#update product failed
		logger.info('Current product being set to None')
		current_product=None
		current_product_name=None

def update_new_input():
	""" Add the liked/disliked item in the user's like/dislike set """
	''' Add the user in the product's likes/dislike set too !!!'''
	
	global logger
	global current_set_l, current_set_d, current_product, menu_val,new_set_l,new_set_d
	global n_pr_dset,n_pr_lset,model_value
	
	if menu_val == 'y':
		current_set_l.add(current_product)
		new_set_l.add(current_product)
		n_pr_lset[current_product].add(user_id)
		logger.info('%d added to like set of current user, like set size:%d',current_product,len(current_set_l))
	elif menu_val == 'n':
		current_set_d.add(current_product)
		new_set_d.add(current_product)
		n_pr_dset[current_product].add(user_id)
		logger.info('%d added to dislike set of current user, dislike set size:%d',current_product,len(current_set_d))
	
	''' Update the item similarity matrix if proper model_no is active '''
	if model_value == 4:
		fill_similarities(current_product,1)     # update the similarities for all product related to current_product
		pass

def push_user_data_to_db():
	"""	Push the new like/dislike data collected for the current user to the DB	"""
	global logger
	global db,cursor,user_id,new_set_l,new_set_d
	
	# if no data has been collected,exit 
	if(len(new_set_l)+len(new_set_d)<1):
		logger.info('size of user like dislike set is 0')
		return
	else:
		# iterate over each in new like and dislike set and add to the likes table
		for elem in new_set_l:
			cursor.execute('''INSERT INTO user_inputs_table(user_id,product_id,input_val) VALUES (?,?,1)''', (user_id,elem))
		for elem in new_set_d:
			cursor.execute('''INSERT INTO user_inputs_table(user_id,product_id,input_val) VALUES (?,?,-1)''', (user_id,elem))
		db.commit()
		logger.info('pushed user likes and dislikes data to db ')
		
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

	if user_persona == None:
		cursor.execute('''SELECT user_id,persona FROM user_info_table WHERE email_id=?''',(user_email,))
		user_selection=cursor.fetchone()
		
		if user_selection==None:
			logger.info('User was not found, set user_id to None and exit')
			user_id=None
			return 
		else:
			#user already present ,update user's like and dislike profile
			user_id=user_selection[0] #fetchone returns a tuple, so in this case first element is what we need
			user_persona=user_selection[1]
			logger.info('User found in db with id %d and persona:%s',user_id,user_persona)
			
			#like set
			cursor.execute('''SELECT product_id FROM user_inputs_table WHERE user_id=? AND input_val=1''',(user_id,))
			current_set_l=set([i[0] for i in cursor.fetchall()])
			logger.info('Like set for user %d is %s',user_id,repr(current_set_l))
			
			#dislike set
			cursor.execute('''SELECT product_id FROM user_inputs_table WHERE user_id=? AND input_val=-1''',(user_id,))
			current_set_d=set([i[0] for i in cursor.fetchall()])
			logger.info('DisLike set for user %d is %s',user_id,repr(current_set_d))

	else:
		logger.info('Adding new user to user info table')
		cursor.execute('''INSERT INTO user_info_table(email_id,persona) VALUES(?,?)''',(user_email,user_persona))
		cursor.execute('''SELECT user_id FROM user_info_table WHERE email_id=? AND persona=?''',(user_email,user_persona))
		user_id=cursor.fetchone()[0]
		logger.info('DB Query: Success , user id is %d',user_id)
		db.commit()

		''' WORKAROUND '''
		
		# populate currentl,d from test db
		# tdb=sqlite3.connect('test.db')
		# tcursor=tdb.cursor()
		# tcursor.execute('''SELECT user_id FROM user_info_table WHERE email_id=? AND persona=?''',(user_email,user_persona))
		# t_user_id=tcursor.fetchone()[0]
		# tdb.commit()

		# #like set
		# tcursor.execute('''SELECT product_id FROM user_inputs_table WHERE user_id=? AND input_val=1''',(t_user_id,))
		# current_set_l=set(random.sample([i[0] for i in tcursor.fetchall()],2))
		# logger.info('Like set for user %d is %s',user_id,repr(current_set_l))
		# tdb.commit()
		# tdb.close()

		''' WORKAROUND '''
		
def update_current_product():
		
	global logger
	global current_product,n_users,current_set_l,current_set_d
	global trending_set,fallback_set,model_value,fall_back_count
	
	if len(n_users) <1 :
		#show trending products
		current_product=pick_product(trending_set)
		if current_product == None:
			# print('Phew!! we are all exhausted here, thank you for your inputs. See you next time.')
			return 1
		else :
			logger.info('current product value is %d',current_product)
			return 0
	else:
		#prev data is present, if user input is more than 2
		if (len(current_set_d)+len(current_set_l)) > 2:
			if model_value==1:
				return model1()
			elif model_value==2:
				return model2()
			elif model_value==3:
				return model3()
			elif model_value==4:
				return model4()
			else:
				return model4()
		else:
			# show a random product to build user profile
			logger.info('NOW showing random product as user inputs were not enough')
			current_product=pick_product(fallback_set)
			if current_product == None:
				print('2Phew!! we are all exhausted here, thank you for your inputs. See you next time.')
				return 1
			else:
				logger.info('current_product is set to %d',current_product)
				fall_back_count+=1
				return 0
		


def populate_previous_data():
		""" 
		Get the list of previous users, their like/dislike set and populate trending and random sets
		"""
		global logger
		global db,cursor,n_users_lset,n_users_dset,n_users_jset,n_users,trending_set,user_persona,fallback_set,user_id
		global n_products,n_pr_dset,n_pr_pval,n_pr_lset,all_suggestions,model_value,item_item_sim_matrix
				
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
		
		#get list of previous products,trending and random sets
		cursor.execute('''SELECT product_id,trending FROM product_info_table WHERE persona=?''',(user_persona,))
		n_products=[i[0] for i in cursor.fetchall()] # converting [(1,), (2,), (3,)] to [1, 2, 3]
		# no products found exit the application , LOL 
		if len(n_products)<1:
			# print('Ohh shoot, we dont have any products for your persona, are you sure you entered your persona correctly ??')
			return 1

		trending_set=set([i[0] for i in cursor.fetchall() if i[1]==1])
				
		#iterate and populate product's like and dislike sets
		for elem in n_products:
			#populate like set
			cursor.execute('''SELECT user_id FROM user_inputs_table WHERE product_id=? AND input_val=1''',(elem,))
			n_pr_lset[elem]=set([i[0] for i in cursor.fetchall()])
			
			#populate dislikes set
			cursor.execute('''SELECT user_id FROM user_inputs_table WHERE product_id=? AND input_val=-1''',(elem,))
			n_pr_dset[elem]=set([i[0] for i in cursor.fetchall()])
			#initialize the index value
			n_pr_pval[elem]=None
		
		#get list of previous users
		cursor.execute('''SELECT user_id FROM user_info_table WHERE persona=?''',(user_persona,))
		n_users=[i[0] for i in cursor.fetchall()] # converting [(1,), (2,), (3,)] to [1, 2, 3]
		n_users.remove(user_id)
		
		#if no users found, exit 
		if len(n_users)<1:
			# print('Looks like you are first in this category!!')
			logger.info('Fn: populate_previous_data() exited')
			return 0
		
		#iterate and populate user's like and dislike sets
		for elem in n_users:
			#populate like set
			cursor.execute('''SELECT product_id FROM user_inputs_table WHERE user_id=? AND input_val=1''',(elem,))
			n_users_lset[elem]=set([i[0] for i in cursor.fetchall()])
			
			#populate dislikes set
			cursor.execute('''SELECT product_id FROM user_inputs_table WHERE user_id=? AND input_val=-1''',(elem,))
			n_users_dset[elem]=set([i[0] for i in cursor.fetchall()])
			
			#initialize the similarity index value
			n_users_jset[elem]=None
		
		# calculate the item item similarity matrix for model 4, maybe build fallback set based on similarity values
		if model_value == 4:
			# initialize item similarity matrix [250x250] to None
			item_item_sim_matrix = [ ([None] * (len(n_products)+1)) for row in range((len(n_products)+1)) ]
			
			# for all product id's 1 to 249 calc the respective similarity values
			for iterval in range(1,len(n_products)+1):
				fill_similarities(iterval)		
			pass
		
		templist=list()
		templist=[(elem,len(n_pr_lset[elem])) for elem in n_products]
		templist.sort(key=lambda tup: tup[1],reverse=True)
		logger.info('templist is %s',repr(templist))
		fallback_set=set([i[0] for i in templist[0:30]])
		logger.info('Fallback set LEN:%d and set is :%s',len(fallback_set),repr(fallback_set))

		return 0

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
	else:
		menu_val='e'
		push_user_data_to_db()	

def getProduct():
	showProduct()
	return current_product # global can be used directly,if not assigned

def start(model_no=4):
	global db,cursor,logger,model_value,fall_back_count,valid_choice
	#connect to db
	db=sqlite3.connect('train.db')
	cursor=db.cursor()
	logger.info('Connected to db')
	model_value=model_no
	fall_back_count=0
	valid_choice=1

def end():
	global db,logger
	
	set_user_input(0) # will set menu_val and push_user_data_to_db()
	
	db.commit() #make sure any pending transactions are comitted
	db.close() #close db
	logger.info('DB committed and closed')
	logger.info('Exited application')
	logging.shutdown()
''' FUNCTION DEFINITIONS END'''

''' MODEL FUNCTIONS '''
# returns a product from the set , else returns None (can set preference =1 for most liked product or = for random pick)
def pick_product(set_name,preferred=0):
	
	global current_set_d,current_set_l,all_suggestions,n_pr_lset
	
	pset=set((set_name - (current_set_d | current_set_l | all_suggestions)))
	
	if preferred == 0:						# pick random, no preference
		if len(pset) <1:
			return None
		else:
			return random.sample(pset,1)[0]
	elif preferred == 1:					# pick product with most likes
		if len(pset) <1:
			return None
		else:
			#templist=sorted(pset,key=lambda x: len(n_pr_lset[x]),reverse=True)
			templist=list()		
			templist=[(elem,len(n_pr_lset[elem])) for elem in list(pset)]
			templist.sort(key=lambda tup: tup[1],reverse=True)
			return templist[0][0]			# return product id with most likes
			
# calculates the user similarity of user_elem with the current user 
def calc_user_similarity(user_elem):
	
	global n_users_lset,n_users_dset,current_set_l,current_set_d
	
	calc_val=0				
	# jaccard index calculation
	calc_val+= len(n_users_lset[user_elem] & current_set_l)
	calc_val+= len(n_users_dset[user_elem] & current_set_d)
	calc_val-= len(n_users_lset[user_elem] & current_set_d)
	calc_val-= len(n_users_dset[user_elem] & current_set_l)
	calc_val/= (len(current_set_d)+len(current_set_l))
	
	return calc_val

# calculates the pval for product product_elem
#FOR MODEL 1
def calc_pval(product_elem):
	
	global n_pr_lset,n_pr_dset,n_users_jset
	
	calc_val=0
	for val in n_pr_lset[product_elem]:
		calc_val+= n_users_jset[val]
	for val in n_pr_dset[product_elem]:
		calc_val-= n_users_jset[val]

	if (len(n_pr_lset[product_elem]) + len(n_pr_dset[product_elem])) <1:
		calc_val=-100
	else:
		calc_val/= (len(n_pr_lset[product_elem]) + len(n_pr_dset[product_elem]))
	
	return calc_val

# calc similarity with users, calc pval for all products , pick product with best pval
def model1():
	"""
	Returns 0 for a successful attempt, else returns 1 and prints the error message
	"""
	global logger
	global current_product,n_users,n_users_jset,current_set_l,current_set_d
	global n_products,n_pr_pval,fallback_set,fall_back_count
	
	#the user has put in atleast 2 inputs till now
	for elem in n_users:
		n_users_jset[elem]=calc_user_similarity(elem)
	
	# take only those products that user has not seen for calculating pval.
	concerned_list = list(set((set(n_products) - (current_set_d | current_set_l | all_suggestions))))
	
	#calculate pval for each product
	for elem in concerned_list:
		n_pr_pval[elem]=calc_pval(elem)
		
	# sort products according to pval and pick product with best pval
	concerned_list.sort(key=n_pr_pval.get,reverse=True)
	logger.info('The sorted list of products is %s',repr([(elem,n_pr_pval[elem]) for elem in concerned_list]))
	if len(concerned_list) > 0: 
		current_product=concerned_list[0]
		return 0
	
	#if reached here, we could not find a product,show user more products from the fallback set 
	current_product=pick_product(fallback_set)
	if current_product == None:
		print('1Phew!! we are all exhausted here, thank you for your inputs. See you next time.')
		return 1
	else:
		logger.info('current_product is set to %d',current_product)
		fall_back_count+=1
		return 0
	
# calc similarity with users, sort acc to similarity , pick random like from nearest user
def model2():

	"""
	Returns 0 for a successful attempt, else returns 1 and prints the error message
	"""
	global logger,current_product,n_users,n_users_jset,n_users_lset,fallback_set,fall_back_count
	
	# calculate similarity values with every user
	for elem in n_users:
		n_users_jset[elem]=calc_user_similarity(elem)
	
	# sort users in descending order of similarity index
	nearest_order=sorted(n_users_jset, key=n_users_jset.get,reverse=True)
	logger.info('Nearest users order is %s',repr(nearest_order))
	for elem in nearest_order:
		# try their like set
		current_product=pick_product(n_users_lset[elem])
		if current_product != None:
			return 0
	
	#if reached here, we could not find a product,show user more products from the fallback set 
	current_product=pick_product(fallback_set)
	if current_product == None:
		print('1Phew!! we are all exhausted here, thank you for your inputs. See you next time.')
		return 1
	else:
		logger.info('current_product is set to %d',current_product)
		fall_back_count+=1
		return 0
	
# calc similarity with users, sort acc to similarity , pick most popular product in k_nearest nearest users
def model3():
	"""
	Returns 0 for a successful attempt, else returns 1 and prints the error message
	"""
	global logger,current_product,n_users,n_users_jset,current_set_l,current_set_d,fallback_set,fall_back_count
	
	k_nearest=5  # local variable
	
	# calculate similarity values with every user
	for elem in n_users:
		n_users_jset[elem]=calc_user_similarity(elem)
	
	# sort users in descending order of similarity index
	nearest_order=sorted(n_users_jset, key=n_users_jset.get,reverse=True)
	logger.info('Nearest users order is %s',repr(nearest_order))
		
	# calculate frequency of products in k_nearest nearest users
	product_freq=dict()
	for elem in nearest_order[0:k_nearest]:
		for each in (n_users_lset[elem] - (current_set_d | current_set_l | all_suggestions)):
			product_freq[each]=product_freq.get(each,0)+1
	logger.info('product frequency dict is %s',repr(product_freq))
	
	#sort products based on frequency and pick most popular
	pdd=sorted(product_freq, key=product_freq.get,reverse=True)
	logger.info('sorted products on frequency is %s',repr(pdd))
	if len(pdd)>0:
		current_product=pdd[0] #choose most popular
		logger.info('current_product is set to %d',current_product)
		return 0
	
	#if reached here, we could not find a product,show user more products from the fallback set 
	current_product=pick_product(fallback_set)
	if current_product == None:
		print('1Phew!! we are all exhausted here, thank you for your inputs. See you next time.')
		return 1
	else:
		logger.info('current_product is set to %d',current_product)
		fall_back_count+=1
		return 0		

# FOR MODEL 4 , function calcs the items which have a input in common and fills those similarities
def fill_similarities(product_sim_elem,updating=0):
	# for updating = 0 , copy if mirror is not None.
	# for updating = 1 , update the mirror also.
	
	global n_users_lset,n_users_dset,user_id
	global n_pr_dset,n_pr_lset,item_item_sim_matrix
	
	all_related_products_set=set()			# local variable
	# for all user's who gave input for this product 
	for each in (n_pr_lset[product_sim_elem] | n_pr_dset[product_sim_elem]):
		if each!=user_id:
			all_related_products_set |= n_users_lset[each] | n_users_dset[each]
	
	for each in all_related_products_set:
		if updating == 0:				# first time initialization of item similarity matrix
			# if diagonally opposite value is not set,calc and set both ; else set directly from opposite value.
			if item_item_sim_matrix[each][product_sim_elem] == None :
				item_item_sim_matrix[product_sim_elem][each]=calc_item_similarity(product_sim_elem,each)
				item_item_sim_matrix[each][product_sim_elem]=item_item_sim_matrix[product_sim_elem][each]
			else:
				item_item_sim_matrix[product_sim_elem][each]=item_item_sim_matrix[each][product_sim_elem]
		
		elif updating == 1:
			# just calculate the similarities for these and update the digonal element
			item_item_sim_matrix[product_sim_elem][each]=calc_item_similarity(product_sim_elem,each)
			item_item_sim_matrix[each][product_sim_elem]=item_item_sim_matrix[product_sim_elem][each]
		
		#if updating==1 or item_item_sim_matrix[each][product_sim_elem] == None:
		#	item_item_sim_matrix[product_sim_elem][each]=calc_item_similarity(product_sim_elem,each)
		#item_item_sim_matrix[each][product_sim_elem]=item_item_sim_matrix[product_sim_elem][each]
		
	pass

# FOR MODEEL 4 , function calculates item similarity	(try multiple methods)
def calc_item_similarity(item_no1,item_no2):
	# calculate the similarity distances between the products 
	# modified jaccard for items too
	
	global n_pr_lset,n_pr_dset
	
	calc_val = 0 # local variable
	
	calc_val+= len( n_pr_lset[item_no1] & n_pr_lset[item_no2] )
	# calc_val+= len( n_pr_dset[item_no1] & n_pr_dset[item_no2] )	
	# calc_val-= len( n_pr_lset[item_no1] & n_pr_dset[item_no2] )
	# calc_val-= len( n_pr_dset[item_no1] & n_pr_lset[item_no2] )
	# calc_val/= len( n_pr_dset[item_no1] | n_pr_dset[item_no2] | n_pr_lset[item_no1] | n_pr_lset[item_no2] )
	
	return calc_val

	pass

# FOR MODEL 4 , calculate prediction value
def calc_pval_model4(product_elem):
	
	global current_set_l,current_set_d,item_item_sim_matrix
	
	# every product which comes here has a value in item mattrix current_set_l,elem check none value too . (take av maybe)
	calc_val=0  # local variable
	
	# add similarity values with like set
	for each in current_set_l:
		if item_item_sim_matrix[product_elem][each] != None:
			calc_val+=item_item_sim_matrix[product_elem][each]
	
	# subtract similarity values with dislike set
	for each in current_set_d:
		if item_item_sim_matrix[product_elem][each] != None:
			calc_val-=item_item_sim_matrix[product_elem][each]
		
	return calc_val
	pass
# item-item similarity method    k_nearest items 
# explain the method 
def model4():
	"""
	Returns 0 for a successful attempt, else returns 1 and prints the error message
	"""
	global logger
	global current_product,current_set_l,current_set_d
	global n_pr_pval
	global fallback_set,item_item_sim_matrix,fall_back_count
	
	k_nearest = 5  # local variable
	similar_products_set=set()  #local variable
	
	# for each item in current user's like set find N similar items and take union and then calc similarities of this set with user's like set and pick best 
	for each in current_set_l:
		temp_list = [(i,item_item_sim_matrix[each][i]) for i in range(1,250) if (item_item_sim_matrix[each][i]!=None and (i not in set(current_set_l | current_set_d | all_suggestions)))]   # get list of (item-id,similarity) for this item
		temp_list.sort(key=lambda tup: tup[1],reverse=True)
		if len(temp_list) > k_nearest:
			temp_list=temp_list[0:k_nearest]
		similar_products_set |= set([i[0] for i in temp_list])
	
	#calculate prediction similarity for each product
	for elem in similar_products_set:
		n_pr_pval[elem]=calc_pval_model4(elem)
		
	# sort products according to pval and pick product with best pval
	if len(similar_products_set) > 0: 
		current_product=sorted(similar_products_set,key=n_pr_pval.get,reverse=True)[0]
		return 0
	
	#if reached here, we could not find a product,show user more products from the fallback set 
	current_product=pick_product(fallback_set)
	if current_product == None:
		print('1Phew!! we are all exhausted here, thank you for your inputs. See you next time.')
		return 1
	else:
		logger.info('current_product is set to %d',current_product)
		fall_back_count+=1
		return 0
	
	pass
		
''' MODEL FUNCTIONS '''
