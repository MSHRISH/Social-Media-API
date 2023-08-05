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

#To check if it is a valid object id
def is_valid_objectid(string):
    try:
        ObjectId(string)
        return True
    except Exception:
        return False



#Post a content by a user
def post_content(user_id,content):
    """
        Posts a content by user in database.
        Schema:
            by-user_id
            content-content
    """
    post_status=posts.insert_one({"by":user_id,"content":content}).acknowledged
    if(post_status):
        return True
    return False








#User_posts
def user_posts(user_id,page):
    """
        Gives the list of possts posted by the user with pagination.
        a post object contains post id a nd post content.
        Post id is used to edit the post or delete it.
    """
    pipeline=[
        {
            "$match":{"by":user_id}
        },
        {"$skip":(page-1)*5},
        {"$limit":5},
    ]

    post_data=list(posts.aggregate(pipeline))
    post_list=[]

    def craft_response(data_obj):
        return {"postId":str(data_obj['_id']),"postData":data_obj['content']}
    post_list=list(map(craft_response,post_data))

    # for i in post_data:
    #     post_object={"postId":str(i['_id']),"postData":i['content']}
    #     post_list.append(post_object)
    count_post=posts.count_documents({"by":user_id})

    return {"posts":post_list,"count":count_post}


#Edit a post by user
def edit_post_content(user_id,post_id,post_data):
    """
        Allows user to edit a post
        Returns error if post id is not valid
        Returns error if post is not found
        Doesnt allow user to edit other peoples post.
        Returns success code 10010 on success
    """
    valid_id=is_valid_objectid(post_id)
    post_id=ObjectId(post_id)
    if(not valid_id):
        return {"code":40017}
    post_by_user=posts.find_one({"by":user_id,"_id":post_id})
    if(post_by_user==None):
        return {"code":40017}
    edit_post=posts.update_one({"by":user_id,"_id":post_id},{"$set":{"by":user_id,"content":post_data}}).acknowledged
    if(edit_post):
        return {"code":10010}
    return {"code":5000}    


#Delete a post by user
def remove_post(user_id,post_id):
    """
        Allows a user to delete the posts made by them.
        Return 40017 if post_id is not valid or if the post_id is wrong.
        Return 10011 if
    """
    valid_id=is_valid_objectid(post_id)
    post_id=ObjectId(post_id)
    if(not valid_id):
        return {"code":40017}
    post_by_user=posts.find_one({"by":user_id,"_id":post_id})
    if(post_by_user==None):
        return {"code":40017}
    del_status=posts.delete_one ({"_id":post_id}).acknowledged
    if(del_status):
        return {"code":10011} 
    return {"code":5000}