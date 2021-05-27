import os
from typing import Optional

import boto3
import yaml


class ConfigLoaderException(Exception):
    # 1. Please, consider move that exception into separate file with exceptions.
    # 2. How about adding a constructor with default message? Ex:
    #  _MESSAGE = "Error when opening {}"
    #  def __init__(self, path):
    #      super().__init__(self._MESSAGE.format(path))
    # In that way, you can avoid a lot of repetitive parts of code
    pass


class Config:
    # I think that class should be moved into a separate file called 'config.py'

    def __init__(self, config: dict, source: str):
        self._config = config
        self._source = source

    @property
    # I think we can just change the '_source' variable from private to public instead of creating an additional line of code
    def source(self):
        return self._source

    def __repr__(self):
        # 1.I 'm assuming that you are trying to display the two lines of string. In that case,
        # you should add a special character \n at the end of the first line
        # 2. I 'm not sure if __repr__ is a good choice here. __repr__
        # is using mainly to display some sophisticated information for developers, like ex.information about
        # class or elements of source code.The string below look like just regular information
        # for the end - user.Maybe we should consider overload __str__ instead of __repr__  ?
        return (f'Config(config={self._config!r}'
                f'       source={self.source!r})')

    def __getattr__(self, name):
        return self._config[name]

    def __getitem__(self, name):
        return self._config[name]

    def get(self, name, default=None):
        return self._config.get(name, default)


class ConfigLoader:
    # Please remove whitespace
    """Loads configuration files.

    Source of the config depends on the currently set environment (either
    'test' or 'prod', as dictated by the *env* file.
    """

    S3_BUCKET = 'configs'
    _instance = None
    _instance_ready = False

    # Make this class a singleton since usually config is loaded only once.
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, defaults: dict = {}):
        # From one side - empty dictionary (so mutable value) as a default value might be dangerous.
        # From the second side however - you gonna use that value only in the constructor so probably only once
        # Anyway, you should refactor that into:
        # def __init__(self, defaults: dict = None)
        # self.defaults = defaults or {}
        if self._instance_ready:
            return
        # Returning anything from the constructor is an antipattern. How about:
        # if not self._instance_ready:
        #    self._setup_env() <--- that method may contain a rest of constructor logic
        self.defaults = defaults
        env: str = open('env').read().strip()
        # Please, use 'with' context manager to open that file.
        # You can find a detailed explanation here:
        # https://docs.python.org/3/tutorial/inputoutput.html#reading-and-writing-files
        print(f'Current environment is: {env!r}')
        # I'm not sure if simple print will display any information from ex docker container (it possible but AFAIK
        # we need to add PYTHONBUFFERED env variable into a container). Please, consider using some logging library.
        # The logging module from the standard library should do the trick.
        if env == 'test':
            self._handler = self._local_loader
        elif env == 'prod':
            self._handler = self._s3_loader
        # How about:
        # handlers = {
        #     'test' : self._local_loader,
        #     'prod' : self._s3_loader
        # }
        # self._handler = handlers.get(env, <some_default_handler>)
        # Btw. each handler function returining an dict object. Maybe we should consider change the variable name
        # from handler to content?
        self._config: Optional[Config] = None
        self._instance_ready = True

    def _local_loader(self, path: str) -> dict:
        try:
            with open(path) as f:
                config = yaml.load(f)
        except Exception:
            # 1. The exception clause is too broad. Please, put here a specific exception
            # 2. The path should only argument here. Please check my comment above, near the line nr. 8
            raise ConfigLoaderException(f'Error opening {path}')
        return config

    def _s3_loader(self, path: str) -> dict:
        try:
            f = boto3.client('s3').download_fileobj(self.S3_BUCKET, path)
            config = yaml.load(f)
        except Exception:
            # 1. The exception clause is too broad. Please, put here a specific exception
            # 2. The path should only argument here. Please check my comment above, near the line nr. 8
            raise ConfigLoaderException(f'Error when opening {path}')
        return config


    def load(self, path: str) -> Config:
        # That function is too broad and i see a potential for splitting. Please, check my further comments, below.
        # Furthemore I have a feeling if you move some part of that function into Config class as a public method,
        # you can easily refactor that function into:
        # return self._config or Config(self._handler(path), path)
        if self._config:
            return self._config
        config = self._handler(path)
        environ = os.environ
        for key in config:
            if key in environ:
                config[key] = os.environ[key]
        # I'm think the better idea will be move these three lines above to the Config class as public method:
        # def set_vars_from_local_env(self):
        #    env = os.environ
        #    for key in (k for k self._config if k in env):
        #        self._config[key] = env[key]
        for key in self.defaults:
            if key not in config:
                config[key] = self.defaults[key]
        # The same as above:
        # def set_defaults_vars(self, defaults):
        #    for key in (k for k in defaults if k not in self._config):
        #        config[key] = defaults[key]
        self._config = Config(config, path)
        return self._config

    def reset(self):
        self._config = None
