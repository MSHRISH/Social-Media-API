from flask import Flask,request
from datetime import datetime,date
import secrets
from flask_swagger_ui import get_swaggerui_blueprint
from bson import ObjectId

from operationManagement import userOperations as userops
from operationManagement import securityOperations as securityops
from operationManagement import relationshipOperations as relationops
from operationManagement import feedOperations as feedops
from operationManagement import postOperations as postops
app = Flask(__name__)


SWAGGER_URL = '/api/docs'  # URL for exposing Swagger UI (without trailing '/')
API_URL = '/static/schema/swagger.json'  # Our API url (can of course be a local resource)

# Call factory function to create our blueprint
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,  # Swagger UI static files will be mapped to '{SWAGGER_URL}/dist/'
    API_URL,
    config={  # Swagger UI config overrides
        'app_name': "Test application"
    },
)
app.register_blueprint(swaggerui_blueprint)


success_responses={10001:"User Created Sucessfully",10002:"Profile Updated Sucessfully",
                   10003:"User already logged in",10004:"User logged in successfully"
                   ,10005:"Follow Successfull",
                   10006:"Unfollow Successfull",
                   10007:"Blocked Successfully",
                   10008:"Unblocked Successfully",
                   10009:"Posted Successfully",
                   10010:"Post Edited",
                   10011:"Post Deleted"

                   ,10012:"Commented",
                   10013:"Liked a post",
                   10014:"Unliked a post",
                   10015:"Likes Found",
                   10016:"Replied",
                   10017:"Comments Found",
                   10018:"Replies Found"
                   }

error_responses={40001:"Username already exists",40002:"Username Doesn't exist",5000:"Unknown Error",
                 40003:"Incorrect Password",40004:"Invalid API Key",
                 40005:"User cannot Follow themself",40006:"User is Already Following the profile",
             40007:"User cannot Unfollow themself",
             40008:"User is not following the profile",
             40009:"User cannot block themself",
             40010:"Profile Blocked Already",
             40011:"User cannot unblock themself",
             40012:"User not blocked the account",
             40013:"User cannot follow a blocked account",
             40014:"User Cannot unfollow a blocked Account",
             40015:"User cannot Visit their Profile using this api",
             40016:"User cannot Visit a blocked profile",
             40017:"Post not ID not found",

             40018:"Comment not Found"
                 }

#Register a User
@app.route("/register",methods=["POST"])
def register():
   """
        Registers a user in the database.
   """
   user_data=request.json #User details
   u_name=user_data['name']
   user_status=userops.user_exists(u_name) #Checking if user name exists
   if(user_status['code']==40001):
      return {"error":error_responses[40001],"code":40001},400
   
   #Hash the password
   user_data['password']=securityops.hash_password(user_data['password'])
   
   #Create a user
   create_user=userops.register_user(user_data)
   if(create_user):
      return {"response":success_responses[10001],"code":10001},200
   return {"error":error_responses[5000],"code":5000},400
   
#Login
@app.route("/login",methods=['POST'])
def login():
   """
        Login the user.
   """
   u_name=request.json['name']
   p_wrd=request.json['password']
   
   user_status=userops.user_exists(u_name) #Checking if user name exists
   if(user_status['code']==40002):
      return {"error":error_responses[40002],"code":40002},400
   user_id=user_status['user_data']['_id'] #Unique ID from user document object

   #login
   login_status=securityops.login_user(user_id,p_wrd,user_status['user_data']['password'])
   if(login_status['code']==40003):
      return {"error":error_responses[40003],"code":40003} , 400
   elif(login_status['code']==10003):
      return {"code":10003,"response":success_responses[10003],"api_Key":login_status['api_key'],"user_name":u_name}
   elif(login_status['code']==10004):
       return {"code":10004,"response":success_responses[10004],"api_Key":login_status['api_key'],"user_name":u_name}
   return {"code":5000,"error":error_responses[5000]},400

#update Profile
@app.route("/editProfile",methods=["POST"])
def edit_profile():
   """
      Update a profile.
   """
   #Key Validation
   key_status=securityops.validate_key(request.headers['key']) 
   if(not key_status['valid_key']):
       return {"error":error_responses[40004],"code":40004} , 400
   user_id=key_status['user_data']['user_id'] #Unique user ID

   #Update
   update_status=userops.update_profile(user_id,request.json)
   if(update_status['code']==40001):
      return {"error":error_responses[40001],"code":40001},400
   elif(update_status['code']==10002):
        return {"response":success_responses[10002],"code":10002} 
   return {"code":5000,"error":error_responses[5000]},400

#Follow a profile
@app.route("/follow",methods=['POST'])
def follow():
   """
      Follow a Profile.
   """
   #Key Validation
   key_status=securityops.validate_key(request.headers['key']) 
   if(not key_status['valid_key']):
       return {"error":error_responses[40004],"code":40004} , 400
   user_id=key_status['user_data']['user_id'] #Unique user ID

   #Check Profile Exists
   profile_status=userops.user_exists(request.json['name'])
   if(profile_status['code']==40002):
      return {"error":error_responses[40002],"code":40002},400
   profile_id=profile_status['user_data']['_id']

   #Check if the user try to follow a blocked profile
   block_status=relationops.check_blocking(user_id,profile_id)
   if(block_status):
          return {"error":error_responses[40013],"code":40013},400
   
   #Check if user is blocked by the profile
   #If user is blocked by the profile then simply return 40002
   block_status=relationops.check_blocking(profile_id,user_id)
   if(block_status):
       return {"error":error_responses[40002],"code":40002},400

   #Follow_Profile
   follow_status=relationops.follow(user_id,profile_id)
   if(follow_status['code']==40005):
      return {"error":error_responses[40005],"code":40005},400
   elif(follow_status['code']==40006):
      return {"error":error_responses[40006],"code":40006},400
   elif(follow_status['code']==10005):
        return {"response":success_responses[10005],"code":10005} 
   return {"code":5000,"error":error_responses[5000]},400
   


#Unfollow a profile
@app.route("/unfollow",methods=['POST'])
def unfollow():
   """
      Unfollow a Profile.
   """
   #Key Validation
   key_status=securityops.validate_key(request.headers['key']) 
   if(not key_status['valid_key']):
       return {"error":error_responses[40004],"code":40004} , 400
   user_id=key_status['user_data']['user_id'] #Unique user ID

   #Check Profile Exists
   profile_status=userops.user_exists(request.json['name'])
   if(profile_status['code']==40002):
      return {"error":error_responses[40002],"code":40002},400
   profile_id=profile_status['user_data']['_id']

   #check if the user try to unfollow a blocked profile
   block_status=relationops.check_blocking(user_id,profile_id)
   if(block_status):
          return {"error":error_responses[40014],"code":40014},400
   
   #Check if user is blocked by the profile
   #If user is blocked by the profile then simply return 40002
   block_status=relationops.check_blocking(profile_id,user_id)
   if(block_status):
       return {"error":error_responses[40002],"code":40002},400

   #Unfollow_Profile
   unfollow_status=relationops.unfollow(user_id,profile_id)
   if(unfollow_status['code']==40007):
      return {"error":error_responses[40007],"code":40007},400
   elif(unfollow_status['code']==40008):
      return {"error":error_responses[40008],"code":40008},400
   elif(unfollow_status['code']==10006):
        return {"response":success_responses[10006],"code":10006} 
   return {"code":5000,"error":error_responses[5000]},400

#Show user profile
@app.route("/myprofile/",methods=['GET'])
def myprofile():
   """
      Shows user profile.
   """
   #Key Validation
   key_status=securityops.validate_key(request.headers['key']) 
   if(not key_status['valid_key']):
       return {"error":error_responses[40004],"code":40004} , 400
   user_id=key_status['user_data']['user_id'] #Unique user ID
   
   # Show Profile
   profile=userops.show_profile(user_id)
   if(profile['status']):
      return profile['profile_data']
   return {"code":5000,"error":error_responses[5000]},400

#visit other profiles
@app.route("/visit")
def visit():
   """
      visit other profiles
   """
   args = request.args
   profile_name = args.get('profile')

   # Key Validation
   key_status=securityops.validate_key(request.headers['key']) 
   if(not key_status['valid_key']):
       return {"error":error_responses[40004],"code":40004} , 400
   user_id=key_status['user_data']['user_id'] #Unique user ID

    #Check Profile Exists
   profile_status=userops.user_exists(profile_name)
   if(profile_status['code']==40002):
      return {"error":error_responses[40002],"code":40002},400
   profile_id=profile_status['user_data']['_id']

   #Check if the user try to view a blocked profile
   block_status=relationops.check_blocking(user_id,profile_id)
   if(block_status):
          return {"error":error_responses[40016],"code":40016},400
   
   #Check if user is blocked by the profile
   #If user is blocked by the profile then simply return 40002
   block_status=relationops.check_blocking(profile_id,user_id)
   if(block_status):
       return {"error":error_responses[40002],"code":40002},400

   # Show Profile 
   profile=userops.show_profile(profile_id)
   if(profile['status']):
      return profile['profile_data']
   return {"code":5000,"error":error_responses[5000]},400

#Show MyFollowers
@app.route("/myFollowers")
def my_followers():
   """
      Returns user's followers according to the page.
   """
   # Key Validation
   key_status=securityops.validate_key(request.headers['key']) 
   if(not key_status['valid_key']):
       return {"error":error_responses[40004],"code":40004} , 400
   user_id=key_status['user_data']['user_id'] #Unique user ID
   
   #Setting Pagination
   args = request.args
   page = args.get('page')
   if(page==None):
      page=1
   
   return relationops.user_followers(user_id,int(page))

#User's following
@app.route("/myFollowings")
def my_followings():
   """
      Return Followings of the user with pages.
   """
   # Key Validation
   key_status=securityops.validate_key(request.headers['key']) 
   if(not key_status['valid_key']):
       return {"error":error_responses[40004],"code":40004} , 400
   user_id=key_status['user_data']['user_id'] #Unique user ID
   
   #Setting Pagination
   args = request.args
   page = args.get('page')
   if(page==None):
      page=1
   
   return relationops.user_followings(user_id,int(page))

@app.route("/showFollowings")
def show_followings():
    # Key Validation
   key_status=securityops.validate_key(request.headers['key']) 
   if(not key_status['valid_key']):
       return {"error":error_responses[40004],"code":40004} , 400
   user_id=key_status['user_data']['user_id'] #Unique user ID

   #Setting Pagination
   args = request.args
   page = args.get('page')
   if(page==None):
      page=1

   #Check Profile Exists
   profile_name=args.get("profile")
   profile_status=userops.user_exists(profile_name)
   if(profile_status['code']==40002):
      return {"error":error_responses[40002],"code":40002},400
   profile_id=profile_status['user_data']['_id']

    #Check if the user try to view a blocked profile
   block_status=relationops.check_blocking(user_id,profile_id)
   if(block_status):
          return {"error":error_responses[40016],"code":40016},400
    #Check if user is blocked by the profile
   #If user is blocked by the profile then simply return 40002
   block_status=relationops.check_blocking(profile_id,user_id)
   if(block_status):
       return {"error":error_responses[40002],"code":40002},400

   if(user_id==profile_id):
       return {"error":error_responses[40015],"code":40015} , 400

   return relationops.show_followings(user_id,profile_id,int(page))

@app.route('/showFollowers')
def show_followers():
    # Key Validation
   key_status=securityops.validate_key(request.headers['key']) 
   if(not key_status['valid_key']):
       return {"error":error_responses[40004],"code":40004} , 400
   user_id=key_status['user_data']['user_id'] #Unique user ID

   #Setting Pagination
   args = request.args
   page = args.get('page')
   if(page==None):
      page=1

   #Check Profile Exists
   profile_name=args.get("profile")
   profile_status=userops.user_exists(profile_name)
   if(profile_status['code']==40002):
      return {"error":error_responses[40002],"code":40002},400
   profile_id=profile_status['user_data']['_id']

     #Check if the user try to view a blocked profile
   block_status=relationops.check_blocking(user_id,profile_id)
   if(block_status):
          return {"error":error_responses[40016],"code":40016},400
    #Check if user is blocked by the profile
   #If user is blocked by the profile then simply return 40002
   block_status=relationops.check_blocking(profile_id,user_id)
   if(block_status):
       return {"error":error_responses[40002],"code":40002},400


   if(user_id==profile_id):
       return {"error":error_responses[40015],"code":40015} , 400

   return relationops.show_followers(user_id,profile_id,int(page))

#Block a user
@app.route("/block")
def block_profile():
      # Key Validation
   key_status=securityops.validate_key(request.headers['key']) 
   if(not key_status['valid_key']):
       return {"error":error_responses[40004],"code":40004} , 400
   user_id=key_status['user_data']['user_id'] #Unique user ID

   args = request.args
   #Check Profile Exists
   profile_name=args.get("profile")
   profile_status=userops.user_exists(profile_name)
   if(profile_status['code']==40002):
      return {"error":error_responses[40002],"code":40002},400
   profile_id=profile_status['user_data']['_id']

   #Block_profile
   block_status=relationops.block(user_id,profile_id)
   if(block_status['code']==40009):
      return {"error":error_responses[40009],"code":40009},400
   elif(block_status['code']==40010):
      return {"error":error_responses[40010],"code":40010},400
   elif(block_status['code']==10007):
        return {"response":success_responses[10007],"code":10007} 
   return {"code":5000,"error":error_responses[5000]},400
   
#Unblock a user
@app.route("/unblock")
def unblock_profile():
        # Key Validation
   key_status=securityops.validate_key(request.headers['key']) 
   if(not key_status['valid_key']):
       return {"error":error_responses[40004],"code":40004} , 400
   user_id=key_status['user_data']['user_id'] #Unique user ID

   args = request.args
   #Check Profile Exists
   profile_name=args.get("profile")
   profile_status=userops.user_exists(profile_name)
   if(profile_status['code']==40002):
      return {"error":error_responses[40002],"code":40002},400
   profile_id=profile_status['user_data']['_id']

   #Unblock Profile
   unblock_status=relationops.unblock(user_id,profile_id)
   if(unblock_status['code']==40011):
       return {"error":error_responses[40011],"code":40011},400
   elif(unblock_status['code']==40012):
       return {"error":error_responses[40012],"code":40012},400
   elif(unblock_status['code']==10008):
        return {"response":success_responses[10008],"code":10008} 
   return {"code":5000,"error":error_responses[5000]},400
   


#Get blocked profiles list
@app.route("/blockedProfile")
def blocked_profiles():
   """
      Get a list of profiles that are blocked by ther user.
      If the profile has blocked the user then dont show it.
   """
    # Key Validation
   key_status=securityops.validate_key(request.headers['key']) 
   if(not key_status['valid_key']):
       return {"error":error_responses[40004],"code":40004} , 400
   user_id=key_status['user_data']['user_id'] #Unique user ID
   
   #Setting Pagination
   args = request.args
   page = args.get('page')
   if(page==None):
      page=1
   
   return relationops.user_blocked_profiles(user_id,int(page))


#Post into Feed
@app.route("/postContent",methods=['POST'])
def post_feed():
   """
      Allows a user to post content.
   """
   # Key Validation
   key_status=securityops.validate_key(request.headers['key']) 
   if(not key_status['valid_key']):
       return {"error":error_responses[40004],"code":40004} , 400
   user_id=key_status['user_data']['user_id'] #Unique user ID

   
   post_content_status=postops.post_content(user_id,request.json['postContent'])
   if(post_content_status):
      return {"response":success_responses[10009],"code":10009},200
   return {"error":error_responses[5000],"code":5000},400
   
#My posts
@app.route("/myPosts")
def my_posts():
     # Key Validation
   key_status=securityops.validate_key(request.headers['key']) 
   if(not key_status['valid_key']):
       return {"error":error_responses[40004],"code":40004} , 400
   user_id=key_status['user_data']['user_id'] #Unique user ID

      #Setting Pagination
   args = request.args
   page = args.get('page')
   if(page==None):
      page=1

   return postops.user_posts(user_id,int(page))

#Edit post
@app.route("/editPost",methods=["POST"])
def edit_post():
   """
      Allows the user to edit the post posted by only them.
   """
         # Key Validation
   key_status=securityops.validate_key(request.headers['key']) 
   if(not key_status['valid_key']):
       return {"error":error_responses[40004],"code":40004} , 400
   user_id=key_status['user_data']['user_id'] #Unique user ID

   post_id=request.json['postId']
   post_data=request.json['postData']

   edit_status=postops.edit_post_content(user_id,post_id,post_data)
   if(edit_status['code']==40017):
       return {"error":error_responses[40017],"code":40017} , 400
   elif(edit_status['code']==10010):
      return {"response":success_responses[10010],"code":10010},200
   return {"error":error_responses[5000],"code":5000},400

#Delete Post
@app.route("/deletePost",methods=["POST"])
def delete_post():
   """
      Delete a post by user.
   """
             # Key Validation
   key_status=securityops.validate_key(request.headers['key']) 
   if(not key_status['valid_key']):
       return {"error":error_responses[40004],"code":40004} , 400
   user_id=key_status['user_data']['user_id'] #Unique user ID

   post_id=request.json['postId']

   del_status=postops.remove_post(user_id,post_id)
   if(del_status['code']==40017):
       return {"error":error_responses[40017],"code":40017} , 400
   elif(del_status['code']==10011):
      return {"response":success_responses[10011],"code":10011},200
   return {"error":error_responses[5000],"code":5000},400
   
       
#User's feed
@app.route("/myFeed")
def my_feed():
   """
      Show a list of post to user.
   """
                # Key Validation
   key_status=securityops.validate_key(request.headers['key']) 
   if(not key_status['valid_key']):
       return {"error":error_responses[40004],"code":40004} , 400
   user_id=key_status['user_data']['user_id'] #Unique user ID

      #Setting Pagination
   args = request.args
   page = args.get('page')
   if(page==None):
      page=1

   return feedops.user_feed(user_id,int(page))


#Commenting on a post
@app.route("/comment",methods=['POST'])
def comment_post():
   """
      Comments on a post
   """
   key_status=securityops.validate_key(request.headers['key']) 
   if(not key_status['valid_key']):
       return {"error":error_responses[40004],"code":40004} , 400
   user_id=key_status['user_data']['user_id'] #Unique user ID

   post_id=request.json['postID']
   comment_content=request.json['comment']
   
   comment=feedops.user_comment(post_id,user_id,comment_content)

   if(comment['code']==40017):
       return {"error":error_responses[40017],"code":40017} , 400
   elif(comment['code']==10012):
      return {"response":success_responses[10012],"code":10012},200
   return {"error":error_responses[5000],"code":5000} , 400
   



@app.route("/likePost",methods=['POST'])
def like_post():
   """
      Like Button of the post.Allows user to like and unlike the post.
   """
   key_status=securityops.validate_key(request.headers['key']) 
   if(not key_status['valid_key']):
       return {"error":error_responses[40004],"code":40004} , 400
   user_id=key_status['user_data']['user_id'] #Unique user ID

   post_id=request.json['postID']
   like_status=feedops.like_unlike_post(post_id,user_id)
   if(like_status['code']==40017):
       return {"error":error_responses[40017],"code":40017} , 400
   elif(like_status['code']==10013):
      return {"response":success_responses[10013],"code":10013},200
   elif(like_status['code']==10014):
      return {"response":success_responses[10014],"code":10014},200
   return {"error":error_responses[5000],"code":5000} , 400

#Show the list of profiles that liked a post
@app.route("/showLikes")
def show_likes():
    key_status=securityops.validate_key(request.headers['key']) 
    if(not key_status['valid_key']):
        return {"error":error_responses[40004],"code":40004} , 400
    user_id=key_status['user_data']['user_id'] #Unique user ID

        #Setting Pagination
    args = request.args
    page = args.get('page')
    if(page==None):
       page=1

    get_likers=feedops.likes_of_post(args.get("postId"),user_id,int(page))
    if(get_likers['code']==40017):
       return {"error":error_responses[40017],"code":40017} , 400
    return get_likers

#Allows user to reply to as post
@app.route("/reply",methods=['POST'])
def reply_comment():
    key_status=securityops.validate_key(request.headers['key']) 
    if(not key_status['valid_key']):
        return {"error":error_responses[40004],"code":40004} , 400
    user_id=key_status['user_data']['user_id'] #Unique user ID
    
    comment_id=request.json['commentID']
    reply_content=request.json['reply']

    reply_status=feedops.user_reply(comment_id,user_id,reply_content)

    if(reply_status['code']==40018):
        return {"error":error_responses[40018],"code":40018} , 400
    elif(reply_status['code']==10016):
      return {"response":success_responses[10016],"code":10016},200
    return {"error":error_responses[5000],"code":5000} , 400
    

#Comment Section
@app.route("/showComments")
def show_comments():
   key_status=securityops.validate_key(request.headers['key']) 
   if(not key_status['valid_key']):
       return {"error":error_responses[40004],"code":40004} , 400
   user_id=key_status['user_data']['user_id'] #Unique user ID

        #Setting Pagination
   args = request.args
   page = args.get('page')
   if(page==None):
       page=1
   
   post_id=args.get("postId")

   get_comments=feedops.show_post_comments(post_id,user_id,int(page))
   if(get_comments['code']==40018):
       return {"error":error_responses[40018],"code":40018} , 400
   return get_comments
       

#Show Replies for a comment
@app.route("/showReplies")
def show_replies():
   key_status=securityops.validate_key(request.headers['key']) 
   if(not key_status['valid_key']):
       return {"error":error_responses[40004],"code":40004} , 400
   user_id=key_status['user_data']['user_id'] #Unique user ID

        #Setting Pagination
   args = request.args
   page = args.get('page')
   if(page==None):
       page=1
   comment_id=args.get("commentId")

   reply_data=feedops.replies_of_comment(comment_id,user_id,int(page))

   if(reply_data['code']==40018):
       return {"error":error_responses[40018],"code":40018} , 400
   return reply_data
       

   
    
       
       
    
       
       



    













if __name__ == '__main__':
   app.debug = True
   app.run()