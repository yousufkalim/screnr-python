# -*- coding: utf-8 -*-
"""
Created on Oct 12 20:35:01 2021

@author: Ahmad
"""

import mediapipe as mp
import cv2
import pandas as pd
import numpy as np
import time
from screnr import screnr
from server import get_landmark_ids, supported_exercises
from banner import mp_video_stat_banner
import time
import json


mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

# this class launches video and detects human pose
class mp_video:

    def __init__(self, exercise_name, patient_facing, landmark_api, video_file):
    
        self.exercise_name = exercise_name
        self.patient_facing = patient_facing
        self.landmark_api = landmark_api
       
        # api used for capturing landmarks
        self.landmark_api = landmark_api

        # this will render drawing utilities
        self.mp_drawing = mp.solutions.drawing_utils

        # this brings in the pose estimation model
        self.mp_pose = mp.solutions.pose
        
        # receive video feed and get fps
        self.video_file = video_file
        self.cap = cv2.VideoCapture(video_file)
        self.fps_cv2 = int(round(self.cap.get(cv2.CAP_PROP_FPS), 0))
        self._fourcc = cv2.VideoWriter_fourcc(*'MP4V')

        # detection confidence
        self.detection_confidence = 0.0
        self.tracking_confidence = 0.0

        # feedback on frame
        self.print_feedback_on_frame = ""
        
    @property
    def min_detection_conf(self):
        # this is for the minimum detection confidence
        return self.detection_confidence
        
    @min_detection_conf.setter
    def min_detection_conf(self, value):
        # this is to set minimum detection confidence
        self.detection_confidence = value

    @property
    def min_tracking_conf(self):
        return self.tracking_confidence
        
    @min_tracking_conf.setter
    def min_tracking_conf(self, value):
        self.tracking_confidence = value       
        
    # this will process and launch the video
    def launch(self, loop, sample_pose_coord=1, get_pose_coords=True, drop_pose=True, scale=0):      
        if (self.cap.isOpened()== False): 
            print(f'Error opening {self.video_file}')
        
        else:
            screnr_id_dict, landmark_id_dict = get_landmark_ids(self.landmark_api) # get joint ids from landmark api so joint locations can be obtained
            exercise_ = screnr(self.exercise_name, self.patient_facing, self.landmark_api, landmark_id_dict, screnr_id_dict) # initialize screnr class
            exercise_.read_exercise_packet() # read exercise packet

            # extract joints that should be displayed based on side of the body facing camera
            print(f'Screnr>  exercise = {self.exercise_name}')
            print(f'Screnr>  patient side = {self.patient_facing}')
            print(f'Screnr>  landmark API = {self.landmark_api}')

            frame_counter = 0  # video frame counter
            rep_counter = 0  # exercise repetition counter
            rep_time_elapsed = 0  # timer to time the exercise session
            session_stop_time = 0
            rep_start_time = time.time()
            
            display_dict = {}  # display exercise info (angles, feedback, timer, repetitions) on screen
            feedback = ""  # exercise feedback returned from screnr
            feedback_to_display = ""  # exercise feedback to display on screen
            rep_angles_dict = {}  # holds angle names and their values (in a list form) for each repetition. Sent to the server. 
            feedback_dict = {}  # holds feedback for all rules for each repetition. Sent to the server.
            
            time_threshold = 1.5 # time threshold to show feedback on screen
            timer_on = False
            feedback_flag = 0
            session_report = {}

                        
            with self.mp_pose.Pose(min_detection_confidence=self.detection_confidence, min_tracking_confidence=self.tracking_confidence, model_complexity=1) as pose:          
                while self.cap.isOpened():
                
                    ret, frame = self.cap.read()
                    width = int(frame.shape[1])
                    height = int(frame.shape[0])

                    frame_counter += 1
                    
                    if ret == True:
                    
                        # this will scale the output video to desired ratio
                        if scale>0:
                            width = int(frame.shape[1] * scale)
                            height = int(frame.shape[0] * scale)

                            # image_size
                            image_size = (width, height)

                            # resize image
                            frame = cv2.resize(frame, image_size)

                    # this will get pose coordinates                                
                    if get_pose_coords:
                        
                        # color feed to RGB since that is what mediapipe expects
                        frame.flags.writeable = False
                        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        
                        if frame_counter%sample_pose_coord==0 or frame_counter==1:
                            results = pose.process(frame)

                           #landmarks = results.pose_landmarks
                            landmarks = results.pose_landmarks.landmark
                            exercise_.update_joints(landmarks, image_size)
                            joint_locs_dict = exercise_.get_joints()
                            #angles = exercise_.get_angles() # calculate and get angle values
                            
                        # recolor back to BGR 
                        frame.flags.writeable = True
                        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                        
                        # analyze the rep, get angles and feedback
                        rep_complete, angles, phase, feedback, rep_counter, rep_packet = exercise_.analyze_rep(int(rep_time_elapsed))

                        rep_stop_time = time.time()
                        rep_time_elapsed += rep_stop_time-rep_start_time
                        rep_start_time = rep_stop_time

                        display_dict["Timer (sec)"] = int(rep_time_elapsed)
                        display_dict["Phase"] = phase
                        display_dict["Rep Counter"] = rep_counter

                        for key, value in angles.items():
                            display_dict[key] = value

                        if feedback != "" and timer_on ==False:
                            start_time = time.time()
                            timer_on = True
                            feedback_to_display = feedback
                            
                        if timer_on:
                            stop_time = time.time()
                            time_elapsed = stop_time-start_time
                            
                            if time_elapsed > time_threshold:
                                feedback_to_display = ""
                                timer_on = False

                        if rep_complete:                              
                            session_report["repetition"] = rep_counter
                            session_report["angles"] = rep_packet["angles"]
                            session_report["feedback_dict"] = rep_packet["feedback"]

                            with open('session.json', 'a') as f:
                                json.dump(session_report, f)

                        self.draw_custom_landmarks(frame, joint_locs_dict)
                        frame = mp_video_stat_banner(frame, self.exercise_name, feedback_to_display, display_dict, (60, 62, 66))
                    
                        
                    # show the video
                    cv2.imshow('mediapipe feed', frame)
                    if cv2.waitKey(10) & 0xFF == ord('q'):
                        self.cap.release()
                        cv2.destroyAllWindows()
                        break


    # this function calculates fps and average fps (for size n_sample)
    def calc_fps(self, n_sample, end_time, fps_list):
        start_time = time.time()
        fps = int(round(1/(start_time - end_time), 0))
        fps_list.append(fps)
        end_time = start_time
        avg_fps = 0

        if len(fps_list)>n_sample:
            fps_list.pop(0)
            avg_fps = int(round(sum(fps_list)*1.0/len(fps_list),0))

        return fps, avg_fps, fps_list, end_time


    def draw_custom_landmarks(self, frame, joint_locs_dict, color=(0, 255, 0), line_color=(170, 255, 0)): 
        ''' this draws custom coordinates '''

        # first draw joints on screen (save location in a dictionary)
        joint_locs = {}
        for screnr_joint, screnr_joints in joint_locs_dict.items():        
            if screnr_joints["on_screen"]==True:                
                center_x = screnr_joints["coords"][0] #* image_width
                center_y = screnr_joints["coords"][1] #* image_height
                visibility = screnr_joints["visibility"]
                center1 = (int(center_x), int(center_y)) # calculating point on the image where the joint is
                joint_locs[screnr_joint] = center1

                if visibility>0.50:
                    cv2.circle(frame, center1, 5, color, -1)  # drawing the joint

        '''
        # now connect joints with lines
        for screnr_joint, screnr_info in self.screnr_info["screnr_landmark_map"].items():        
            if screnr_info["on_screen"]==True and len(screnr_info["connected_to"])>0:
                for connected_joint in screnr_info["connected_to"]:
                    cv2.line(frame, joint_locs[screnr_joint], joint_locs[connected_joint], line_color, thickness=1)
        '''



    # this function displays stats on the video
    def on_display(self, img, text, font=cv2.FONT_HERSHEY_PLAIN, pos=(0, 0), font_scale=3, font_thickness=2, text_color=(255, 255, 255), text_color_bg=(0, 0, 0)):
        x, y = pos
        text_size, _ = cv2.getTextSize(text, font, font_scale, font_thickness)
        text_w, text_h = text_size
        cv2.rectangle(img, pos, (x + text_w + 20, y + text_h + 15), text_color_bg, -1)
        cv2.putText(img, text, (x+10, y + 7 + text_h + font_scale - 1), font, font_scale, text_color, font_thickness)

        return text_size



if __name__ == "__main__":

    # -- 0: EOS Cannon
    # -- 1: Logitech webcam
    cannon = 0
    webcam = 1
    
    exercise_list, in_dev_exercise_list = supported_exercises()
    
    # squat   
    #'data\squat_left_student1_new.mp4', 'data\squat_left_student2_new.mp4', 'data\squat_left_JB_new.mp4', 'data\squat_left_Falcon.mp4'

    # planks
    # 'data\Plank_1_right.mp4', 'data\Plank_3_right.mp4'

    # pick an exercise
    # - populate the exercise_list here so patient can select an exercise
    # - exercise_name is user selected exercise
    exercise_name = "overhead squat"  #"lunge"  "overhead squat"  "plank" "left side bend"
    patient_facing = "left"  #"front" "right" "left"
    landmark_api = "mediapipe"  # or AR Kit, or ML Kit
    video_file = 'data\squat_left_JB_new.mp4'

    video_proc1 = mp_video(exercise_name, patient_facing, landmark_api, video_file)
    video_proc1.min_detection_confidence = 0.50
    video_proc1.min_tracking_confidence = 0.50
    video_proc1.launch(loop=False, sample_pose_coord=1, get_pose_coords=True, drop_pose=True, scale=0.50)