import sqlite3
import product_roulette as pr
import populate_db as popdb

'''GLOBALS ''' 

n_users_test=list() # list of tuple(email,persona) users
n_users_lset_test=dict() # dict of l sets
n_users_dset_test=dict() # dict of d sets
n_users_sgset_test=dict() # dict of suggestionsets 
n_users_rset_test=dict() # result dict

# testing parameters

'''GLOBALS ''' 


''' FUNCTION DECLARATIONS'''

def populate_user_details():

	global n_users_test,n_users_sgset_test,n_users_dset_test,n_users_lset_test,n_users_rset_test,db,cursor
	
	#get list of previous users
	cursor.execute('''SELECT user_id,email_id,persona FROM user_info_table''')
	n_users_test=list(cursor.fetchall())	# list of tuple(id,email,persona) users
	
	#if no users found, exit
	if len(n_users_test)<1:
		print('errror!!')
		return
	
	#iterate and populate user's like and dislike sets
	for elem in n_users_test:
		
		#populate like set
		cursor.execute('''SELECT product_id FROM user_inputs_table WHERE user_id=? AND input_val=1''',(elem[0],))
		n_users_lset_test[elem[0]]=set([i[0] for i in cursor.fetchall()])
		
		#populate dislikes set
		cursor.execute('''SELECT product_id FROM user_inputs_table WHERE user_id=? AND input_val=-1''',(elem[0],))
		n_users_dset_test[elem[0]]=set([i[0] for i in cursor.fetchall()])
		
		#initialize the other values
		n_users_rset_test[elem[0]]=None
		n_users_sgset_test[elem[0]]=set()	

''' FUNCTION DECLARATIONS'''

popdb.start()

# use the test db and iterate over each user
db=sqlite3.connect('test.db')
cursor=db.cursor()
populate_user_details()


for elem in n_users_test:
	pr.start()
	pr.set_user(elem[1],elem[2]) # will set the internal variable for user id also 
	pr.populate_previous_data()
	pr.valid_choice=1

	# each user gives 10 inputs
	for i in range(60):
		suggestion=pr.getProduct() # basically calls showproduct and returns current_product id
		if suggestion == None : 
			continue
			pr.set_user_input(0)
			break
		# send input to pr
		if suggestion in n_users_lset_test[elem[0]]:
			pr.set_user_input(1)
			print("!!! HIT !!!") 
		elif suggestion in n_users_dset_test[elem[0]]:
			pr.set_user_input(-1)
			print("!!! OOPS !!!")
		n_users_sgset_test[elem[0]].add(suggestion)
	pr.set_user_input(0) # this will end the pr and call push data to db 
	# we can push the complete data for this user from test to train also
	pr.end()

val1=0
val2=0
val3=0
# find the result values
for elem in n_users_test:

	calc_val=0

	val1+= len(n_users_sgset_test[elem[0]] & n_users_lset_test[elem[0]])
	val2+= len(n_users_sgset_test[elem[0]] & n_users_dset_test[elem[0]])
	val3+= len(n_users_sgset_test[elem[0]])
	calc_val=(val1-val2)/val3
	print('result for:',elem,':',val1,val2,val3)
	n_users_rset_test[elem[0]]=(val1,val2,val3,calc_val)

print('Overall results:',val1,val2,val3)
