from Speaker import vocalize


# TODO: modify to fit inheritance scheme
class GoogleSearchBeta(object):

    def __init__(self, command, driver):
        self.command = command
        self.driver = driver
        self.COMMAND_HOOK_DICT = {'open link': ['open link', 'open']}
        self.FUNCTION_KEY_DICT = {'1': ['number 1', 'number one', 'the first', 'one'],
                                  '2': ['number 2', 'number two', 'the second', 'two', 'too', 'to'],
                                  '3': ['number 3', 'number three', 'the third', 'three'],
                                  '4': ['number 4', 'number four', 'the fourth', 'four'],
                                  '5': ['number 5', 'number five', 'the fifth', 'five'],
                                  '6': ['number 6', 'number six', 'the sixth', 'six'],
                                  '7': ['number 7', 'number seven', 'the seventh', 'the last', 'seven']}

    def function_handler(self):
        for variations in self.COMMAND_HOOK_DICT['open link']:
            if variations in self.command:
                self.open_link()
                return

    def update_database(self):
        pass

    def open_link(self):
        link_list = []
        links = self.driver.find_elements_by_xpath('//div/h3/a')
        for link in links:
            link_list.append(link.get_attribute('href'))

        for indices in self.FUNCTION_KEY_DICT:
            for variations in self.FUNCTION_KEY_DICT[indices]:
                if variations in self.command:
                    self.driver.get(link_list[int(indices)-1])
                    return
        # if no number is specified open the first link
        self.driver.get(link_list[0])
