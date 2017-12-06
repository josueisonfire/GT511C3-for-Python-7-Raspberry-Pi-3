# Python library to make a POST request
import requests

# This function posts the data to the server
# Arguments :
#		server : address of the server
#		data 	 : JSON formatted data
def postData(server ,data):
	# make request
	res = requests.post(server, json=data)
	# check for server response code
	print res.text



# __main__

# sample JSON format expected
# Student ID
# Fingerprint ID
# Timestamp
data = {'sid':'314159265', 'fid':'9', 'time': '12:00:00'}

# server address
server = 'http://172.16.23.189:5000/tests/endpoint'
postData(server,data)