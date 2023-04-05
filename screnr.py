# -*- coding: utf-8 -*-
"""
Created on Oct 12 20:35:01 2021

@author: Ahmad
"""

import numpy as np
from server import get_exercise_params
import random


# this class handles all exercises
class screnr:
    '''
        This class manages exercise packets for the exercise being performed
        Inputs: 
            - exercise_name  -- name of the exercise
            - patient_facing -- patient's side facing the camera ("left", "right", "front")
            - landmark_api   -- landmark api ("mediapipe", "AR kit", "ML kit")
        Outputs:
            - screnr_landmark_map  -- maps screnr joints to mediapipe, AR kit, ML kit joints.
            - screnr_landmark_map  -- maps screnr joints to mediapipe, AR kit, ML kit joints.
            - screnr_landmark_map  -- maps screnr joints to mediapipe, AR kit, ML kit joints.
            
    '''
    

    def __init__(self, exercise_name, patient_facing, landmark_api, landmark_id_dict, screnr_id_dict):
    
        self.exercise_name = exercise_name
        self.patient_facing = patient_facing
        self.landmark_api = landmark_api  # name of the API
        self.landmark_id_dict = landmark_id_dict # landmark ids for the API being used
        self.screnr_id_dict = screnr_id_dict # landmark ids for screnr

        #--------------------------------------------------------------------------------------------------------------------------------------------------
        self.display_joints = [] # joints to be displayed on screen (read from exercise packet)
        
        self.rep_angles_dict = {} # this collects values of each angle (angle dictionary and values are a list) within each rep
        self.joint_angles = {}  # this holds values for each joint angle that are needed for the exercise (angle joint info read from exercise packet)
        
        self.current_phase = 0 # current phase for exercises that use phases (if an exercise does not use phases, then this remains 0)
        self.rep_counter = 0 # this will count repetitions if reps are defined by phases. Otherwise, it is set to time elapsed for the exercise to mimick repetition counter
        self.threshold_tolerance = 0 # this is to adjust the threshold based on tolerance provided by the clinician

        #--------------------------------------------------------------------------------------------------------------------------------------------------
        # create screnr joints dictionary that will contain joint name, mediapipe landmark id, landmark coordinates and visibility that will be updated, 
        # and on_screen that will set to True for joints that should be displayed
        self.joints = {}
        
        # read screnr joint id (mapping to an API is done in the update_joints method below)
        for joint, joint_dict in self.screnr_id_dict.items():
            self.joints[joint] = {"id": joint_dict["id"], "calc": joint_dict["calc"], "coords": np.array([-999, -999]), "visibility": 0.0, "on_screen": False}


    def read_exercise_packet(self):
        ''' 
            this reads the exercise packet
        '''
    
        # read EP for the exercise
        self.exercise_packet = get_exercise_params(self.exercise_name)
        self.display_joints = self.exercise_packet["display_joints"][self.patient_facing]  # get joints to display on screen

        for joint in self.display_joints:
            self.joints[joint]["on_screen"] = True

        self.angle_info = self.exercise_packet["angles"][self.patient_facing]  # this has information on angle names and joints that form that angle
        self.rule_info = self.exercise_packet["rules"][self.patient_facing]  # this has information on rules that should be applied and the feedback that is displayed
        self.threshold_tolerance = self.exercise_packet["tolerance"][self.patient_facing]  # this is the tolerance that should be applied to the thresholds for each rule

        self.phase_info = self.exercise_packet["phases"][self.patient_facing]  # If an exercise involves phases, this has information on phase changes (e.g. squat), otherwise it is "None" (e.g. plank)
        self.feedback_probs = self.exercise_packet["feedback_probs"][self.patient_facing]  # If an exercise involves phases, this has information on phase changes (e.g. squat), otherwise it is "None" (e.g. plank)
   
        self.reset_angles_dict() # this sets up and resets rep_angles_dict


    def reset_angles_dict(self):
        ''' 
            This resets rep_angles_dict (dictionary that collects angle values in each repetition for each phase 
            Inputs: 
                - None
            
            Outputs:
                - 1
        '''
        for angle_name, angle_joints in self.angle_info.items():  # exercise angle names and the 3 joints that create that angle (read from exercise packet)
            self.rep_angles_dict[angle_name] = {}
            
            if self.phase_info=="None":  # exercise does not involve phases (e.g. plank) so each angle only involves phase 0
                if 0 not in self.rep_angles_dict[angle_name]:
                    self.rep_angles_dict[angle_name][0] = []
                    
            else:  # exercise involve phases (e.g. squats) so read phases from self.phase_info (read from exercise packet)
                for id_, phase_info in self.phase_info.items():
                    phase_num = phase_info["phase"]
                    if phase_num not in self.rep_angles_dict[angle_name]:
                        self.rep_angles_dict[angle_name][phase_num] = []
        
        return 1


    def update_joints(self, landmarks, image_size):
        ''' 
            This updates joint locations in self.joints dictionary. 
            Input Landmarks are return
            Inputs: 
                - landmarks (dict) -- landmarks read from landmark API
                - dsize (tuple) -- contains size of the frame so x,y points can be calculated
            
            Outputs:
                - 1
        '''
        xsize, ysize = image_size[0], image_size[1]
        
        if self.landmark_api == "mediapipe":
            for joint_name, joint_info in self.joints.items():
                if self.joints[joint_name]["calc"]:
                    joint1 = self.joints[joint_name]["calc"][0]
                    joint2 = self.joints[joint_name]["calc"][1]
                
                    self.joints[joint_name]["coords"] = (self.joints[joint1]["coords"]+self.joints[joint2]["coords"])/2
                    self.joints[joint_name]["visibility"] = (self.joints[joint1]["visibility"]+self.joints[joint2]["visibility"])/2
                
                else:
                    self.joints[joint_name]["coords"] = np.array([landmarks[self.joints[joint_name]["id"]].x * xsize, landmarks[self.joints[joint_name]["id"]].y * ysize])
                    self.joints[joint_name]["visibility"] = landmarks[self.joints[joint_name]["id"]].visibility

        elif landmark_api_id == "mlkit_joint":
            pass

        elif landmark_api_id == "arkit_joint":
            pass

        return 1
        

    def get_joints(self):
        return self.joints


    def calculate_angle(self, left_joint, mid_joint, right_joint, full_round=True, small_angle=True):
        '''
        INPUTS ----
        left_joint:     [x,y] points for the left joint
        mid_joint:      [x,y] points for the mid joint
        right_joint:    [x,y] points for the right joint
        full_round:     Boolean round or do not round
        small_angle:    If True, then return the min(angle, 360-angle). Otherwise max(angle, 360-angle)
        
        OUTPUT ----
        joint_angle     Angle value in degrees
        '''

        left_center_x = left_joint[0] - mid_joint[0]
        left_center_y = left_joint[1] - mid_joint[1]
        left_center_magnitude = (left_center_x**2 + left_center_y**2)**0.50
        left_center_x_normalized = left_center_x/left_center_magnitude
        left_center_y_normalized = left_center_y/left_center_magnitude
        
        right_center_x = right_joint[0] - mid_joint[0]
        right_center_y = right_joint[1] - mid_joint[1]
        right_center_magnitude = (right_center_x**2 + right_center_y**2)**0.50
        right_center_x_normalized = right_center_x/right_center_magnitude
        right_center_y_normalized = right_center_y/right_center_magnitude

        dot_product	= left_center_x_normalized * right_center_x_normalized + left_center_y_normalized * right_center_y_normalized
        joint_angle	= round(np.abs(np.arccos(dot_product))* 180 / np.pi, 1)

        if small_angle:
            joint_angle = min(joint_angle, 360 - joint_angle)
        else:
            joint_angle = max(joint_angle, 360 - joint_angle)

        if full_round:
            joint_angle = round(joint_angle,0)
            
        return joint_angle


    def get_angles(self):
        ''' 
            This calculates angles specified in EP. 
            Inputs: 
                - None -- self.angles_info is read for angle names and the 3 joints that form the angle
            
            Outputs:
                - self.joint_angles (dict) -- returns a dictionary of angles as key and angle value as values. 
        '''
            
        for angle_name, joints in self.angle_info.items():
            
            left_joint = joints["left_joint"]
            if type(left_joint) == list:
                left = np.array([self.joints[left_joint[0]]["coords"][0]*left_joint[1], 
                                 self.joints[left_joint[0]]["coords"][1]*left_joint[2]])
            else:
                left = self.joints[left_joint]["coords"]
            
            mid_joint = joints["mid_joint"]
            if type(mid_joint) == list:
                mid = np.array([self.joints[mid_joint[0]]["coords"][0]*mid_joint[1], 
                                self.joints[mid_joint[0]]["coords"][1]*mid_joint[2]])
            else:
                mid = self.joints[mid_joint]["coords"]
            
            right_joint = joints["right_joint"]
            if type(right_joint) == list:
                right = np.array([self.joints[right_joint[0]]["coords"][0]*right_joint[1], 
                                  self.joints[right_joint[0]]["coords"][1]*right_joint[2]])
            else:
                right = self.joints[right_joint]["coords"]


            full_round = False
            if joints["full_round"]=="True":
                full_round = True
            
            small_angle = False
            if joints["small_angle"]=="True":
                small_angle = True
        
            self.joint_angles[angle_name] = self.calculate_angle(left, mid, right, full_round, small_angle)


        return self.joint_angles


    def get_phase(self, angles_dict):
        # get phase of the exercise
        rep_completed = 0
        
        if self.phase_info=="None":
            self.current_phase, rep_completed = 0, 0

        else:
            for id_, phase_dict in self.phase_info.items():
                phase = phase_dict['phase']
                phase_update = phase_dict['phase_update']
                rep_complete = phase_dict['rep_complete']

                n = len(list(phase_dict['angles'].keys()))
                i = 0

                for angle_phase, angle_dict in phase_dict['angles'].items():
                    i+=1
                    #angles_dict = self.get_angles() # get joint angles for the exercise
                    current_angle_value = angles_dict[angle_phase] # angle name
                    
                    sign = angle_dict['sign']

                    if sign=='<':
                        if current_angle_value<angle_dict['value']:
                            if self.current_phase == phase and i==n:
                                self.current_phase = phase_update
                                rep_completed = rep_complete

                    elif sign=='<=':
                        if current_angle_value<=angle_dict['value']:
                            if self.current_phase == phase and i==n:
                                self.current_phase = phase_update
                                rep_completed = rep_complete

                    elif sign=='>':
                        if current_angle_value>angle_dict['value']:
                            if self.current_phase == phase and i==n:
                                self.current_phase = phase_update
                                rep_completed = rep_complete

                    elif sign=='>=':
                        if current_angle_value>=angle_dict['value']:
                            if self.current_phase == phase and i==n:
                                self.current_phase = phase_update
                                rep_completed = rep_complete

                    elif sign=='==':
                        if current_angle_value==angle_dict['value']:
                            if self.current_phase == phase and i==n:
                                self.current_phase = phase_update
                                rep_completed = rep_complete

        return (self.current_phase, rep_completed)
    

    def get_feedback(self):
        '''
        This method prints feedback for the rules that should be applied to 
        '''      
        feedback_dict = {} 
        priority_feedback = ""
        num_angles = 1

        # extract feedback rules from the exercise packet
        for rule_name, rule_info in self.rule_info.items():
            rule_priority = rule_info["priority"] # this is a priority of the rule (high priority rules get displayed first)
            
            if rule_info["phase"]=="None":
                rule_phase = 0 # if there are no phases in the exercise, assign tule phase to 0
            else:
                rule_phase = rule_info["phase"] # this is the phase in which the rule should be checked

            rule_angles_values = rule_info["angles"] # this is a dictionary where key is angle name and values are sign and angle value
            fail_message = rule_info["fail_message"] # this is the message that should be displayed if the rule fails
            pass_message = rule_info["pass_message"] # this is the message that should be displayed if the rule passes

            num_angles = len(rule_angles_values) # how many angles are involved in the rule
            num_angles_set = 0 # counter to count how many angles of "num_angles" satisfy the rule

            feedback_dict[rule_name] = {"failed_rule": False, "priority": rule_priority, "feedback": pass_message}  # setup "feedback_dict" 

            #for rule_angle, rule_sign_thresh_dict in rule_angles_values.items():
            #    feedback_dict[rule_name][rule_angle] = False

            for rule_angle, rule_sign_thresh_dict in rule_angles_values.items():
                #feedback_dict[rule_name][rule_angle] = False
                feedback_dict[rule_name][rule_angle] = -999

                min_or_max = rule_sign_thresh_dict["min_or_max"] # this will either check the min or max angle achieved in the phase
                sign = rule_sign_thresh_dict["sign"]
                threshold = rule_sign_thresh_dict["threshold"]

                angle_value_list = self.rep_angles_dict[rule_angle][rule_phase] 

                if min_or_max=="min":
                    # get min angle achieved in the phase
                    min_val = 999
                    for angle_value in angle_value_list:
                        if angle_value<min_val:
                            min_val = angle_value

                    # apply rule to check the min angle against the threshold
                    if sign=="<":
                        threshold_with_tolerance = threshold * (1-self.threshold_tolerance)
                        if min_val<threshold_with_tolerance:
                            feedback_dict[rule_name][rule_angle] = min_val
                            num_angles_set += 1
                    
                    elif sign==">":
                        threshold_with_tolerance = threshold * (1+self.threshold_tolerance)
                        if min_val>threshold_with_tolerance:
                            feedback_dict[rule_name][rule_angle] = min_val
                            num_angles_set += 1
                        
                    '''
                    # without tolerances
                    if sign=="<" and min_val<threshold:
                        #feedback_dict[rule_name][rule_angle] = True
                        feedback_dict[rule_name][rule_angle] = min_val
                        num_angles_set += 1
                    elif sign==">" and min_val>threshold:
                        #feedback_dict[rule_name][rule_angle] = True
                        feedback_dict[rule_name][rule_angle] = min_val
                        num_angles_set += 1
                    '''
                    
                elif min_or_max=="max":
                    # get max angle achieved in the phase
                    max_val = -999
                    for angle_value in angle_value_list:
                        if angle_value>max_val:
                            max_val = angle_value

                    # apply rule to check the max angle against the threshold
                    if sign=="<":
                        threshold_with_tolerance = threshold * (1-self.threshold_tolerance)
                        if max_val<threshold_with_tolerance:
                            feedback_dict[rule_name][rule_angle] = max_val
                            num_angles_set += 1
                    
                    elif sign==">":
                        threshold_with_tolerance = threshold * (1+self.threshold_tolerance)
                        if max_val>threshold_with_tolerance:
                            feedback_dict[rule_name][rule_angle] = max_val
                            num_angles_set += 1
                    
                    '''
                    if sign=="<" and max_val<threshold:
                        #feedback_dict[rule_name][rule_angle] = True
                        feedback_dict[rule_name][rule_angle] = max_val
                        num_angles_set += 1
                    elif sign==">" and max_val>threshold:
                        #feedback_dict[rule_name][rule_angle] = True
                        feedback_dict[rule_name][rule_angle] = max_val
                        num_angles_set += 1
                    '''
                
                #self.rep_angles_dict[rule_angle][rule_phase] = []
            
            # if "num_angles_set" is equal to "num_angles", it means all angles for the rule violate the rule
            if num_angles_set == num_angles:
                feedback_dict[rule_name]["feedback"] = fail_message
                feedback_dict[rule_name]["failed_rule"] = True
            
        return feedback_dict   


    def randomized_feedback(self, feedback_dict):
        ''' this returns random feedback on the rules '''
    
        random_feedback = ""  # this is the select feedback that will be returned 
        
        passed_rules_list = []  # this will collect all rules that passed
        failed_rules_list = []  # this will collect all rules that failed
        
        if feedback_dict:
            for rule_name, rule_info in feedback_dict.items():
                if rule_info["failed_rule"]==True:
                    failed_rules_list.append(rule_info["feedback"]) 
                else:
                    passed_rules_list.append(rule_info["feedback"]) 
                    
            if len(passed_rules_list)==0:
                passed_rules_list.append("")
                
            if len(failed_rules_list)==0:
                failed_rules_list.append("")
            
            
            random.shuffle(failed_rules_list)
            random.shuffle(passed_rules_list)
            
            #print(len(failed_rules_list), len(passed_rules_list))
            
            random_feedback = random.choices(population=[failed_rules_list[0], passed_rules_list[0], "keep going!", ""], 
                                             weights=[self.feedback_probs["fail_prob"], self.feedback_probs["pass_prob"], self.feedback_probs["custom_prob"], self.feedback_probs["shush_prob"]], k=1)[0]
            
        return random_feedback


    def screnr_custom_feedback(self, feedback_dict):
        ''' TODO: screnr feedback that adjusts based on several factors '''
        '''
            e.g.
            - Initially, feedback that is printed should be for the rules that are broken
            - If rules continue to breaking, then start providing positive encouraging feedback_dict
            - In the later part of the exercise, do not print anything
            - Randomize the above steps only slightly
            - Sensitivity of the printout should be controlled by the data packet.
        '''
        

    def analyze_rep(self, rep_time_elapsed):
        ''' 
            this method applies exercise rules to each repetition 
            Steps are: 
                for each repetition:
                    get angles and phase of the exercise in each frame                    
                    apply rules to angles
                    return feedback to display
        '''
        rep_packet = {} # this collects angles and feedback in each rep

        feedback = ""
        rep_complete = False
        feedback_dict = {}
        rep_angles_dict = {}
        prev_rep_count = self.rep_counter

        angles_dict = self.get_angles() # get joint angles for the exercise
        phase_num, rep_count = self.get_phase(angles_dict) # get current phase and rep count (1 if the phase changes)
        self.rep_counter += rep_count

        if self.phase_info=="None":
            self.rep_counter = rep_time_elapsed


        if self.rep_counter == prev_rep_count:
            # if the repetition is not finished then keep collecting all angles, return empty set for angles and feedback
            for angle_name, value in angles_dict.items():
                self.rep_angles_dict[angle_name][phase_num].append(value)

            rep_packet = {"angles": {}, "feedback": {}}
            return rep_complete, angles_dict, phase_num, feedback, self.rep_counter, rep_packet

        else:
            rep_angles_dict = dict(self.rep_angles_dict)
            rep_complete = True
            feedback_dict = self.get_feedback()
            feedback = self.randomized_feedback(feedback_dict) # review the feedback dictionary and return a fail/pass/shush message based on probabilities
            rep_packet = {"angles": rep_angles_dict, "feedback": feedback_dict}
            self.reset_angles_dict()
            
            print(f'Screnr>  All Feedback = {feedback_dict}')
            print(f'Screnr>  Feedback (displayed) = {feedback}')
            
            return rep_complete, angles_dict, phase_num, feedback, self.rep_counter, rep_packet


if __name__ == "__main__":

    print("screnr class")