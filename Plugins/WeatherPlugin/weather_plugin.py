import requests
from bs4 import BeautifulSoup
import json
from Plugins import base


# TODO: add 'forecast' premodifier
class WeatherPlugin(base.Plugin):

    def __init__(self):
        self.command_hooks = {self.check_weather: ['check the weather',
                                                   'what is the weather',
                                                   "what's the weather",
                                                   'check weather']}
        self.modifiers = {self.check_weather: {'in': ['in', 'on']}}
        self.name = 'WeatherPlugin'
        super().__init__(command_hooks=self.command_hooks,
                         modifiers=self.modifiers,
                         name=self.name)

    def check_weather(self):
        if self.command.modifier == 'in':
            # get weather for specific location
            self.get_foreign_weather()
        else:
            # get local weather
            self.get_local_weather()
        self.sleep()

    def get_local_weather(self):
        # load environment variable
        api_key = self.environment_variable('API_KEY')

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
        request_url = 'https://api.darksky.net/forecast/{}/{},{}'.format(api_key,
                                                                         latitude,
                                                                         longitude)
        headers = {'Accept-Encoding': 'gzip, deflate'}
        response = requests.get(request_url, headers=headers)
        response = json.loads(response.text)
        response = response['currently']
        self.vocalize__weather(response)

    def get_foreign_weather(self):
        # load environment_variables
        api_key = self.environment_variable('API_KEY')
        username = self.environment_variable('USERNAME')

        location = self.command.postmodifier
        response = requests.get('http://api.geonames.org/searchJSON?q={}&maxRows=10&username={}'.format(location,
                                                                                                        username))
        response = json.loads(response.text)
        response = response['geonames'][0]
        latitude = response['lat']
        longitude = response['lng']
        request_url = 'https://api.darksky.net/forecast/{}/{},{}'.format(api_key,
                                                                         latitude,
                                                                         longitude)
        headers = {'Accept-Encoding': 'gzip, deflate'}
        response = requests.get(request_url, headers=headers)
        response = json.loads(response.text)
        response = response['currently']
        self.vocalize__weather(response)

    def vocalize__weather(self, weather_dict):
        weather_dict['temperature'] = str(int(weather_dict['temperature']))
        weather_dict['humidity'] = str(int(float(weather_dict['humidity'])*100))
        weather_dict['precipProbability'] = str(int(float(weather_dict['precipProbability'])*100))
        weather_dict['cloudCover'] = str(int(float(weather_dict['cloudCover'])*100))
        weather_dict['windSpeed'] = str(weather_dict['windSpeed'])
        if self.command.postmodifier:
            location = 'in {}'.format(self.command.postmodifier)
        else:
            location = ''
        self.vocalize('''currently {location}, the temperature is {temperature} degrees, 
                      humidity is at {humidity} percent, the chance of precipitation is {precip} percent, 
                      wind is blowing at {wind} miles per hour, 
                      and cloud coverage is {cloud} percent.'''.format(location=location,
                                                                       temperature=weather_dict['temperature'],
                                                                       humidity=weather_dict['humidity'],
                                                                       precip=weather_dict['precipProbability'],
                                                                       wind=weather_dict['windSpeed'],
                                                                       cloud=weather_dict['cloudCover']))
