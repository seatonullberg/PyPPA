from selenium import webdriver


class WebDriver(webdriver.Chrome):
    """
    A convenient preconfigured selenium webdriver object
    """

    def __init__(self, configuration, options=None):
        """
        Configures a selenium webdriver object
        :param configuration: configuration object from the calling plugin
        :param options: webdriver.ChromeOptions object to specify custom options
        """
        chromedriver_path = configuration.environment_variables['Base']['CHROMEDRIVER_PATH']
        if options is None:
            options = webdriver.ChromeOptions()
            options.add_argument('--no-sandbox')
            options.add_argument('--no-default-browser-check')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-default-apps')
            options.add_argument("--window-size=1920,1080")
        super().__init__(executable_path=chromedriver_path, options=options)
