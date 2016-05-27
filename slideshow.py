#!/usr/bin/python

import pygame
from pygame.locals import *
import os
from time import sleep
import RPi.GPIO as GPIO
import json
import urllib
import random, string
import atexit
import time
import subprocess

#Setup the GPIOs as outputs - only 4 and 17 are available
GPIO.setmode(GPIO.BCM)
GPIO.setup(4, GPIO.OUT)
GPIO.setup(17, GPIO.OUT)

#Colours
WHITE = (255,255,255)

os.putenv('SDL_FBDEV', '/dev/fb1')

pygame.init()
pygame.mouse.set_visible(False)
screen_res_x = pygame.display.Info().current_w
screen_res_y = pygame.display.Info().current_h
screen = pygame.display.set_mode((screen_res_x, screen_res_y))
screen.fill((0,0,0))
pygame.display.update()
clock = pygame.time.Clock() # create a clock object for timing
#font_big = pygame.font.Font(None, 50)

def cleanup():
    GPIO.cleanup()

def resize_image(image, max_width, max_height):
    image_width = image.get_width()
    image_height = image.get_height()
    new_width = image_width
    new_height = image_height
    if (image_height > image_width): 
        if (image_height > max_height):
            ratio = float(max_height) / image_height
            new_height = max_height
            new_width = int(round(image_width * ratio))
        if (new_width > max_width):
            ratio = float(max_width) / image_width
            new_width = max_width
            new_height = int(round(image_height * ratio))
    elif (image_width > max_width):
        ratio = float(max_width) / image_width
        new_width = max_width
        new_height = int(round(image_height * ratio))
        if (new_height > max_height):
            ratio = float(max_heigh) / image_height
            new_height = max_height
            new_width = int(round(image_width * ratio))
    if (new_height != image_height or new_width != image_width):
        print("Resizing to "+str(new_width)+" x "+str(new_height))
        image = pygame.transform.scale(image, (new_width, new_height))
    return image

def fade_transition(target_surface, screen):
    source_surface = pygame.display.get_surface().copy()
    target_surface = pygame.Surface((screen_res_x, screen_res_y))
    target_surface.fill(background_colour)
    target_surface.blit(slide_image, ((0.5 * screen_res_x) - (0.5 * image_width), (0.5 * screen_res_y) - (0.5 * image_height)))
    target_screen_alpha = 0
    source_screen_alpha = 255
    while target_screen_alpha < 255:
        target_screen_alpha = target_screen_alpha + 5
        source_screen_alpha = source_screen_alpha - 5
        source_surface.set_alpha(source_screen_alpha)
        target_surface.set_alpha(target_screen_alpha)
        screen.blit(source_surface, (0, 0)) 
        screen.blit(target_surface, (0, 0)) 
        pygame.time.delay(10)
        pygame.display.flip() 
    screen.blit(target_surface, (0, 0))
    pygame.display.flip() 

atexit.register(cleanup)

with open('slideshow.json') as slideshow_file:
    slideshow_data = json.load(slideshow_file)

FNULL = open(os.devnull, 'w')
repeats = 0
if (int(slideshow_data['repeat']) > 0): 
    repeats = int(slideshow_data['repeat'])
repeate_number = 0
repeate = True
while repeate:
    for slide in slideshow_data['slides']:
        temp_file = "/tmp/" + ''.join(random.choice(string.lowercase) for i in range(10))
        while ( os.path.isfile(temp_file) ): 
            # We don't want to just assume that the temp file does not exist
            temp_file = "/tmp/" + ''.join(random.choice(string.lowercase) for i in range(10))
        # Using wget to retrieve images. The urllib had issues with Zabbix logins. 
        subprocess.check_call("wget --output-document="+temp_file+" '"+slide['url']+"'", shell=True, stdout=FNULL, stderr=subprocess.STDOUT)
        print("Downloaded "+slide['url']+" to "+temp_file)
        slide_image = pygame.image.load(temp_file).convert()
        os.remove(temp_file)
        slide_image = resize_image(slide_image, screen_res_x, screen_res_y)
        image_width = slide_image.get_width()
        image_height = slide_image.get_height()
        background_red, backgound_green, background_blue = (slide['background_colour'].split(','))
        background_colour = (int(background_red), int(backgound_green), int(background_blue))
        surface = pygame.Surface((screen_res_x, screen_res_y))
        surface.fill(background_colour)
        surface.blit(slide_image, ((0.5 * screen_res_x) - (0.5 * image_width), (0.5 * screen_res_y) - (0.5 * image_height)))
        if (slide['transition'] == 'fade'):
            fade_transition(surface, screen)
            screen.blit(surface, (0, 0)) 
            pygame.display.flip() 
            time.sleep(int(slide['delay']))
    repeate_number = repeate_number + 1
    if (repeate_number >= repeats and repeats != 0):
        repeate = False
    
