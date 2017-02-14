import sqlite3
import product_roulette as pr
import populate_db as popdb
import csv

'''GLOBALS ''' 
n_users_test=list() # list of tuple(email,persona) users
n_users_lset_test=dict() # dict of l sets
n_users_dset_test=dict() # dict of d sets
n_users_sgset_test=dict() # dict of suggestionsets 
n_users_rset_test=dict() # result dict
'''GLOBALS '''


''' FUNCTION DECLARATIONS'''
def populate_user_details():

	global n_users_test,n_users_sgset_test,n_users_dset_test,n_users_lset_test,n_users_rset_test
	
	#get list of previous users
	db=sqlite3.connect('test.db')
	cursor=db.cursor()
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

# testing parameters
model_nos=[2,4]
iterations=3
nsuggestions_peruser=20
test_set_size=5

# results 
csvresults=list()
csvresults.append(['model_no','iteration','user_email','likes','dislikes','hits','oops','suggestions_given','suggestions_value'])
model_results=dict()

# start simulation
for model_no in model_nos:
	
	#result calculation variables
	total_hits=0
	total_suggestions=0
	previous_avg=0
	avg_hit_per_suggestion=0
	avg_hit_per_like=0
	should_exit=0
	
	print('Model No.',model_no)
	
	for iterval in range(iterations):
		
		if should_exit == 1:
			break
			
		popdb.start(test_set_size)  # part the data into training and testing sets
		populate_user_details()		# populate the details of test users

		for elem in n_users_test:
			
			pr.start(model_no)			 # initialize the roulette for current user with model no.
			pr.set_user(elem[1],elem[2]) # set the current user email,persona in roulette
			pr.populate_previous_data()	 # get the data in roulette from the train db 
			pr.valid_choice=1			 
			
			hits_peruser=0				 # initialize the hit and oop count for user
			oops_peruser=0
			
			for i in range(nsuggestions_peruser):
				suggestion=pr.getProduct() 			# get the suggestion(product id) for the user
				print(suggestion,'suggested to',elem[1])
				if suggestion == None:
					# print('None suggested')
					pass
					# continue
					# pr.set_user_input(0)
					# break
				if suggestion in n_users_lset_test[elem[0]]:		# HIT
					pr.set_user_input(1)
					# print("!!! HIT !!!")
					hits_peruser+=1
				
				elif suggestion in n_users_dset_test[elem[0]]:		# OOPs
					pr.set_user_input(-1)
					# print("!!! OOPS !!!")
					oops_peruser+=1
				n_users_sgset_test[elem[0]].add(suggestion)			# add suggestion to users set
			
			# end the roulette
			pr.set_user_input(0)
			pr.end()				

			#calculate result for user
			n_users_rset_test[elem[0]]=(hits_peruser,oops_peruser,len(n_users_sgset_test[elem[0]]))
			csvresults.append([model_no,iterval+1,elem[1],len(n_users_lset_test[elem[0]]),len(n_users_dset_test[elem[0]]),hits_peruser,oops_peruser,len(n_users_sgset_test[elem[0]]),nsuggestions_peruser])

			#total hits and suggestions calc
			total_hits+=hits_peruser
			total_suggestions+=len(n_users_sgset_test[elem[0]])

			#recall calculation
			avg_hit_per_like+=hits_peruser/len(n_users_lset_test[elem[0]])
			
		previous_avg=avg_hit_per_suggestion
		avg_hit_per_suggestion=total_hits/total_suggestions

		#print('Iteration',iterval,'>> diff:',abs(avg_hit_per_suggestion-previous_avg))
		print('Iteration',iterval,'>> precision:',avg_hit_per_suggestion)
	model_results[model_no]={'precision':avg_hit_per_suggestion*10,'recall':(avg_hit_per_like*10)/(iterations*test_set_size)}
	
#write results to csv
with open('results.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerows(csvresults)
print('<<<<<<<<<<<<<<<<<  Completed  >>>>>>>>>>>>>>>>>')
print('Model results:',repr(model_results))
