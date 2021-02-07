import requests
from matplotlib import pyplot as plt
from tabulate import tabulate


urls = {
    'findAll': 'http://api.gios.gov.pl/pjp-api/rest/station/findAll',
    'stationInfo': 'http://api.gios.gov.pl/pjp-api/rest/station/sensors/{stationId}',
    'sensorData': 'http://api.gios.gov.pl/pjp-api/rest/data/getData/{sensorId}'
}


def get_station_info(id):
    result = requests.get(urls['stationInfo'].format(stationId=id))
    return result.json()


def get_sensor_data(id):
    result = requests.get(urls['sensorData'].format(sensorId=id))
    return result.json()


class Station:
    '''Class to represent a single station'''
    def __init__(self, station_dict: dict) -> object:
        self._id = station_dict['id']
        self._name = station_dict['stationName']
        self._latitude = station_dict['gegrLat']
        self._longitude = station_dict['gegrLon']
        self._address = station_dict['addressStreet']

        # Some stations have no entry for parameter 'city', hence:
        if station_dict['city']:
            self._city = station_dict['city']['name']
            self._commune = station_dict['city']['commune']['communeName']
            self._district = station_dict['city']['commune']['districtName']
            self._province = station_dict['city']['commune']['provinceName']

    def getSensors(self):
        self._sensors = [Sensor(sensor_dict) for sensor_dict in get_station_info(self._id)]

    def id(self) -> int:
        return self._id

    def name(self) -> str:
        return self._name

    def coordinates(self) -> tuple:
        return self._latitude, self._longitude

    def address(self) -> str:
        return self._address

    def sensors(self) -> list:
        '''Returns list of Sensor objects'''
        return self._sensors

    def city(self) -> str:
        if self._city:
            return self._city
        else:
            return None

    def commune(self) -> tuple:
        '''Returns detailed administrative location'''
        if self._city:
            return self._city, self._commune, self._district, self._province

    def shortlist(self) -> list:
        '''Returns list of id and name'''
        return [self._id, self._name]


class Sensor:
    '''Class representing a single sensor'''
    def __init__(self, sensor_dict: dict) -> object:
        self._id = sensor_dict['id']
        self._param = sensor_dict['param']['paramName']
        self._paramFormula = sensor_dict['param']['paramFormula']
        self._paramCode = sensor_dict['param']['paramCode']
        self._paramId = sensor_dict['param']['idParam']

        self._readings = [Reading(reading_dict) for reading_dict in get_sensor_data(self._id)['values']][::-1]

    def id(self) -> int:
        return self._id

    def param(self) -> str:
        return self._param

    def paramFormula(self) -> str:
        return self._paramFormula

    def readings(self) -> list:
        '''Returns list of Reading class objects'''
        return self._readings


class Reading:
    '''Class representing a single sensor reading'''
    def __init__(self, sensor_dict: dict) -> object:
        self._date = sensor_dict['date']
        self._value = sensor_dict['value']

    def date(self) -> str:
        return self._date

    def value(self) -> int:
        return self._value


def main():
    print('Fetching data, please wait...')
    fetched_data = requests.get(urls['findAll']).json()
    stations_list = [Station(station_data) for station_data in fetched_data]

    city = input('Search for stations in a city: ')

    search_result = [station for station in stations_list if city in station.name()]

    if not search_result:
        print('No stations found following given input')
        return

    result_table = [station.shortlist() for station in search_result]
    print(tabulate(result_table, headers=['Id', 'Station name']))

    choice = int(input('Select station to plot(id): '))

    try:
        chosen_station = [station for station in search_result if station.id() == choice][0]
    except IndexError:
        print('Invalid input')
        return

    chosen_station.getSensors()

    print(f'{chosen_station.id()}\t{chosen_station.name()}')

    for sensor in chosen_station.sensors():
        dates = [reading.date() for reading in sensor.readings()]
        values = [reading.value() for reading in sensor.readings()]
        plt.plot(dates, values, label=sensor.paramFormula())

    plt.title(label=chosen_station.name())
    plt.xticks(rotation=45, ha='right', fontsize=6)
    plt.legend()
    plt.show()


if __name__ == "__main__":
    main()
