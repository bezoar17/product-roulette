import sqlite3
import product_roulette as pr
import populate_db as popdb
import csv

# simulation parameters
model_nos=[1,2,3,4]
iterations=10
nsuggestions_peruser=20
test_set_size=5

# results
csvresults=list()
csvresults.append(['model_no','iteration','user_email','likes','dislikes','hits','oops','suggestions_given','suggestions_value'])
model_results=dict()

'''GLOBALS ''' 
n_users_test=list() # list of tuple(test-id,email,persona) users
n_users_lset_test=dict() # dict of l sets
n_users_dset_test=dict() # dict of d sets
n_users_sgset_test=dict() # dict of suggestionsets 
n_users_rset_test=dict() # result dict (hits,oops,total_suggestions)
'''GLOBALS '''

''' FUNCTION DECLARATIONS'''
def populate_user_details():

	global n_users_test,n_users_sgset_test,n_users_dset_test,n_users_lset_test,n_users_rset_test
	
	#get list of users to be tested
	db=sqlite3.connect('test.db')
	cursor=db.cursor()
	cursor.execute('''SELECT user_id,email_id,persona FROM user_info_table''')
	n_users_test=list(cursor.fetchall())	# list of tuple(test-id,email,persona) users
	
	#if no users found, exit
	if len(n_users_test)<1:	print('no users found errror!!');return
	
	#iterate and populate every user's like and dislike sets
	for elem in n_users_test:
		
		#populate like set
		cursor.execute('''SELECT product_id FROM user_inputs_table WHERE user_id=? AND input_val=1''',(elem[0],))
		n_users_lset_test[elem[0]]=set([i[0] for i in cursor.fetchall()]) # converting [(1,),(2,)] to [1,2]
		
		#populate dislikes set
		cursor.execute('''SELECT product_id FROM user_inputs_table WHERE user_id=? AND input_val=-1''',(elem[0],))
		n_users_dset_test[elem[0]]=set([i[0] for i in cursor.fetchall()]) # converting [(1,),(2,)] to [1,2]
		
		#initialize the other values
		n_users_rset_test[elem[0]]=None
		n_users_sgset_test[elem[0]]=set()	
''' FUNCTION DECLARATIONS'''

# start simulation
for model_no in model_nos:
	
	#result calculation variables
	avg_hit_per_suggestion=0
	avg_hit_per_like=0
		
	print('Model No.',model_no)
	
	for iterval in range(iterations):
		
		print('Iteration No.',iterval)
		
		popdb.start(test_set_size)  # part the data into training and testing sets
		populate_user_details()		# populate the details of test users

		for elem in n_users_test:
			
			pr.start(model_no)			 # initialize the roulette for current user with model no.
			pr.set_user(elem[1],elem[2]) # set the current user email,persona in roulette
			pr.populate_previous_data()	 # get the data in roulette from the train db
			
			hits_peruser=0				 # initialize the hit and oop count for current user
			oops_peruser=0
			none_count=0
			
			for i in range(nsuggestions_peruser):
				suggestion=pr.getProduct() 			# get the suggestion(product id) for the user
				print(suggestion,'suggested to',elem[1])
				if suggestion == None:
					none_count+=1
				if suggestion in n_users_lset_test[elem[0]]:		# HIT
					pr.set_user_input(1)
					# print("!!! HIT !!!")
					hits_peruser+=1
				elif suggestion in n_users_dset_test[elem[0]]:		# OOPs
					pr.set_user_input(-1)
					# print("!!! OOPS !!!")
					oops_peruser+=1
			
			n_users_sgset_test[elem[0]]=set(pr.all_suggestions) # get suggestion set from roulette
			# end the roulette
			pr.end()

			#calculate result for user
			n_users_rset_test[elem[0]]=(hits_peruser,oops_peruser,len(n_users_sgset_test[elem[0]]))
			csvresults.append([model_no,iterval+1,elem[1],len(n_users_lset_test[elem[0]]),len(n_users_dset_test[elem[0]]),hits_peruser,oops_peruser,len(n_users_sgset_test[elem[0]]),nsuggestions_peruser])
			
			#precision calculation
			avg_hit_per_suggestion+=(hits_peruser/len(n_users_sgset_test[elem[0]]))
			
			#recall calculation
			avg_hit_per_like+=(hits_peruser/len(n_users_lset_test[elem[0]]))
			
			print('Fallback count:',pr.fall_back_count,'None count:',none_count,'Hit count:',hits_peruser,'Oops count:',oops_peruser)

	model_results[model_no]={'precision':(avg_hit_per_suggestion*10)/(iterations*test_set_size),'recall':(avg_hit_per_like*10)/(iterations*test_set_size)}

#write results to csv
with open('results.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerows(csvresults)
print('<<<<<<<<<<<<<<<<<  Completed  >>>>>>>>>>>>>>>>>')
print('Model results:',repr(model_results))
