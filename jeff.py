import ipaddress as ip

import csv

from scrut_api import ReportAPI, Requester
import json


report_params = ReportAPI()

scrutinizer_requester = Requester(
    authToken="xhaCcfLp2nmLsDZBXb8NWCjM",
    hostname="10.60.1.154"
)

parents = {
    "china": ['10.6.0.0/16', '192.168.6.0/24'],
    "highland" : ['10.1.0.0/16'],
    "taylor":["10.2.0.0/16","192.168.10.0/24","192.168.11.0/24"],
    "Singapore":["10.5.0.0/16",	"192.168.8.0/24"],
    "Mexico":["10.3.0.0/16","192.168.15.0/24"],
    "Eagle Pass": ["10.7.0.0/16","192.168.13.0/24"],
    "BP": ["10.8.0.0/16","192.168.12.0/24"],
    "E2":["10.9.0.0/16","192.168.16.0/24"]
    }


## dictionary that will be used to add the IDs for the children. 

parents_two = {
    "china":  {"subnets" : ['10.6.0.0/16', '192.168.6.0/24'],
    "child_ids":[]},
    "highland" :  {"subnets" : ['10.1.0.0/16'],
    "child_ids":[]},
    "taylor": {"subnets" : ["10.2.0.0/16","192.168.10.0/24","192.168.11.0/24"],
    "child_ids":[]},
    "Singapore": {"subnets" : ["10.5.0.0/16",	"192.168.8.0/24"],
    "child_ids":[]},
    "Mexico": {"subnets" : ["10.3.0.0/16","192.168.15.0/24"],
    "child_ids":[]},
    "Eagle Pass":  {"subnets" : ["10.7.0.0/16","192.168.13.0/24"],
    "child_ids":[]},
    "BP":  {"subnets" : ["10.8.0.0/16","192.168.12.0/24"],
    "child_ids":[]},
    "E2": {"subnets" : ["10.9.0.0/16","192.168.16.0/24"],
    "child_ids":[]}
    }


children = {

}

## goes through the CSV and adds all the ipgroups to a dicstionary, making the group name the key, and the subnet information a dictionary, example format would be

with open('children.csv', newline='') as csvfile:
    spamreader = csv.reader(csvfile, delimiter=',', quotechar='|')
    for row in spamreader:
        children[row[0]] = {
            'subnet':row[1],
            'subnet_split':row[1].split('/'),
            'id':'', 
            'parent':'' }


## flags a child as a parent IF the child shows up int he parent dictionary which is hard codes. You mentioned you may just remove those from the CSV, so this may not be needed.

for child in children:
    for subnet in parents: 
        if children[child]['subnet'] in parents[subnet]:
            children[child]['parent'] = True


## Now that the children dictionary is created, this loops through it and adds the parents name to the parent value for each group (only if the value was not set to true from the previous loop). If you remove the previous loop and the offending groups, you will not need to preform the check, although leaving it in shouldn't hurt anything. 

for child in children:
    try:
        network_one = ip.ip_network(children[child]['subnet'])
        for parent in parents:
            for network in parents[parent]:
                network_two = ip.ip_network(network)
                if network_one.overlaps(network_two) and children[child]['parent'] != True:
                    children[child]['parent'] = parent
        

        
    except:
        pass


## makes the API call and creates all the IP groups. 

print("creating all children groups")
for child in children: 
    group_name = child
    group_subnet = children[child]['subnet'].split('/')[0]
    group_mask = children[child]['subnet'].split('/')[1]
    report_params.create_group(group_name, json.dumps([{"type":"network", "address":group_subnet, "mask":group_mask}]))
    data = scrutinizer_requester.make_request(report_params)





## now that all the groups are created, we make an API call to get back all the IPGROUP data, we will use this to create the parent groups. 

report_params.find_all_groups()

print("Gathering All IP Group Data from Scrutinizer")
data = scrutinizer_requester.make_request(report_params)


##check to see if the name of the group returned fromt he API call is in the childrens object we created up above. If it is, we give it the proper ID.
print("Adding Group IDs to children Groups")
for group in data['results']:
    for child in children:
        if group['fc_name'] == child:
            children[child]['id'] = group['fc_id']


## This is a bit sloppy, but instead of refactoring the code to look in the parents dictioanry, I just recreated it and added in an ID's and Subnet portion. This loop goes through the parents_two dictionaty and adds in a list of IDs, we will later loop over that list to create the API request. 
print("Adding Group IDs to parent Groups")
for child in children:
    if children[child]['parent'] in parents:
        array_to_append = []
        child_group = children[child]
        child_parent = child_group['parent']
        parents_two[child_parent]['child_ids'].append(child_group['id'])


## final loop, goes throught the parents_two array and splits the subnet appart and then appends a dictioanry to each subnet as expect. Then goes through each ID and creates a similar dictionary that is then appented to the array_to_for_request
print("Creating Parent Groups")
for parent in parents_two:
    array_to_for_request = []
    for network in parents_two[parent]['subnets']:
        dict_to_append = {
            "type":"network",
            "address": network.split('/')[0], 
            "mask":network.split('/')[1]
        }
        array_to_for_request.append(dict_to_append)
    for group_id in parents_two[parent]['child_ids']:
        dict_to_append = {
            "type":"child",
            "child_id": group_id
        }
        array_to_for_request.append(dict_to_append)

    #creates the API call for each parent
    report_params.create_group(parent, json.dumps(array_to_for_request))
    data = scrutinizer_requester.make_request(report_params)
    print(data)