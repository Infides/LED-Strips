#!/usr/bin/env python
# -*- coding: utf-8 -*-  

import time
import colorsys
import math
import logging as log
log.basicConfig(filename='log/LED-Strip.log',level=log.INFO,format='%(asctime)s %(message)s')

from tinkerforge.ip_connection import IPConnection
from tinkerforge.ip_connection import Error
from tinkerforge.bricklet_led_strip import LEDStrip
from tinkerforge.bricklet_multi_touch import MultiTouch
from tinkerforge.bricklet_rotary_poti import RotaryPoti

# Class for the two LED-Strips and the multi-touch bricklet with rotary poti
class led_strips:
    HOST = "localhost"
    PORT = 4223

    UID_LED_STRIP_ONE = "jGy"
    UID_LED_STRIP_TWO = "jHE"

    MODE = 0 
    MODE_HUE = 1
    MODE_SATURATION = 2
    MODE_VALUE = 3 
    MODE_VELOCITY = 4  
    MODE_COLOR_GRADIENT = 5
    MODE_COLOR_DOT = 6
    MODE_COLOR_FADING = 7   
    MODE_LEDS = 8    
    MODE_OFF = 9

    MODE_STRIPS = 0
    MODE_LEFT_STRIP = 1
    MODE_RIGHT_STRIP = 2
    MODE_BOTH_STRIPS = 3

    POSITION_HUE = 1
    POSITION_SATURATION = 1
    POSITION_VALUE = 0.3
    POSITION_VELOCITY = 1

    R = [255]*16
    G = [0]*16
    B = [0]*16
    
    MAX_LEDS = 16
    ACTIVE_LEDS = 16

    ipcon = None
    led_strip_1 = None
    led_strip_2 = None
    multi_touch = None
    rotary_poti = None

    def __init__(self):
        # Create IP Connection
        self.ipcon = IPConnection()
        while True:
            try:
                self.ipcon.connect(led_strips.HOST, led_strips.PORT)
                break
            except Error as e:
                log.error('Connection error: ' + str(e.description))
                time.sleep(1)
            except socket.error as e:
                log.error('Socket error: ' + str(e))
                time.sleep(1)

        # Register IP Connection callbacks
        self.ipcon.register_callback(IPConnection.CALLBACK_ENUMERATE, self.cb_enumerate)
        self.ipcon.register_callback(IPConnection.CALLBACK_CONNECTED, self.cb_connected)

        while True:
            try:
                self.ipcon.enumerate()
                break
            except Error as e:
                log.error('Enumerate error: ' + str(e.description))
                time.sleep(1)

    # Callback handels device connections and configures possibly lost configuration
    def cb_enumerate(self, uid, connected_uid, position, hardware_version, firmware_version, device_identifier, enumeration_type):
        if enumeration_type == IPConnection.ENUMERATION_TYPE_CONNECTED or enumeration_type == IPConnection.ENUMERATION_TYPE_AVAILABLE:
            if device_identifier == LEDStrip.DEVICE_IDENTIFIER and uid == self.UID_LED_STRIP_ONE: #LED-Strip 1
                try:
                    self.led_strip_1 = LEDStrip(uid, self.ipcon)
                    log.info('LED-Strip 1 initialized.')
                except Error as e:
                    log.error('LED-Strip 1 init failed: ' + str(e.description))
                    self.led_strip_1 = None
            elif device_identifier == LEDStrip.DEVICE_IDENTIFIER and uid == self.UID_LED_STRIP_TWO: #LED-Strip 2
                try:
                    self.led_strip_2 = LEDStrip(uid, self.ipcon)
                    log.info('LED-Strip 2 initialized.')
                except Error as e:
                    log.error('LED-Strip 2 init failed: ' + str(e.description))
                    self.led_strip_2 = None
            elif device_identifier == MultiTouch.DEVICE_IDENTIFIER: # MulitTouch for changing colors etc.
                try:
                    self.multi_touch = MultiTouch(uid, self.ipcon)
                    self.multi_touch.register_callback(self.multi_touch.CALLBACK_TOUCH_STATE, self.cb_buttons)
                    self.multi_touch.set_electrode_config(0x0FFF)
                    self.multi_touch.recalibrate()
                    log.info('Set proximity off.')
                    log.info('Multi-Touch initialized.')
                except Error as e:
                    log.error('Multi-Touch init failed: ' + str(e.description))
                    self.multi_touch = None
            elif device_identifier == RotaryPoti.DEVICE_IDENTIFIER: # Rotary Poti for picking a color or changing the saturation
                try:
                    self.rotary_poti = RotaryPoti(uid, self.ipcon)
                    self.rotary_poti.register_callback(self.rotary_poti.CALLBACK_POSITION, self.cb_position)
                    self.rotary_poti.set_position_callback_period(50)
                    log.info('Rotary Poti initialized.')
                except Error as e:
                    log.error('Rotary Poti init failed: ' + str(e.description))
                    self.rotary_poti = None

    # Callback handels reconnection of IP Connection
    def cb_connected(self, connected_reason):
        if connected_reason == IPConnection.CONNECT_REASON_AUTO_RECONNECT:
            log.info('Auto reconnect.')
            while True:
                try:
                    self.ipcon.enumerate()
                    break
                except Error as e:
                    log.error('Enumerate error:' + str(e.description))
                    time.sleep(1)

    # Check which mode is set: the left LED strip, the right LED strip or both LED strips
    def set_mode(self, mode, i, leds, r, b, g):
        if self.MODE_STRIPS == self.MODE_BOTH_STRIPS:
            self.led_strip_1.set_rgb_values(i, leds, r, b, g)
            self.led_strip_2.set_rgb_values(i, leds, r, b, g)
        elif self.MODE_STRIPS == self.MODE_LEFT_STRIP:
            self.led_strip_1.set_rgb_values(i, leds, r, b, g)
        elif self.MODE_STRIPS == self.MODE_RIGHT_STRIP:
            self.led_strip_2.set_rgb_values(i, leds, r, b, g)
    
    # Turn off the LED strips depending on the given mode
    def leds_off(self):
        r = [0]*self.MAX_LEDS
        g = [0]*self.MAX_LEDS
        b = [0]*self.MAX_LEDS
        self.set_mode(self.MODE_STRIPS, 0, self.MAX_LEDS, r, b, g)

    # Some simple color functions to turn the strips to red, green or blue
    def led_strips_red(self):
        r = [255]*self.MAX_LEDS
        g = [0]*self.MAX_LEDS
        b = [0]*self.MAX_LEDS
        self.set_mode(self.MODE_STRIPS, 0, self.MAX_LEDS, r, b, g)

    def led_strips_green(self):
        r = [0]*self.MAX_LEDS
        g = [255]*self.MAX_LEDS
        b = [0]*self.MAX_LEDS
        self.set_mode(self.MODE_STRIPS, 0, self.MAX_LEDS, r, b, g)

    def led_strips_blue(self):
        r = [0]*self.MAX_LEDS
        g = [0]*self.MAX_LEDS
        b = [255]*self.MAX_LEDS
        self.set_mode(self.MODE_STRIPS, 0, self.MAX_LEDS, r, b, g)

    # Match the hue (color) to the position by the rotary poti.
    def set_hue(self, position):
        # The position returned by the rotary poti (o to +300) must be mapped to 0°-360° in the HSV colorspace
        hue = ((position / 360) * 432)
        # Convert the HSV color (hue,saturation,value) to the RGB color
        # The function expects hue to be in the range 0-1 not 0-360
        r, g, b = colorsys.hsv_to_rgb(hue/360, self.POSITION_SATURATION, self.POSITION_VALUE)
        print('Hue: {0:.1f}'.format(hue),'Saturation: {0:.2f}'.format(self.POSITION_SATURATION),'Value: {0:.2f}'.format(self.POSITION_VALUE))
        # Build the LED strip
        self.build_led_strip(r, g, b) 
        # Save the value in the variable
        self.POSITION_HUE = hue/360

    # Match the saturation to the position by the rotary poti.
    def set_saturation(self, position):
        # The position returned by the rotary poti must be mapped to 0-1 in the HSV colorspace
        saturation = (position / 300)
        # Convert the HSV color (hue,saturation,value) to the RGB color
        r, g, b = colorsys.hsv_to_rgb(self.POSITION_HUE, saturation, self.POSITION_VALUE) 
        print('Hue: {0:.1f}'.format(self.POSITION_HUE*360),'Saturation: {0:.2f}'.format(saturation),'Value: {0:.2f}'.format(self.POSITION_VALUE))
        # Build the LED strip
        self.build_led_strip(r, g, b)
        # Save the value in the variable
        self.POSITION_SATURATION = saturation
    
    # Match the value to the position by the rotary poti.
    def set_value(self, position):
        # The position returned by the rotary poti must be mapped to 0-1 in the HSV colorspace
        value = (position / 300)
        # Convert the HSV color (hue,saturation,value) to the RGB color
        r, g, b = colorsys.hsv_to_rgb(self.POSITION_HUE, self.POSITION_SATURATION, value)
        print('Hue: {0:.1f}'.format(self.POSITION_HUE*360),'Saturation: {0:.2f}'.format(self.POSITION_SATURATION),'Value: {0:.2f}'.format(value))
        # Build the LED strip
        self.build_led_strip(r, g, b)
        # Save the value in the variable
        self.POSITION_VALUE = value

    # The veolcity for some functions can be adjusted by the rotary poti.
    def set_velocity(self, position):
        velocity = (position / 3)
        print('Velocity: {0:0.1f}'.format(velocity))
        # Save the velocity in the variable
        self.POSITION_VELOCITY = velocity

    # Function to generate a rainbow gradient. Can be adjusted by the velocity.
    def set_color_gradient(self, position):
        # Always use all LEDs for the gradient
        active_leds = self.MAX_LEDS

        # Match the velocity of the gradient by the position of the rotary poti
        gradient_velocity = (position / 3)
        #gradient_velocity = self.POSITION_VELOCITY
        print('Gradient velocity: {0:0.1f}'.format(gradient_velocity))

        """
        red_array = []
        green_array = []
        blue_array = []

        range_leds = list(range(active_leds))
        print('Range LEDs: ' + str(range_leds))

        range_leds = list(range_leds[int(gradient_velocity) % 16:]) + list(range_leds[:int(gradient_velocity) % 16])
        print('Range LEDs: ' + str(range_leds))

        # Start from the other side of the strip
        range_leds = list(reversed(range_leds))
        print('Reversed LEDs: ' + str(range_leds))

        # Generating the color gradient
        for i in range_leds:
            r, g, b = colorsys.hsv_to_rgb(1.*i/active_leds, self.POSITION_SATURATION, self.POSITION_VALUE)
            red_array.append(int(r*255))
            green_array.append(int(g*255))
            blue_array.append(int(b*255))
 
        print('R: ' + str(red_array) + '\n','G: ' + str(green_array) + '\n','B: ' + str(blue_array) + '\n')
        
        # Get the gradient to the strips
        self.set_mode(self.MODE, 0, self.MAX_LEDS, red_array, blue_array, green_array)
        """

        range_leds = list(range(active_leds))
        #print('Range LEDs: ' + str(range_leds))
 
        red_array = []
        green_array = []
        blue_array = []
       
        loop_counter = 0

        for i in range_leds:
            r, g, b = colorsys.hsv_to_rgb(1.*i/active_leds, self.POSITION_SATURATION, self.POSITION_VALUE)
            red_array.append(int(r*255))
            green_array.append(int(g*255))
            blue_array.append(int(b*255))

        for j in range(16):
            print("Loop counter: " + str(loop_counter))

            first_red = red_array.pop(0)
            red_array.append(first_red)
            first_green = green_array.pop(0)
            green_array.append(first_green)
            first_blue = blue_array.pop(0)
            blue_array.append(first_blue)

            print('R: ' + str(red_array) + '\n','G: ' + str(green_array) + '\n','B: ' + str(blue_array) + '\n')
            
            self.set_mode(self.MODE, 0, self.MAX_LEDS, red_array, blue_array, green_array)

            loop_counter = loop_counter + 1
            
            time.sleep(0.075)

        if position == 300:
            print("Gradient end!")

        """
        #if position < 300:
        for k in range(16):
            red_array = []
            green_array = []
            blue_array = []
            
            #range_leds = list(range_leds[int(gradient_velocity) % 16:]) + list(range_leds[:int(gradient_velocity) % 16])
            print("k: " + str(k))
            #range_leds = list(range_leds[k % 16:]) + list(range_leds[:k % 16])
            range_leds = list(range_leds[k:]) + list(range_leds[:k])
            print('Range LEDs: ' + str(range_leds))

            for i in range_leds:
                r, g, b = colorsys.hsv_to_rgb(1.*i/active_leds, self.POSITION_SATURATION, self.POSITION_VALUE)
                red_array.append(int(r*255))
                green_array.append(int(g*255))
                blue_array.append(int(b*255))

            print('R: ' + str(red_array) + '\n','G: ' + str(green_array) + '\n','B: ' + str(blue_array) + '\n')
            
            # Get the gradient to the strips
            self.set_mode(self.MODE, 0, self.MAX_LEDS, red_array, blue_array, green_array)

            time.sleep(0.075)
        """

    # Only one LED is active and moves from one end to the other end of the strip.
    # The speed can be adjusted by the velocity function.
    def set_color_dot(self, position):
        # Build the initial array
        r = self.R[0]
        g = self.G[0]
        b = self.B[0]
        r = [r]
        g = [g]
        b = [b]
        r.extend([0]*15)
        g.extend([0]*15)
        b.extend([0]*15)
        #print('R: ' + str(r) + '\n','G: ' + str(g) + '\n','B: ' + str(b) + '\n')
        # Now get the dot moving
        i = 0
        while i < 15:
            dot_r = r[i]
            dot_g = g[i]
            dot_b = b[i]
            r[i] = 0
            g[i] = 0
            b[i] = 0
            r[i+1] = dot_r
            g[i+1] = dot_g
            b[i+1] = dot_b
            print('R: ' + str(r) + '\n','G: ' + str(g) + '\n','B: ' + str(b) + '\n')
            i = i + 1
            self.set_mode(self.MODE, 0, self.MAX_LEDS, r, b, g)
            time.sleep(0.1)
        while i > 0:
            dot_r = r[i]
            dot_g = g[i]
            dot_b = b[i]
            r[i] = 0
            g[i] = 0
            b[i] = 0
            r[i-1] = dot_r
            g[i-1] = dot_g
            b[i-1] = dot_b
            print('R: ' + str(r) + '\n','G: ' + str(g) + '\n','B: ' + str(b) + '\n')
            i = i - 1
            self.set_mode(self.MODE, 0, self.MAX_LEDS, r, b, g)
            time.sleep(0.1)
 
    # The LEDs are fading from 0.1 to 1.0 in the value space. The fading can be adjusted by the velocity.
    def set_color_fading(self, position):
        loop_counter = 0
        if position < 300:
            #while loop_counter < 5:
            print("Position: " + str(position))
            print("Loop counter: " + str(loop_counter))
            for value in range(1, 21):
                value = value / 20
                print("Value: " + str(value))
                r, g, b = colorsys.hsv_to_rgb(self.POSITION_HUE, self.POSITION_SATURATION, value)
                self.build_led_strip(r, g, b)
                time.sleep(0.075)
            for value in reversed(range(1, 21)):
                value = value / 20
                print("Value: " + str(value))
                r, g, b = colorsys.hsv_to_rgb(self.POSITION_HUE, self.POSITION_SATURATION, value)
                self.build_led_strip(r, g, b)
                time.sleep(0.075)
                loop_counter = loop_counter + 1
        elif position >= 300:
            print("Position: " + str(position))

    # Extend the LEDs from 1 LED to 16 LEDs per strip. Like the fading, but here the LEDs can be adjusted by the velocity.
    def set_leds(self, position):
        # The rotary poti can set the number of LEDs which should be used
        active_leds = (position / 300) * self.MAX_LEDS
        active_leds = int(math.ceil(active_leds))
        print('Active LEDs: ' + str(active_leds))
        
        # Get the color values from the variables
        r = self.R[0]
        g = self.G[0]
        b = self.B[0]
        #print('R: ' + str(r) + '\n','G: ' + str(g) + '\n','B: ' + str(b) + '\n')
        
        # Now build the list with the active leds
        r = [r]*active_leds
        g = [g]*active_leds
        b = [b]*active_leds
        #print('R: ' + str(r) + '\n','G: ' + str(g) + '\n','B: ' + str(b) + '\n')

        # Now add the remaining dark leds to the list
        dark_leds = 16 - active_leds
        print('Dark LEDs: ' + str(dark_leds))
        r.extend([0]*dark_leds)
        g.extend([0]*dark_leds)
        b.extend([0]*dark_leds)          
        print('R: ' + str(r) + '\n','G: ' + str(g) + '\n','B: ' + str(b) + '\n')
        
        # Now get it to the strips
        self.set_mode(self.MODE, 0, self.MAX_LEDS, r, b, g)           
        # Save the value in the variable
        self.ACTIVE_LEDS = active_leds

    # Helper function to generate the output for the LED strips
    def build_led_strip(self, r, g, b):
        r = int(r*255)
        g = int(g*255)
        b = int(b*255)
        #print('R: ' + str(r),'G: ' + str(g),'B: ' + str(b))
        # Get the actual number of LEDs which should be used
        active_leds = self.ACTIVE_LEDS
        r = [r]*active_leds
        g = [g]*active_leds
        b = [b]*active_leds
        # Now add the remaining dark leds to the list
        dark_leds = 16 - active_leds
        r.extend([0]*dark_leds)
        g.extend([0]*dark_leds)
        b.extend([0]*dark_leds)
        #print('R: ' + str(r) + '\n','G: ' + str(g) + '\n','B: ' + str(b) + '\n')
        # Now get it to the strips
        self.set_mode(self.MODE, 0, self.MAX_LEDS, r, b, g)
        # Save the values in the variables
        self.R = r
        self.G = g
        self.B = b

    # Callback function for position callback (parameter has range -150 to 150)
    def cb_position(self, position):
        # Print the position for debuging
        #print('Position: ' + str(position))
        # Always add +150 to the position value so that it will start on the left by 0 and to the right it will end by 300
        position = position + 150
        # Select in which MODE it is called
        if self.MODE == self.MODE_HUE:
            self.set_hue(position)
        elif self.MODE == self.MODE_SATURATION:
            self.set_saturation(position)
        elif self.MODE == self.MODE_VALUE:
            self.set_value(position)
        elif self.MODE == self.MODE_VELOCITY:
            self.set_velocity(position)
        elif self.MODE == self.MODE_COLOR_GRADIENT:
            self.set_color_gradient(position)
        elif self.MODE == self.MODE_COLOR_DOT:
            self.set_color_dot(position)
        elif self.MODE == self.MODE_COLOR_FADING:
            self.set_color_fading(position)
        elif self.MODE == self.MODE_LEDS:
            self.set_leds(position)

    # Callback function for button callback
    def cb_buttons(self, button_state):
        for i in range(12):
            if button_state & (1 << i):
                if i == 0:
                    self.MODE_STRIPS = self.MODE_LEFT_STRIP
                elif i == 1:
                    self.MODE = self.MODE_HUE
                elif i == 2:
                    self.MODE = self.MODE_COLOR_GRADIENT
                elif i == 3:
                    self.MODE_STRIPS = self.MODE_BOTH_STRIPS
                elif i == 4:
                    self.MODE = self.MODE_SATURATION
                elif i == 5:
                    self.MODE = self.MODE_COLOR_DOT
                elif i == 6:
                    self.MODE_STRIPS = self.MODE_RIGHT_STRIP
                elif i == 7:
                    self.MODE = self.MODE_VALUE
                elif i == 8:
                    self.MODE = self.MODE_COLOR_FADING
                elif i == 9:
                    self.MODE = self.MODE_OFF
                elif i == 10:
                    self.MODE = self.MODE_VELOCITY
                elif i == 11:
                    self.MODE = self.MODE_LEDS

# Main function
if __name__ == "__main__":
    log.info('LED-Strips: Start')

    # Start the class
    ledstrips = led_strips()

    # Wait a little bit, so everything can be initialized
    time.sleep(0.5)

    # Make a nice initial setup
    if ledstrips.ipcon != None:
        ledstrips.MODE_STRIPS = led_strips.MODE_BOTH_STRIPS
        ledstrips.set_color_dot(100)
        ledstrips.set_color_dot(100)
        ledstrips.set_color_fading(100)
        ledstrips.set_color_fading(100)
        ledstrips.leds_off()

    input('Press enter to exit.\n')

    # Clean shutdown
    if ledstrips.ipcon != None:
        ledstrips.MODE_STRIPS = led_strips.MODE_BOTH_STRIPS
        ledstrips.leds_off()
        ledstrips.ipcon.disconnect()

    log.info('LED-Strips: End')
