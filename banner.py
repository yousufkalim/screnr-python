# -*- coding: utf-8 -*-
"""
Created on Oct 12 20:35:01 2021

@author: Ahmad
"""

import mediapipe as mp
import cv2
import numpy as np
import time


# this class displays banners on the video
class banner:

    def __init__(self, image, text):
        # this assigns image or video input
        self.image = image

        # this assigns text to be displayed
        self.text_is_dict = False
        self.text = text
        
        if type(self.text)==dict:
            self.text_is_dict = True
        
    def on_screen(self, banner_pos_start, banner_pos_end, text_pos, font_face, scale = 0.8, text_height=0, transparency=1, banner_color = (60, 62, 66), text_color = (255, 255, 255)):
        # put banner and text on screen
        
        # rectangle 
        #   start(x, y)-------------
        #        |                  |
        #        |                  |
        #        |                  |
        #        -----------end(x, y)
        
        # if transparency is specified, banner is transparent by transparency factor
        if transparency>0:
            overlay = self.image.copy()
            cv2.rectangle(self.image, banner_pos_start, banner_pos_end, banner_color, cv2.FILLED)
            alpha = 1-transparency  # Transparency factor.
            self.image = cv2.addWeighted(overlay, alpha, self.image, transparency, 0)
            
        else:
            cv2.rectangle(self.image, banner_pos_start, banner_pos_end, banner_color, cv2.FILLED)

        # if text is a dictionary containing stats in key,value pairs, then populate on vertical bar
        if self.text_is_dict:
            stat_text_pos_y = text_pos[1]
            for stat, value in self.text.items():
                if stat=="" and value=="":
                    stat_text = "  "
                else:
                    stat_text = stat + ': ' + str(value)
                cv2.putText(self.image, stat_text, text_pos, font_face, scale, text_color, 1, cv2.LINE_AA)
                stat_text_pos_y += text_height
                text_pos = (text_pos[0], stat_text_pos_y)
                
        else:
            cv2.putText(self.image, self.text, text_pos, font_face, scale, text_color, 1, cv2.LINE_AA)
            
        return self.image

def mp_video_stat_banner(image, exercise_name, feedback, stats_dict, feedback_color):
    padding = 20
    scale = 0.8
    margin = 2
    color = (255, 255, 255)
    thickness = cv2.FILLED

    image_height = int(image.shape[0])
    image_width = int(image.shape[1])

    # design idea:
    # - (1) top bar to display exercise name
    # - (2) side bar to display exercise stats
    # - (3) bottom bar to display feedback
        
    # rectangle 
    #   start(x, y)-------------
    #        |                  |
    #        |                  |
    #        |                  |
    #        -----------end(x, y)


    # (1) exercise name
    # ----------------
    font_face = cv2.FONT_HERSHEY_SIMPLEX
    text_size = cv2.getTextSize(exercise_name, font_face, scale, thickness)
    
    # banner    
    banner_start_x = padding
    banner_start_y = padding
    banner_pos_start = (banner_start_x, banner_start_y)

    banner_end_x = image_width - padding
    banner_end_y = text_size[0][1] + 60
    banner_pos_end = (banner_end_x, banner_end_y)
    
    # text
    text_pos_x = int((banner_start_x+banner_end_x)/2) - int(text_size[0][0]/2)
    text_pos_y = banner_start_y + text_size[0][1] + padding
    text_pos = (text_pos_x, text_pos_y)
    
    top_bar = banner(image, exercise_name)
    image = top_bar.on_screen(banner_pos_start, banner_pos_end, text_pos, font_face, 0.8, 0, 1.0)


    # (2) feedback
    # ----------------
    font_face = cv2.FONT_HERSHEY_SIMPLEX
    text_size = cv2.getTextSize(feedback, font_face, scale, thickness)
    
    # banner
    banner_start_x = padding
    banner_start_y = image_height - padding - text_size[0][1] - 2*padding
    banner_pos_start = (banner_start_x, banner_start_y)

    banner_end_x = image_width - padding
    banner_end_y = image_height - padding
    banner_pos_end = (banner_end_x, banner_end_y)
    
    # text
    text_pos_x = int((banner_start_x+banner_end_x)/2) - int(text_size[0][0]/2)
    text_pos_y = banner_start_y + text_size[0][1] + padding
    text_pos = (text_pos_x, text_pos_y)


    feedback_bar = banner(image, feedback)
    image = feedback_bar.on_screen(banner_pos_start, banner_pos_end, text_pos, font_face, 0.8, 0, 0.80, feedback_color)


    # (3) stats
    # ----------------
    font_face = cv2.FONT_HERSHEY_SIMPLEX
    text_size = cv2.getTextSize(exercise_name, font_face, scale, thickness)
    text_height = text_size[0][1] + padding
    
    # banner
    banner_start_x = image_width - 15*padding
    banner_start_y = text_size[0][1] + 4*padding
    banner_pos_start = (banner_start_x, banner_start_y)

    banner_end_x = image_width - padding
    banner_end_y = image_height - padding - text_size[0][1] - padding - 2*padding
    banner_pos_end = (banner_end_x, banner_end_y)
    
    # text
    text_pos_x = banner_start_x + int(padding/2)
    text_pos_y = banner_start_y + 2*padding
    text_pos = (text_pos_x, text_pos_y)
        
    stats_bar = banner(image, stats_dict)
    image = stats_bar.on_screen(banner_pos_start, banner_pos_end, text_pos, font_face, 0.50, text_height, 0.80)

    return image