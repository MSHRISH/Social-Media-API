import pymongo

#MongoDb Initialisation
mongo = pymongo.MongoClient("mongodb://localhost:27017/")

#User DB
profiles = mongo["socialMediaApp"]
users=profiles["Users"]

#Followers Collection
followers=profiles["followers"]
blocks=profiles['blocks']

#Check if profile 1 follows profile 2
def check_relation(profile_id_1,profile_id_2):
    """
        Checks if there exists a relationship from profile 1 to profile 2.
        Return True or False.
    """
    relation_status=followers.find_one({"of":profile_id_1,"to":profile_id_2},{"_id":0,"to":1})
    if(relation_status == None):
        return False
    return True

#Follow a profile
def follow(user_id,profile_id):
    """
        Allows a user to Follow a profile.
        Return code 40005 if user try to follow oneself.
        Return code 40006 if user is already following the profile.
        Return code 10005 if follow is successfull.
        Return code 5000 on unknown error.
    """
    if(user_id==profile_id):
        return {"code":40005}
    
    #Check if already following
    already_following=check_relation(user_id,profile_id)
    if(already_following):
        return {"code":40006}
    
    follow_status=followers.insert_one({"of":user_id,"to":profile_id}).acknowledged
    if(follow_status):
        return {"code":10005}
    return {"code":5000}

#Unfollow a profile
def unfollow(user_id,profile_id):
    """
        Allows a user to Unfollow a profile.
        Return code 40007 if user try to unfollow oneself.
        Return code 40008 if user is not following the profile.
        Return code 10006 if unfollow is successfull.
        Return code 5000 on unknown error.
    """
    if(user_id==profile_id):
        return {"code":40007}
    
    #Check if not following
    already_following=check_relation(user_id,profile_id)
    if(not already_following):
        return {"code":40008}
    
    follow_status=followers.delete_one({"of":user_id,"to":profile_id}).acknowledged
    if(follow_status):
        return {"code":10006}
    return {"code":5000}


#Show followers of a user
def user_followers(user_id,page):
    """
        Returns user's followers according to the page.
    """
    
    pipeline=[
    {
        "$match":{"to":user_id}
    },
    {   #Find out accounts blocked by user
        "$lookup":{
            "from":"blocks",
            "let":{"profileId":"$of"},
            "pipeline":[
                {
                    "$match":{
                        "$expr":{
                            "$and":[{"$eq":["$of",user_id]},{"$eq":["$to","$$profileId"]}]
                        }
                    }
                }
            ],
            "as":"blockFlag"
        }
    },
    {
        #Setting true(1) or false(0) to blockFlag
        "$project":{
            "_id":0,
            "of":"$of",
            "blockFlag":{
                "$cond":{
                    "if":{"$gt":[{"$size":"$blockFlag"},0]},
                    "then":1,
                    "else":0
                }
            }
        }
    },
     {   #Look for Common Profiles i.e profiles in the followers list of profile_id and also in following list of user_id
            "$lookup":{
                "from":"followers",
                "let":{"profileId":"$of"},
                "pipeline":[
                    {
                        "$match":{
                            "$expr":{
                                "$and":[{"$eq":["$of",user_id]},{"$eq":["$to","$$profileId"]}]
                            }
                        }
                    }
                ],
                "as":"followedByLoggedInProfile"
            }
        },
         {   #Setting true(1) or false(0) to followedByLoggedInProfile
            "$project":{
                "_id":0,
                "of":"$of",
                "blockFlag":"$blockFlag",
                "followedByLoggedInProfile":{
                    "$cond":{
                        "if":{"$gt":[{"$size":"$followedByLoggedInProfile"},0]},
                        "then": 1,
                        "else":0
                    }
                }
            }
        },
        {"$sort":{"followedByLoggedInProfile":-1,"blockFlag":1}},
        {"$skip":(page-1)*5},
        {"$limit":5},
        {   #get Profile Names
        "$lookup":{
            "from":"Users",
            "localField":"of",
            "foreignField":"_id",
            "pipeline":[
                {
                    "$project":{
                        "_id":0,
                        "name":1
                    }
                }
            ],
            "as":"profileData"
            }
        }
    ]
    followers_user=list(followers.aggregate(pipeline))
    followers_list=[]

    def craft_response(data_object):
        profile_name=data_object['profileData'][0]['name']
        if(data_object['followedByLoggedInProfile']==1):
            profile_name+="[FBY]"
        if(data_object['blockFlag']==1):
            profile_name="User Not Found"
        return profile_name
    
    followers_list=list(map(craft_response,followers_user))

    followers_count=followers.count_documents({"to":user_id})

    return {"Followers":followers_list,"count":followers_count}
    
    
#Show user's followings
def user_followings(user_id,page):
    """
        Returns Followings of the user with pagination
    """
    pipeline=[
        {"$match":{"of":user_id}},
    
        {   #Find out accounts that blocked user
            "$lookup":{
                "from":"blocks",
                "let":{"profileId":"$to"},
                "pipeline":[
                    {
                        "$match":{
                            "$expr":{
                                "$and":[{"$eq":["$of","$$profileId"]},{"$eq":["$to",user_id]}]
                            }
                        }
                    }
                ],
                "as":"blockFlag"
            }
        },
        {
            #Setting true(1) or false(0) to blockFlag
            "$project":{
                "_id":0,
                "to":"$to",
                "blockFlag":{
                    "$cond":{
                        "if":{"$gt":[{"$size":"$blockFlag"},0]},
                        "then":1,
                        "else":0
                    }
                }
            }
        },
        {"$sort":{"blockFlag":1}},
        {"$skip":(page-1)*5},
        {"$limit":5},
        {   #get Profile Names
            "$lookup":{
                "from":"Users",
                "localField":"to",
                "foreignField":"_id",
                "pipeline":[
                    {
                        "$project":{
                            "_id":0,
                            "name":1
                        }
                    }
                ],
                "as":"profileData"
            }
        }
    ]
    followings=list(followers.aggregate(pipeline))
    followings_list=[]

    def craft_response(data_obj):
        profile_name=data_obj['profileData'][0]['name']
        if(data_obj['blockFlag']==1):
            profile_name="User Not Found"
        return profile_name
    
    followings_list=list(map(craft_response,followings))

    followings_count=followers.count_documents({"of":user_id})

    return {"Followings":followings_list,"count":followings_count}


    










#Show other profile's followings
def show_followings(user_id,profile_id,page):
    """
        Uses Aggregation to find out the following list of the profile.
        Returns a list of profile names.
        Show the accounts followd by the logged in user as [FBY]
    """
    pipeline=[
     {   #Get all the followings of profile_id
            "$match":{"of":profile_id}
    },
    { #LOOK FOR IF I AM PART OF THE FOLLOWING MEANS profile_id follows user_id
            "$project":{
                "of":"$of",
                "to":"$to",
                "youFlag":{
                    "$cond":{
                        "if":{"$and":[  {"$eq":["$of",profile_id]},{"$eq":["$to",user_id]}   ]},
                        "then":1,
                        "else":0
                    }
                }
            }
            
        },
     {   #Look for Common Profiles i.e profiles in the following list of profile_id and also in following list of user_id
            "$lookup":{
                "from":"followers",
                "let":{"profileId":"$to"},
                "pipeline":[
                    {
                        "$match":{
                            "$expr":{
                                "$and":[{"$eq":["$of",user_id]},{"$eq":["$to","$$profileId"]}]
                            }
                        }
                    }
                ],
                "as":"followedByLoggedInProfile"
            }
        },
        {   #Setting true(1) or false(0) to followedByLoggedInProfile
            "$project":{
                "_id":0,
                "to":"$to",
                "youFlag":"$youFlag",
                "followedByLoggedInProfile":{
                    "$cond":{
                        "if":{"$gt":[{"$size":"$followedByLoggedInProfile"},0]},
                        "then": 1,
                        "else":0
                    }
                }
            }

        },
        

        {   #Find out accounts blocked by user
        "$lookup":{
            "from":"blocks",
            "let":{"profileId":"$to"},
            "pipeline":[
                {
                    "$match":{
                        "$expr":{
                            "$and":[{"$eq":["$of",user_id]},{"$eq":["$to","$$profileId"]}]
                        }
                    }
                }
            ],
            "as":"blockedByUser"
        }
    },
    {   #Find out accounts that blocked user
            "$lookup":{
                "from":"blocks",
                "let":{"profileId":"$to"},
                "pipeline":[
                    {
                        "$match":{
                            "$expr":{
                                "$and":[{"$eq":["$of","$$profileId"]},{"$eq":["$to",user_id]}]
                            }
                        }
                    }
                ],
                "as":"blockedTheUser"
            }
        },
    {
        #Setting true(1) or false(0) to blockFlag
        "$project":{
            "_id":0,
            "to":"$to",
            "youFlag":"$youFlag",
            "followedByLoggedInProfile":"$followedByLoggedInProfile",
            "blockedByUser":{
                "$cond":{
                    "if":{"$gt":[{"$size":"$blockedByUser"},0]},
                    "then":1,
                    "else":0
                }
            },
             "blockedTheUser":{
                    "$cond":{
                        "if":{"$gt":[{"$size":"$blockedTheUser"},0]},
                        "then":1,
                        "else":0
                    }
                }
            
        }
    },
    {"$sort":{"youFlag":-1,"followedByLoggedInProfile":-1,"blockedByUser":1,"BlockedTheUser":1}},
    {"$skip":(page-1)*5},
    {"$limit":5},
        {   #get Profile Names
        "$lookup":{
            "from":"Users",
            "localField":"to",
            "foreignField":"_id",
            "pipeline":[
                {
                    "$project":{
                        "_id":0,
                        "name":1
                    }
                }
            ],
            "as":"profileData"
        }
    }    
]

    profile_followings=list(followers.aggregate(pipeline))
    following_list=[]
    
    followings_count=followers.count_documents({"of":profile_id})
    
    def craft_response(data_object):
        profile_name=data_object['profileData'][0]['name']
        if(data_object['youFlag']==1):
            profile_name+="[YOU]"
        elif(data_object["followedByLoggedInProfile"]==1):
            profile_name+="[FBY]"
        elif(data_object['blockedByUser']==1 or data_object['blockedTheUser']==1):
            profile_name="User Not Found"
        return profile_name

    following_list=list(map(craft_response,profile_followings))
    
    return {"Followings":following_list,"count":followings_count}
            





#Show Followers
def show_followers(user_id,profile_id,page):
    """
        Uses Aggregation to find out the followers list of the profile.
        Returns a list of profile names.
        Show the accounts followd by the logged in user as [FBY]
    """
    pipeline=[
    {   #Get all the followings of profile_id(abc123)
            "$match":{"to":profile_id}
    },
    { #LOOK FOR IF I AM PART OF THE FOLLOWING MEANS profile_id follows user_id
            "$project":{
                "of":"$of",
                "to":"$to",
                "youFlag":{
                    "$cond":{
                        "if":{"$and":[  {"$eq":["$of",user_id]},{"$eq":["$to",profile_id]}   ]},
                        "then":1,
                        "else":0
                    }
                }
            }
            
        },
          {   #Look for Common Profiles i.e profiles in the following list of profile_id and also in following list of user_id
            "$lookup":{
                "from":"followers",
                "let":{"profileId":"$of"},
                "pipeline":[
                    {
                        "$match":{
                            "$expr":{
                                "$and":[{"$eq":["$of",user_id]},{"$eq":["$to","$$profileId"]}]
                            }
                        }
                    }
                ],
                "as":"followedByLoggedInProfile"
            }
        },
         {   #Setting true(1) or false(0) to followedByLoggedInProfile
            "$project":{
                "_id":0,
                "of":"$of",
                "youFlag":"$youFlag",
                "followedByLoggedInProfile":{
                    "$cond":{
                        "if":{"$gt":[{"$size":"$followedByLoggedInProfile"},0]},
                        "then": 1,
                        "else":0
                    }
                }
            }

        },
         {   #Find out accounts blocked by user
        "$lookup":{
            "from":"blocks",
            "let":{"profileId":"$of"},
            "pipeline":[
                {
                    "$match":{
                        "$expr":{
                            "$and":[{"$eq":["$of",user_id]},{"$eq":["$to","$$profileId"]}]
                        }
                    }
                }
            ],
            "as":"blockedByUser"
        }
    },
    {   #Find out accounts that blocked user
            "$lookup":{
                "from":"blocks",
                "let":{"profileId":"$of"},
                "pipeline":[
                    {
                        "$match":{
                            "$expr":{
                                "$and":[{"$eq":["$of","$$profileId"]},{"$eq":["$to",user_id]}]
                            }
                        }
                    }
                ],
                "as":"blockedTheUser"
            }
        },
         {
        #Setting true(1) or false(0) to blockFlag
        "$project":{
            "_id":0,
            "of":"$of",
            "youFlag":"$youFlag",
            "followedByLoggedInProfile":"$followedByLoggedInProfile",
            "blockedByUser":{
                "$cond":{
                    "if":{"$gt":[{"$size":"$blockedByUser"},0]},
                    "then":1,
                    "else":0
                }
            },
             "blockedTheUser":{
                    "$cond":{
                        "if":{"$gt":[{"$size":"$blockedTheUser"},0]},
                        "then":1,
                        "else":0
                    }
                }
            
        }
    },
     {"$sort":{"youFlag":-1,"followedByLoggedInProfile":-1,"blockedByUser":1,"BlockedTheUser":1}},
    {"$skip":(page-1)*5},
    {"$limit":5},
       {   #get Profile Names
        "$lookup":{
            "from":"Users",
            "localField":"of",
            "foreignField":"_id",
            "pipeline":[
                {
                    "$project":{
                        "_id":0,
                        "name":1
                    }
                }
            ],
            "as":"profileData"
        }
    }    




]


    profile_followers=list(followers.aggregate(pipeline))
    followers_count=followers.count_documents({"to":profile_id})
    followers_list=[]

    def craft_response(data_obj):
        profile_name=data_obj['profileData'][0]['name']
        if(data_obj['youFlag']==1):
            profile_name+="[YOU]"
        elif(data_obj["followedByLoggedInProfile"]==1):
            profile_name+="[FBY]"
        elif(data_obj['blockedByUser']==1 or data_obj["blockedTheUser"]==1):
            profile_name="User Not Found"
        return profile_name
    
    followers_list=list(map(craft_response,profile_followers))


    return {"Followers":followers_list,"count":followers_count}


#Check Blocks
def check_blocking(profile_1,profile_2):
    """
        Check if Profile 1 has blocked profile 2
    """
    relation_status=blocks.find_one({"of":profile_1,"to":profile_2})
    if(relation_status==None):
        return False
    return True

#Block a profile
def block(user_id,profile_id):
    """
        Allows user to block a profile.
        Return code 40009 if blockin themself
        Return code 40010 if already blocked
        Return code 10007 if block successful
        Return code 5000 on unknown error
    """
    #Check if user trying to block themself
    if(user_id==profile_id):
        return {"code":40009}
   #Check if already blocked 
    already_blocked=check_blocking(user_id,profile_id)
    if(already_blocked):
        return {"code":40010}
    
    block_status=blocks.insert_one({"of":user_id,"to":profile_id}).acknowledged
    
    #If user_id follows the profil_id then unfollow
    unfollow_status=unfollow(user_id,profile_id)

    if(block_status):
        return {"code":10007}
    return {"code":5000}
    
def unblock(user_id,profile_id):
    """
        Allows user to unblock a profile.
        Return code 40011 if blockin themself
        Return code 40012 if already blocked
        Return code 10008 if block successful
        Return code 5000 on unknown error
    """
    if(user_id==profile_id):
        return {"code":40011}
    #Check if already blocked 
    already_blocked=check_blocking(user_id,profile_id)
    if(not already_blocked):
        return {"code":40012}
    
    block_status=blocks.delete_one({"of":user_id,"to":profile_id}).acknowledged
    if(block_status):
        return {"code":10008}
    return {"code":5000}



#Blocked list of profiles
def user_blocked_profiles(user_id,page):
    """
        Gets the list of profiles blocked by the user.
        Doesn't show the profiles that blocked the user.
    """
    pipeline=[
        {   #Blocked by user_id
            "$match":{"of":user_id}
        },
        {   #Find out accounts that blocked user
            "$lookup":{
                "from":"blocks",
                "let":{"profileId":"$to"},
                "pipeline":[
                    {
                        "$match":{
                            "$expr":{
                                "$and":[{"$eq":["$of","$$profileId"]},{"$eq":["$to",user_id]}]
                            }
                        }
                    }
                ],
                "as":"blockFlag"
            }
        },
        {
            #Setting true(1) or false(0) to blockFlag
            "$project":{
                "_id":0,
                "to":"$to",
                "blockFlag":{
                    "$cond":{
                        "if":{"$gt":[{"$size":"$blockFlag"},0]},
                        "then":1,
                        "else":0
                    }
                }
            }
        },
         {"$sort":{"blockFlag":1}},
        {"$skip":(page-1)*5},
        {"$limit":5},
         {   #get Profile Names
            "$lookup":{
                "from":"Users",
                "localField":"to",
                "foreignField":"_id",
                "pipeline":[
                    {
                        "$project":{
                            "_id":0,
                            "name":1
                        }
                    }
                ],
                "as":"profileData"
            }
        }
    ]

    blocked_profiles=list(blocks.aggregate(pipeline))
    blocked_profiles_list=[]

    blocked_profiles_count=blocks.count_documents({"of":user_id})
    
    def craft_response(data_obj):
        profile_name=data_obj['profileData'][0]['name']
        if(data_obj['blockFlag']==1):
            profile_name="User Not Found"
        return profile_name
    blocked_profiles_list=list(map(craft_response,blocked_profiles))
    
    return {"blocked":blocked_profiles_list,"count":blocked_profiles_count}



