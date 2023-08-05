import hashlib
import pymongo
import secrets
from datetime import datetime,date

#MongoDb Initialisation
mongo = pymongo.MongoClient("mongodb://localhost:27017/")


#User Login Session Details DB
session=mongo["sessions"]
login_session=session["login"]



def hash_password(p_wrd):
    """
        Returns a Hashed Password    
    """
    p_wrd_hash=hashlib.md5(p_wrd.encode()).hexdigest()
    return p_wrd_hash

def password_matching(p_wrd,u_pwrd):
    """
        Returns True if passwords' hash match
    """
    h_pwrd=hash_password(p_wrd)
    if(h_pwrd!=u_pwrd):
        return False
    return True

def check_login(user_id):
    """
        Check if user is already logged in.
        Returns True and Api_key if user is already loged in
    """
    user_status=login_session.find_one({"user_id":user_id})
    if(user_status!=None):
      return {"api_key":user_status['api_key'],"logged_in":True}
    return {"logged_in":False}


def login_user(user_id,u_p_wrd,u_h_pwrd):
    """
        If passwords don't match then code 40003 returned
        If user is already logged in code 10003 and api key is returned 
        If user is logged in code 10004 and new api key is returned
        Return 5000 if something goes wrong
    """
    p_wrd_match=password_matching(u_p_wrd,u_h_pwrd)
    if(not p_wrd_match):
        return {"code":40003}
    
    already_login=check_login(user_id)
    if(already_login['logged_in']):
        return {"code":10003,"api_key":already_login['api_key']}
    
    api_key=secrets.token_urlsafe(16)
    a=login_session.insert_one({"login_time":datetime.utcnow(),"api_key":api_key,"user_id":user_id}).acknowledged
    if(a):
        return {"code":10004,"api_key":api_key}
    return {"code":5000}



def validate_key(key):
    """
        Validates a key.
    """
    user_status=login_session.find_one({"api_key":key})
    user_status=user_status
    if(user_status==None):
      return {"valid_key":False} 
    return {"valid_key":True,"user_data":user_status}