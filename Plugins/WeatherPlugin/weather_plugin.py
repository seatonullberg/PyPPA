import requests
from bs4 import BeautifulSoup
import json
from Speaker import vocalize
from private_config import DARK_SKY_KEY, GEONAMES_USERNAME
from Plugins.base_plugin import BasePlugin


# TODO: Could use a total overhaul
# number pronunciation, information relevance, speed
class PyPPA_WeatherPlugin(BasePlugin):

    def __init__(self, command):
        self.COMMAND_HOOK_DICT = {'check_weather': ['check the weather',
                                                    'what is the weather',
                                                    "what's the weather",
                                                    'check weather']}
        self.MODIFIERS = {'check_weather': {'in': ['in', 'on']}}
        self.weather_dict = {}
        self.isBlocking = True
        super().__init__(command=command,
                         command_hook_dict=self.COMMAND_HOOK_DICT,
                         modifiers=self.MODIFIERS)

    def function_handler(self, args=None):
        if self.command_dict['modifier'] == 'in':
            # fetch foreign weather
            self.get_foreign_weather()
            self.vocalize__weather()
            return
        else:
            # otherwise fetch local weather
            self.get_local_weather()
            self.vocalize__weather()
            return

    def get_local_weather(self):
        '''
        :return: Dark Sky API forecast call
         --must be parsed for the specific information ie. ['currently']
        '''
        r = requests.get(r'https://geoiptool.com/')
        readable = r.text
        soup = BeautifulSoup(readable, 'html.parser')
        items_list = []
        for items in soup.find_all('div', {'class': 'data-item'}):
            items_list.append(items.text)
        latitude = items_list[8].replace('Latitude:', '')
        longitude = items_list[9].replace('Longitude:', '')
        latitude = latitude.strip()
        longitude = longitude.strip()
        request_url = 'https://api.darksky.net/forecast/'+DARK_SKY_KEY+'/'+str(latitude)+','+str(longitude)
        headers = {'Accept-Encoding': 'gzip, deflate'}
        response = requests.get(request_url, headers=headers)
        response = json.loads(response.text)
        response = response['currently']
        self.weather_dict = response

    def get_foreign_weather(self):
        location = self.command_dict['postmodifier']
        response = requests.get('http://api.geonames.org/searchJSON?q='+location+'&maxRows=10&username='+GEONAMES_USERNAME)
        response = json.loads(response.text)
        response = response['geonames'][0]
        latitude = response['lat']
        longitude = response['lng']
        request_url = 'https://api.darksky.net/forecast/' + DARK_SKY_KEY + '/' + str(latitude) + ',' + str(longitude)
        headers = {'Accept-Encoding': 'gzip, deflate'}
        response = requests.get(request_url, headers=headers)
        response = json.loads(response.text)
        response = response['currently']
        self.weather_dict = response

    def vocalize__weather(self):
        location = self.command_dict['postmodifier']
        # can be improved with mannerisms
        if location == '':
            vocalize('Currently, the temperature is '+str(self.weather_dict['temperature'])+' degrees, humidity is at '+
                     str(round(float(self.weather_dict['humidity'])*100, 1))+' percent, the chance of precipitation is '+
                     str(round(float(self.weather_dict['precipProbability'])*100, 1))+' percent, wind speeds are at '+
                     str(self.weather_dict['windSpeed'])+' miles per hour, and cloud coverage is around '+
                     str(round(float(self.weather_dict['cloudCover'])*100, 1))+' percent.')
        else:
            vocalize('Currently, in'+location+', the temperature is'+str(self.weather_dict['temperature'])+
                     ' degrees, humidity is at '+
                     str(round(float(self.weather_dict['humidity'])*100, 1))+' percent, the chance of precipitation is '+
                     str(round(float(self.weather_dict['precipProbability'])*100, 1))+' percent, wind speeds are at '+
                     str(self.weather_dict['windSpeed'])+' miles per hour, and cloud coverage is around '+
                     str(round(float(self.weather_dict['cloudCover'])*100, 1))+' percent.')

        self.isBlocking = False
