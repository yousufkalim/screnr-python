# -*- coding: utf-8 -*-
"""
Created on Oct 12 20:35:01 2021

@author: Ahmad
"""

import cv2
import numpy as np
import json

def get_exercise_params(exercise_name):
    
    if exercise_name == "overhead squat":
        exercise_json = "server_data/_overhead_squat.json"
    
    elif exercise_name == "lunge":
        exercise_json = "server_data/_lunges.json"
    
    elif exercise_name == "plank":
        exercise_json = "server_data/_plank.json"
    
    elif exercise_name == "left side bend":
        exercise_json = "server_data/_left_side_bend.json"

    with open(exercise_json, "r") as file:
        exercise_json = json.loads(file.read())
            
    return exercise_json



def get_landmark_ids(landmark_api):
    
    screnr_joint_id_json = "server_data/__screnr_joint_ids.json"

    with open(screnr_joint_id_json, "r") as file:
        screnr_joint_id_json = json.loads(file.read())
    
    if landmark_api == "mediapipe":
        api_joint_id_json = "server_data/__mediapipe_joint_ids.json"
    
    elif landmark_api == "AR Kit":
        api_joint_id_json = ""
    
    elif landmark_api == "ML Kit":
        api_joint_id_json = ""

    with open(api_joint_id_json, "r") as file:
        api_joint_id_json = json.loads(file.read())
            
    return screnr_joint_id_json, api_joint_id_json


def supported_exercises():
    exercises = ["Lunge", "Overhead Squat", "Plank", "Side Bend"]
    dev_exercises = ["Push-ups", "Crunches"]
    
    return exercises, dev_exercises