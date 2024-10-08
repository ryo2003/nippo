import os, sys
from bson import ObjectId
import streamlit as st
from pymongo import MongoClient
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '/app/utils/')))
from vector_search import create_embedding
from dotenv import load_dotenv
load_dotenv()
mongo_URI = os.getenv("MONGO_URI")
import datetime

dt_now = datetime.datetime.now()
# Connect to MongoDB
client = MongoClient(mongo_URI)
db = client["mydb"]  # Replace with your database name

from bson import ObjectId
import datetime

def nippo_exist(event_data):
    collection = db["nippo"]
    events = db["event"]
    event_time = event_data["start"]
    # Check if the event already has a nippo_id
    event = events.find_one({"_id": ObjectId(event_data["id"])})
    existing_nippo_id = event.get("nippo_id")
    return existing_nippo_id

    # If a nippo_id already exists, prompt for overwrite confirmation
def submit_byhands_new(submit_data, submit_user_id, event_data,exist_id):
    # submit_data is a dictionary containing data user input on createbyhands page
    collection = db["nippo"]
    events = db["event"]
    event_time = event_data["start"]

    if exist_id != None:
        # Delete the old nippo document
        collection.delete_one({"_id": exist_id})


    newdata = {
        "user_id": submit_user_id,
        "event_id": ObjectId(event_data["id"]),
        "contents": submit_data["本文"],
        "good": [],
        "bookmark":[],
        "purpose":submit_data["訪問目的"],
        "customer":submit_data["企業名"],
        "chat_log_id":None,
        "timestamp":dt_now,
        "event_time":datetime.datetime.fromisoformat(event_time),
        "embedding":create_embedding(submit_data["本文"],submit_data["訪問目的"])
    }
    #collection.insert_one(newdata)

    # Inserting the new document into the nippo collection
    nippo_result = collection.insert_one(newdata)
    
    # Fetching the newly created _id from nippo collection
    nippo_id = nippo_result.inserted_id

    # Updating the event document with the new nippo_id
    events.update_one(
        {"_id": ObjectId(event_data["id"])},
        {"$set": {"nippo_id": nippo_id}}
    )

    
def insert_chat(event_id,user_id):
    try:
        collection = db["chat_log"]
        data={
            "user_id":user_id
        }
        res = collection.collection.insert_one(data)
        print(type(res._id))
        update_data = {
        "$set": {
            "chatlog_id":  ObjectId(res._id)
            }
        }
        result = collection.update_one({"_id": ObjectId(event_id)}, update_data)
        return res["_id"]
    except:
        return 0

def insert_event(user_id, company_name, start_time, end_time, address, purpose):
    
    events = db["event"]
    chatlogs = db["chat_log"]
    new_event = {
        "user_id": user_id,
        "customer": company_name,
        "start_time": start_time,
        "end_time": end_time,
        "address": address,
        "purpose": purpose
    }

    result = events.insert_one(new_event)

    event_id = result.inserted_id
    
    new_chatlog = {
        "user_id": ObjectId(user_id),
        "event_id": ObjectId(event_id),
        "log_data": [],
        "category": purpose,
    }

    chatlog_result = chatlogs.insert_one(new_chatlog)
    chatlog_id = chatlog_result.inserted_id
    events.update_one(
        {"_id": ObjectId(event_id)},
        {"$set": {"chatlog_id": ObjectId(chatlog_id)}}
    )


    st.success("新しいイベントを登録しました!")
    