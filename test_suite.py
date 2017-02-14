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
csvresults=list()
csvresults.append(['model_no','iteration','user_email','likes','dislikes','hits','oops','suggestions_given','suggestions_value'])

# testing parameters
model_nos=[1]
iterations=3
nsuggestions_peruser=20
test_set_size=5

model_results=dict()

for model_no in model_nos:
	
	#result calculations
	total_hits=0
	total_suggestions=0
	previous_avg=0
	avg_hit_per_suggestion=0
	avg_hit_per_like=0
	should_exit=0
	
	for iterval in range(iterations):
		
		if should_exit == 1:
			break;
		popdb.start(test_set_size)

		# use the test db and iterate over each user
		db=sqlite3.connect('test.db')
		cursor=db.cursor()
		populate_user_details()


		for elem in n_users_test:
			pr.start(model_no)
			pr.set_user(elem[1],elem[2]) # will set the internal variable for user id also 
			pr.populate_previous_data()
			pr.valid_choice=1
			
			hits_peruser=0
			oops_peruser=0
			
			# each user gives 10 inputs
			for i in range(nsuggestions_peruser):
				suggestion=pr.getProduct() # basically calls showproduct and returns current_product id
				if suggestion == None:
					# print('None suggested')
					pass
					# continue
					# pr.set_user_input(0)
					# break
				# send input to pr
				if suggestion in n_users_lset_test[elem[0]]:
					pr.set_user_input(1)
					# print("!!! HIT !!!")
					hits_peruser+=1
				elif suggestion in n_users_dset_test[elem[0]]:
					pr.set_user_input(-1)
					# print("!!! OOPS !!!")
					oops_peruser+=1
				n_users_sgset_test[elem[0]].add(suggestion)
			pr.set_user_input(0) # this will end the pr and call push data to db 
			# we can push the complete data for this user from test to train also
			pr.end()

			#calculate result for user
			n_users_rset_test[elem[0]]=(hits_peruser,oops_peruser,len(n_users_sgset_test[elem[0]]))
			# print('result for:',elem[0],':',n_users_rset_test[elem[0]])
			csvresults.append([model_no,iterval+1,elem[1],len(n_users_lset_test[elem[0]]),len(n_users_dset_test[elem[0]]),hits_peruser,oops_peruser,len(n_users_sgset_test[elem[0]]),nsuggestions_peruser])

			#total calc
			total_hits+=hits_peruser
			total_suggestions+=len(n_users_sgset_test[elem[0]])

			#recall calc
			avg_hit_per_like+=hits_peruser/len(n_users_lset_test[elem[0]])
			
		previous_avg=avg_hit_per_suggestion
		avg_hit_per_suggestion=total_hits/total_suggestions

		print('Iter',iterval,'>> diff:',abs(avg_hit_per_suggestion-previous_avg))

	model_results[model_no]={'precision':avg_hit_per_suggestion*10,'recall':(avg_hit_per_like*10)/(iterations*test_set_size)}

with open('results.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerows(csvresults)
print('Completed>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
print('Model results:',repr(model_results))