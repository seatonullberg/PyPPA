from Speaker import vocalize
from Plugins.base_plugin import BasePlugin


# TODO: modify to fit inheritance scheme
class GoogleSearchBeta(BasePlugin):

    def __init__(self, command):
        self.driver = None
        self.COMMAND_HOOK_DICT = {'open': ['open']}
        self.MODIFIERS = {'open': {'number': ['number']}}
        super().__init__(command=command,
                         command_hook_dict=self.COMMAND_HOOK_DICT,
                         modifiers=self.MODIFIERS)

    def function_handler(self, args=None):
        # expect webdriver as args
        self.driver = args
        if self.command_dict['modifier'] == 'number':
            # open the link from specified position
            # use postmodifier to identify position
            self.open_link(str_number=self.command_dict['postmodifier'])
        else:
            # no modifier
            # use the premodifier as keyword search to open link containing keyword/phrase
            self.open_link(keyphrase=self.command_dict['premodifier'])
        # keep active loop in google_beta function handler context
        self.lock_context(args=self.driver, pre_buffer=15)

    def open_link(self, str_number=None, keyphrase=None):
        link_list = []
        text_list = []
        links = self.driver.find_elements_by_xpath('//div/h3/a')
        for link in links:
            link_list.append(link.get_attribute('href'))
            text_list.append(link.get_attribute('text'))
        text_list = [text.lower() for text in text_list]

        # get by number
        if str_number is not None and keyphrase is None:
            num_dict = {'one': 0, 'two': 1, 'three': 2, 'four': 3, 'five': 4,
                        'six': 5, 'seven': 6, 'eight': 7, 'nine': 8, 'ten': 9,
                        '1': 0, '2': 1, '3': 2, '4': 3, '5': 4, '6': 5,
                        '7': 6, '8': 7, '9': 8, '10': 9}
            try:
                link = link_list[num_dict[str_number]]
            except IndexError:
                # not enough links in list
                vocalize('Sorry, I could not find link number {}'.format(str_number))
            except AttributeError:
                vocalize('Sorry, I could not find link number {}'.format(str_number))
            else:
                self.driver.get(link)
        # get by keyword
        elif keyphrase is not None and str_number is None:
            if len(text_list) == 0:
                vocalize('Sorry, I was unable to find any links containing the phrase {}'.format(keyphrase))
                return
            for i, link_text in enumerate(text_list):
                if keyphrase in link_text:
                    # the keyphrase matches the link test
                    self.driver.get(link_list[i])
                    break
                elif i >= len(text_list) - 1:
                    # if no link has matched and the last link was just checked
                    # vocalize the failure
                    vocalize('Sorry, I was unable to find any links containing the phrase {}'.format(keyphrase))
                    break
                else:
                    continue
