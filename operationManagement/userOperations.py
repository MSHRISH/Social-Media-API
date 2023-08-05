import pymongo
from datetime import datetime,date


#MongoDb Initialisation
mongo = pymongo.MongoClient("mongodb://localhost:27017/")

#User Details DB
profiles = mongo["socialMediaApp"]
#User Collection
users=profiles["Users"]


def user_exists(u_name):
    """
        Returns code 40001 and user document if user exists.
        Returns code 40002 if user doesn't exist
    """
    user_obj=users.find_one({"name":u_name})
    if(user_obj!= None):
        return{"code":40001,"user_data":user_obj}
    return {"code":40002}


def calculate_age(b_day):
   """
        Calulate Age and returns it
    """
   y=b_day[6:] #Year
   m=b_day[3:5] #Month
   d=b_day[:2] #Date
   b_day=date(int(y),int(m),int(d)) #Date Obj
   t=date.today() #Today date
   age=t.year-b_day.year-((t.month,t.day)<(b_day.month,b_day.day))
   return age


def register_user(user_data):
    """
        Registers a user.Returns True if successful or False if Fails.
    """
    user_data['age']=calculate_age(user_data['dob'])
    status=users.insert_one(user_data).acknowledged
    if(status):
        return True
    return False



#Update Profile
def update_profile(user_id,profile_data):
    """
        Updates the profile.
        Returns code-40001 if the username already exists.
        Returns 10002 on successfull updation
        Returns 5000 on unknown error.
    """
    if("name" in profile_data):
      #Check if the new Name already exists
      name_status=user_exists(profile_data['name'])
      if(name_status['code']==40001):
         return {"code":40001}
    
    if("dob" in profile_data):
      #If DOB is changed,update Age   
      age=calculate_age(profile_data['dob'])
      profile_data['age']=age

    #Update Operation
    update_profile=users.update_one({"_id":user_id},{"$set":profile_data}).acknowledged

    if(update_profile):
       return {"code":10002}

    return {"code":5000}

def show_profile(profile_id):
   profile=users.find_one({"_id":profile_id})
   profile={"name":profile['name'],"dob":profile['dob'],"email":profile['email'],"phn":profile['phn'],"age":profile['age']}
   if(profile==None):
    return {"status":False}
   return {"status":True,"profile_data":profile}