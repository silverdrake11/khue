import time
import threading

import pygame.midi

from qhue import Bridge


NANOKONTROL_ID = 3
BRIDGE_IP = '192.168.1.80'
USERNAME = 'nanokontrol'
KONTROL_MAX_VALUE = 127
BRI_MAX_VALUE = 254


buttons = {
    58: 'track_left',
    59: 'track_right',
    46: 'cycle',
    60: 'marker_set',
    61: 'marker_left',
    62: 'marker_right',
    43: 'rwd',
    44: 'fwd',
    42: 'stop',
    41: 'play',
    45: 'record',
    32: 's_0',
    33: 's_1',
    34: 's_2',
    35: 's_3',
    36: 's_4',
    37: 's_5',
    38: 's_6',
    39: 's_7',
    48: 'm_0',
    49: 'm_1',
    50: 'm_2',
    51: 'm_3',
    52: 'm_4',
    53: 'm_5',
    54: 'm_6',
    55: 'm_7',
    64: 'r_0',
    65: 'r_1',
    66: 'r_2',
    67: 'r_3',
    68: 'r_4',
    69: 'r_5',
    70: 'r_6',
    71: 'r_7'
}
knobs = [16, 17, 18, 19, 20, 21, 22, 23]
sliders = [0, 1, 2, 3, 4, 5, 6, 7]


class Bulb:
  
  
  def __init__(self, api_obj):
    self.api = api_obj
    state = self.api()['state']
    
    self.on = state['on']
    self.brightness = state['bri']
    self.ct = state['ct']
    self.hue = state['hue']
    self.saturation = state['sat']
    
    
  def update2(self, hue, saturation):
    
    if hue == self.hue and saturation == self.saturation:
      return
    
    to_update = dict()
    
    if self.on != True:
      to_update['on'] = True
        
    if hue != self.hue:
      to_update['hue'] = hue
      print('Updating hue from {} to {}'.format(self.hue, hue))
      
    if saturation != self.saturation:
      to_update['sat'] = saturation
      print('Updating saturation from {} to {}'.format(self.saturation, saturation))
  
    to_update['transitiontime'] = 0
      
    self.api.state(**to_update)
    self.hue = hue
    self.saturation = saturation
    self.on = True
    
    
  def toggle(self):
    if self.on:
      self.on = False 
      self.api.state(on=False, transitiontime=0)       
    else:
      self.on = True
      self.api.state(on=True, bri=self.brightness, transitiontime=0)
    
    
  def decrease_brightness(self):
    current_brightness = self.brightness
    new_brightness = current_brightness - 25
    
    if new_brightness < 0:
      new_brightness = 0
      
    if current_brightness != new_brightness:
      
      to_update = dict()
      
      if self.on != True:
        to_update['on'] = True
        
      to_update['transitiontime'] = 1
      to_update['bri'] = new_brightness
      
      self.api.state(**to_update)
      self.brightness = new_brightness
      self.on = True
      print('decrease brighness from {} to {}'.format(current_brightness, new_brightness))
      
    if current_brightness == new_brightness == 0:
      if self.on == True:
        self.api.state(on=False, transitiontime=1)
        self.on = False
  
  
  def increase_brightness(self):
    current_brightness = self.brightness
    new_brightness = current_brightness + 25
    if new_brightness > 255:
      new_brightness = 255
    if current_brightness != new_brightness:
      
      to_update = dict()
      
      if self.on != True:
        to_update['on'] = True
        new_brightness = 0
        
      to_update['transitiontime'] = 1
      to_update['bri'] = new_brightness
      
      self.api.state(**to_update)
      self.brightness = new_brightness
      self.on = True
      print('increased brighness from {} to {}'.format(current_brightness, new_brightness))
    

def kontrol_to_bri(kontrol_value):
  return int(kontrol_value/float(KONTROL_MAX_VALUE) * float(BRI_MAX_VALUE))
def kontrol_to_ct(kontrol_value):
  return int(500.0 - ((kontrol_value/float(KONTROL_MAX_VALUE)) * 347.0))
def kontrol_to_hue(kontrol_value):
  return int(kontrol_value/float(KONTROL_MAX_VALUE) * 65535.0)
def kontrol_to_sat(kontrol_value):
  return int(kontrol_value/float(KONTROL_MAX_VALUE) * 254.0)


def twistedKnob(idx, value):
  if idx < 7:
    global BRIGHTNESS
    global HUE
    BRIGHTNESS[idx+1] = kontrol_to_bri(value)
    HUE[idx+1] = kontrol_to_hue(value)
    

def slidSlider(idx, value):
  if idx < 7:
    global CT
    global SATURATION
    CT[idx+1] = kontrol_to_ct(value)
    SATURATION[idx+1] = kontrol_to_sat(value)
    
  
def brightnessPress(button_name, light_num):
  global PRESSED
  PRESSED[light_num] = True
  start_time = time.clock()
  while PRESSED[light_num]:
    if (time.clock() - start_time) > 0.3: # seconds
      print('{} -> {}'.format(button_name, light_num, PRESSED[light_num]))
      time.sleep(0.15) # seconds
      if button_name == 's':
        BULB_TABLE[light_num].increase_brightness()
      else:
        BULB_TABLE[light_num].decrease_brightness()


def brightnessRelease(light_num):
  global PRESSED
  PRESSED[light_num] = False
  print('{} -> {}'.format(light_num, PRESSED[light_num]))
  

def buttonDown(button):
  
  #DEBUG there is a better way to do this...
  if not '_' in button:
    return
  
  button_name, light_num = button.split('_')
  light_num = int(light_num) + 1
  
  if light_num > 7:
    return
  
  if button_name == 's':
    BULB_TABLE[light_num].increase_brightness()
    t = threading.Thread(target=brightnessPress, args=(button_name, light_num))
    t.start()
  elif button_name == 'r':
    BULB_TABLE[light_num].decrease_brightness()
    t = threading.Thread(target=brightnessPress, args=(button_name, light_num))
    t.start()
  elif button_name == 'm':
    t = threading.Thread(target=BULB_TABLE[light_num].toggle)
    t.start()
  else:
    pass
  print ("Pushed button {}".format(button))


def buttonUp(button):
  
  #DEBUG there is a better way to do this...
  if not '_' in button:
    return
  
  button_name, light_num = button.split('_')
  light_num = int(light_num) + 1
  
  if light_num > 7:
    return
  
  if button_name == 's' or button_name == 'r':
    t = threading.Thread(target=brightnessRelease, args=(light_num,))
    t.start()
  elif button_name == 'm':
    t = threading.Thread(target=BULB_TABLE[light_num].toggle)
    t.start()
  else:
    pass
  print("Released button {}".format(button))
  
  
def midiCallback(message):
  control = message[0][0][1]
  value = message[0][0][2]
  if control in buttons:
    name = buttons[control]
    if (value == 127):
      return buttonDown(name)
    else:
      return buttonUp(name)
  else:
    try:
      idx = knobs.index(control)
      return twistedKnob(idx, value)
    except ValueError:
      pass
    try:
      idx = sliders.index(control)
      return slidSlider(idx, value)
    except ValueError:
      pass
    print("Control: {}, Value: {}".format(control, value))


def update_light2():
  threading.Timer(0.1, update_light2).start()
  for bulb_idx in range(1,8):
    time.sleep(0.018)
    BULB_TABLE[bulb_idx].update2(HUE[bulb_idx], SATURATION[bulb_idx])


# Declare globals
BRIGHTNESS = dict()
CT = dict()
HUE = dict()
SATURATION = dict()
PRESSED = dict()

hue = Bridge(BRIDGE_IP, USERNAME)

# Initialize globals
BULB_TABLE = dict()
for bulb_idx in range(1,8):
  bulb_obj = Bulb(hue.lights[bulb_idx])
  BULB_TABLE[bulb_idx] = bulb_obj
  BRIGHTNESS[bulb_idx] = bulb_obj.brightness
  CT[bulb_idx] = bulb_obj.ct
  HUE[bulb_idx] = bulb_obj.hue
  SATURATION[bulb_idx] = bulb_obj.saturation

pygame.midi.init()

num_of_devices = pygame.midi.get_count()
for device_id in range(0, num_of_devices):
  device_info = pygame.midi.get_device_info(device_id)
  print(device_info)

nanok = pygame.midi.Input(NANOKONTROL_ID)

# Launch knob / slider update thread
update_light2()

while True:
  if nanok.poll():
    message = nanok.read(1)
    midiCallback(message)
    
