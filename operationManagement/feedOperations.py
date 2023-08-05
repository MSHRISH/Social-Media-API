import pymongo
from bson import ObjectId
import random

#MongoDb Initialisation
mongo = pymongo.MongoClient("mongodb://localhost:27017/")

#User DB
profiles = mongo["socialMediaApp"]
users=profiles["Users"]

#Followers Collection
followers=profiles["followers"]
blocks=profiles['blocks']
posts=profiles['posts']
comments=profiles['comments']
likes=profiles['likes']
replies=profiles['replies']

#To check if it is a valid object id
def is_valid_objectid(string):
    try:
        ObjectId(string)
        return True
    except Exception:
        return False


#Show the feed to the user
def user_feed(user_id,page):
    """
        Retruns a set of posts from the followings of the user.
    """
    following_pipeline=[
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
            "$match":{"blockFlag":[]}
        },
        {
            "$project":{
                "_id":0,
                "to":1
            }
        }
    ]

    #Valid Following list
    valid_following=list(followers.aggregate(following_pipeline))
    def valid_followings_id(data_object):
        return data_object['to']
    valid_following=list(map(valid_followings_id,valid_following))

    #Posts from the valid followings
    post_pipeline=[
    {
        "$match":{"by":{"$in":valid_following}}
    },
    {"$skip":(page-1)*5},
    {"$limit":5},
    {
        "$lookup":{
            "from":"Users",
            "localField":"by",
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
    posts_list = list(posts.aggregate(post_pipeline))
    # random.shuffle(posts_list)

    def craft_response(data_object):
        return {"postID":str(data_object['_id']),"PostedBy":data_object['profileData'][0]['name'],"post":data_object['content']}
    response_data=list(map(craft_response,posts_list))

    return {"posts":response_data}

#Comment on a post
def user_comment(post_id,user_id,comment_content):
    """
        Commentts on a post
        Return 40017 if postid not valid.
        Return 40017 if post not found.
        Return 40017 if user blocked the poster or if poster blocked the user.
        Return 10012 on success.
    """
    valid_post_id=is_valid_objectid(post_id)
    if(not valid_post_id):
        return {"code":40017}
    post_id=ObjectId(post_id)
    post_details=posts.find_one({"_id":post_id})
    if(post_details== None):
        return {"code":40017}
    blocking=blocks.find_one({"$or":[{"of":user_id,"to":post_details['by']},{"of":post_details['by'],"to":user_id}]})
    if(blocking!=None):
        return {"code":40017}
    post_comment=comments.insert_one({"by":user_id,"post_id":post_id,"comment":comment_content}).acknowledged
    if(not post_comment):
        return {"code":5000}
    return {"code":10012}

#To check if the post exists in user's access
def post_exists(post_id,user_id):
    """
        This a collective functon to check if a post exist under user's access.
    """
    #Check if it is a valid string litertal of ObjectId
    valid_post_id=is_valid_objectid(post_id)
    if(not valid_post_id):
        return False
    post_id=ObjectId(post_id)
    #Check if  post exists in db
    post_details=posts.find_one({"_id":post_id})
    if(post_details== None):
        return False
    
    #Check permissions
    blocking=blocks.find_one({"$or":[{"of":user_id,"to":post_details['by']},{"of":post_details['by'],"to":user_id}]})
    if(blocking!=None):
        return False
    return True
    


#Show a list profiles liked a post
def likes_of_post(post_id,user_id,page):
    """
        Checks if the post_id is valid.
        Return 40017 on invalid.
        Return Liker profile list.
    """
    valid_post=post_exists(post_id,user_id)
    if(not valid_post):
        return {"code":40017}
    post_id=ObjectId(post_id)


    pipeline=[
        {    #Find the post
            "$match":{"postId":post_id}
        },
        {       #Find followed by you
            "$lookup":{
                    "from":"followers",
                    "localField":"by",
                    "foreignField":"to",
                    "pipeline":[
                        {
                            "$match":{"of":user_id}
                        }
                    ],
                    "as":"followedByUser"
            }
        },
        {   #Find blocked by you
            "$lookup":{
                "from":"blocks",
                "localField":"by",
                "foreignField":"to",
                "pipeline":[
                    {
                        "$match":{"of":user_id}
                    }
                ],
                "as":"blockedByUser"
            }
        },
        {   #Find blocked the user
            "$lookup":{
                "from":"blocks",
                "localField":"by",
                "foreignField":"of",
                "pipeline":[
                    {
                        "$match":{"to":user_id}
                    }
                ],
                "as":"blockedTheUser"
            }
        },
        {     #Mark flags
            "$project":{
                "_id":0,
                "by":"$by",
                "followedByUser":{
                    "$cond":{
                        "if":{"$gt":[{"$size":"$followedByUser"},0]},
                        "then":1,
                        "else":0
                    }
                },
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
        {"$sort":{"youFlag":-1,"blockedByUser":1,"blockedTheUser":1,"followedByUser":-1}},
        {"$skip":(page-1)*5},
        {"$limit":5},
        {       #Lookup names
            "$lookup":{
                "from":"Users",
                "localField":"by",
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

    likers=list(likes.aggregate(pipeline))
    
    def craft_response(data_object):
        profile_name=data_object['profileData'][0]['name']
        if(data_object['blockedByUser']==1 or data_object['blockedTheUser']==1):
            profile_name="User Not Found"
        elif(data_object['followedByUser']==1):
            profile_name+="[FBY]"
        elif(data_object['by']==user_id):
            print(data_object)
            profile_name+="[YOU]"
        return profile_name
    
    likers_list=list(map(craft_response,likers))
    actual_likes_count=likes.count_documents({"postId":post_id})
    return {"LikedBy":likers_list,"code":10015,"likes":actual_likes_count}



#Like or unlike a post
def like_unlike_post(post_id,user_id):
    """
        Return 40017
            if postId not valid
            if post not found
            if post is from blocked or blocker profile
        Return 10013 on like
        Return 10014 on unlike
    """
    valid_id=is_valid_objectid(post_id)
    if(not valid_id):
        return {"code":40017}
    post_id=ObjectId(post_id)

    post_details=posts.find_one({"_id":post_id})
    if(post_details==None):
        return {"code":40017}
    
    blocking=blocks.find_one({"$or":[{"of":user_id,"to":post_details['by']},{"of":post_details['by'],"to":user_id}]})
    if(blocking!=None):
        return {"code":40017}
    
    already_liked=likes.find_one({"postId":post_id,"by":user_id})
    if(already_liked==None):
        like_post=likes.insert_one({"postId":post_id,"by":user_id}).acknowledged
        if(like_post):
            return {"code":10013}
        return {'code':5000}
    
    unlike_post=likes.delete_one({"by":user_id,"postId":post_id}).acknowledged
    if(unlike_post):
        return {"code":10014}
    return {"code":5000}


def is_valid_comment(comment_id,user_id):
    """
        Check whether the id is valid and access check.
    """
        #Check if it is a valid string litertal of ObjectId
    valid_comment_id=is_valid_objectid(comment_id)
    if(not valid_comment_id):
        return False
    comment_id=ObjectId(comment_id)

    #Check if comment exists
    comment_details=comments.find_one({"_id":comment_id})
    if(comment_details == None):
        return False
    
    post_details=posts.find_one({"_id":comment_details['post_id']})
    
    #Check blockings
    commenter_blocking=blocks.find_one({"$or":[{"of":user_id,"to":comment_details['by']},{"of":comment_details['by'],"to":user_id},{"of":user_id,"to":post_details['by']},{"of":post_details['by'],"to":user_id}]})
    if(commenter_blocking!=None):
        return False
    return True    
    

#reply to a comment
def user_reply(comment_id,user_id,reply_content):
    """
        Allows a user to reply to a comment.
        Return 40018 if error
        Return 10016 on success
    """
    valid_comment_id=is_valid_comment(comment_id,user_id)
    if(not valid_comment_id):
        return {"code":40018}
    comment_id=ObjectId(comment_id)
    reply=replies.insert_one({"by":user_id,"replyContent":reply_content,"commentId":comment_id}).acknowledged
    if(reply):
        return {"code":10016}
    return {"code":5000}


#Show comments
def show_post_comments(post_id,user_id,page):
    """
        Allows user to visitcomment section.
        Returns 40018 on invalid access of post.
        Returns a list of comments and 10017
    """
    post_status=post_exists(post_id,user_id)
    if(not post_status):
        return {"code":40018}
    post_id=ObjectId(post_id)
    pipeline=[
    {   #Find all comments
        "$match":{"post_id":post_id}
    },
    {   #You Flag
        "$project":{
            "_id":"$_id",
            "by":"$by",
            "comment":"$comment",
            "youFlag":{
                "$cond":{
                    "if":{"$eq":["$by",user_id]},
                    "then":1,
                    "else":0
                }
            }
        }
    },
    {   #Following by you flag
        "$lookup":{
            "from":"followers",
            "localField":"by",
            "foreignField":"to",
            "pipeline":
                [
                    {
                        "$match":{"of":user_id}
                    },
                    {
                        "$project":{
                            "_id":0,
                        }
                    }
                ],
            
            "as":"followedByUser"
        }
    },
    {   #Blocked by user
        "$lookup":{
            "from":"blocks",
            "localField":"by",
            "foreignField":"to",
            "pipeline":[
                {
                    "$match":{"of":user_id}
                }
            ],
            "as":"blockedByUser"
        }
    },
    {   #Blocked the user
        "$lookup":{
            "from":"blocks",
            "localField":"by",
            "foreignField":"of",
            "pipeline":[
                {
                    "$match":{"to":user_id}
                }
            ],
            "as":"blockedTheUser"
        }

    },
    {   #Make Flags
        "$project":{
            "_id":"$_id",
            "by":"$by",
            "youFlag":"$youFlag",
            "comment":"$comment",
            "followedByUser":{
                "$cond":{
                    "if":{"$gt":[{"$size":"$followedByUser"},0]},
                    "then":1,
                    "else":0
                }
            },
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
    {"$sort":{"youFlag":-1,"followedByUser":-1,"blockedByUser":1,"blockedTheUser":1}},
    {"$skip":(page-1)*5},
    {"$limit":5},
    {   #Lookup names
        "$lookup":{
            "from":"Users",
            "localField":"by",
            "foreignField":"_id",
            "pipeline":[
                {
                    "$project":{
                        "_id":0,
                        "name":1
                    }
                }
            ],
            "as":"profileDetails"
        }
    },
    {   #No.of Replies
        "$lookup":{
            "from":"replies",
            "localField":"_id",
            "foreignField":"commentId",
            "as":"replies"
        }

    },  
    {   #Get count
        "$addFields":{"replies":{"$size":"$replies"}}
        }
    ]

    comments_data=list(comments.aggregate(pipeline))

    def craft_response(data_object):
        profile_name=data_object['profileDetails'][0]['name']
        comment_content=data_object['comment']
        replies=data_object['replies']
        if(data_object['youFlag']==1):
            return {"comment_id":str(data_object['_id']),"comment":comment_content,"by":profile_name+"[YOU]","replies":replies}
        elif(data_object['blockedByUser']==1 or data_object['blockedTheUser']==1):
            return {"comment":"COMMENT NOT FOUND","by":"USER NOT FOUND"}
        elif(data_object['followedByUser']==1):
            return {"comment_id":str(data_object['_id']),"comment":comment_content,"by":profile_name+"[FBY]","replies":replies}
        
        return {"comment_id":str(data_object['_id']),"comment":comment_content,"by":profile_name,"replies":replies}
    comments_list=list(map(craft_response,comments_data))

    actual_comments_count=comments.count_documents({"post_id":post_id})

    return {"code":10017,"comments":comments_list,"count":actual_comments_count}



#Show replies under a comment
def replies_of_comment(comment_id,user_id,page):
    """
        Allows user to get replies under a comment.
        Returns 40018 if invalid access.
        Returns code 10018 on success with a list of replies.
    """
    comment_access=is_valid_comment(comment_id,user_id)
    if(not comment_access):
        return {"code":40018}
    comment_id=ObjectId(comment_id)

    pipeline=[
        {
            "$match":{"commentId":comment_id}
        },
        {   #Following by you flag
        "$lookup":{
            "from":"followers",
            "localField":"by",
            "foreignField":"to",
            "pipeline":
                [
                    {
                        "$match":{"of":user_id}
                    },
                    {
                        "$project":{
                            "_id":0,
                        }
                    }
                ],
            
            "as":"followedByUser"
        }
    },
    {   #Blocked by user
        "$lookup":{
            "from":"blocks",
            "localField":"by",
            "foreignField":"to",
            "pipeline":[
                {
                    "$match":{"of":user_id}
                }
            ],
            "as":"blockedByUser"
        }
    },
    {   #Blocked the user
        "$lookup":{
            "from":"blocks",
            "localField":"by",
            "foreignField":"of",
            "pipeline":[
                {
                    "$match":{"to":user_id}
                }
            ],
            "as":"blockedTheUser"
        }

    },
    {   #Make Flags
        "$project":{
            "_id":"$_id",
            "by":"$by",
            "youFlag":{
                "$cond":{
                    "if":{"$eq":["$by",user_id]},
                    "then":1,
                    "else":0
                }

            },
            "reply":"$replyContent",
            "followedByUser":{
                "$cond":{
                    "if":{"$gt":[{"$size":"$followedByUser"},0]},
                    "then":1,
                    "else":0
                }
            },
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
     {"$sort":{"youFlag":-1,"followedByUser":-1,"blockedByUser":1,"blockedTheUser":1}},
    {"$skip":(page-1)*5},
    {"$limit":5},
    {   #Lookup names
        "$lookup":{
            "from":"Users",
            "localField":"by",
            "foreignField":"_id",
            "pipeline":[
                {
                    "$project":{
                        "_id":0,
                        "name":1
                    }
                }
            ],
            "as":"profileDetails"
        }
    },
    ]

    reply_data=list(replies.aggregate(pipeline))

    def craft_response(data_object):
        profile_name=data_object['profileDetails'][0]['name']
        reply_content=data_object['reply']
        if(data_object['youFlag']==1):
            return {"reply_id":str(data_object['_id']),"reply":reply_content,"by":profile_name+"[YOU]"}
        elif(data_object['blockedByUser']==1 or data_object['blockedTheUser']==1):
            return {"reply":"REPLY NOT FOUND","by":"USER NOT FOUND"}
        elif(data_object['followedByUser']==1):
            return {"reply_id":str(data_object['_id']),"reply":reply_content,"by":profile_name+"[FBY]"}
        
        return {"reply_id":str(data_object['_id']),"reply":reply_content,"by":profile_name}
    reply_list=list(map(craft_response,reply_data))

    actual_reply_count=replies.count_documents({"commentId":comment_id})

    return {"code":10018,"replies":reply_list,"count":actual_reply_count}
