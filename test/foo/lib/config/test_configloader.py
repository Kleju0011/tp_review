from unittest.mock import Mock

import pytest

from foo.lib.config import ConfigLoader, ConfigLoaderException


def reset_config_loader_singleton():
    ConfigLoader._instance = None
    ConfigLoader._instance_ready = False


def test_load(monkeypatch):
    # 1.'load' what? I'm assuming that test checking a local loader. Please, change the test name for more meaningful.
    # 2. In an ideal world, one test case should have only one assert. I think you can achieve that, creating test class with
    # nice and clean setUp method and two test cases like: 'test_config_content' and 'test_config_source'
    reset_config_loader_singleton()
    monkeypatch.setenv('VAR3', 'not bar')
    cfg_loader = ConfigLoader(defaults={'VAR0': 'default value 0',
                                        'VAR1': 'default value 1'})
    config = cfg_loader.load('test/foo/lib/config/config.yaml')
    assert config._config == {'VAR0': 'fizz',
                              'VAR1': 'default value 1',
                              'VAR2': 'foo',
                              'VAR3': 'not bar'}
    # 1. Test data and test scenarios should be kept in a separate file called "fixtures"
    # 2. I think we shouldn't testing private variables
    assert config.source == 'test/foo/lib/config/config.yaml'


def test_load_missing():
    reset_config_loader_singleton()
    cfg_loader = ConfigLoader()
    with pytest.raises(ConfigLoaderException):
        cfg_loader.load('test/foo/lib/config/missing-config.yaml')


def test_is_a_singleton():
    reset_config_loader_singleton()
    assert ConfigLoader(defaults={'VAR0': 'default value 0'}) is ConfigLoader()


def test_load_from_s3(monkeypatch):
    # That test does too many things. Please, split that test into smaller test cases within one test class.
    reset_config_loader_singleton()
    monkeypatch.setenv('VAR1', 'not bar')

    mock_file = Mock(autospec='read')
    mock_file.read.return_value = 'prod'
    mock_open = Mock()
    mock_open.return_value = mock_file
    monkeypatch.setattr('builtins.open', mock_open)
    mock_s3_loader = Mock()
    mock_s3_loader.return_value = {'VAR0': 'foo',
                                   'VAR1': 'bar'}
    monkeypatch.setattr(ConfigLoader, '_s3_loader', mock_s3_loader)
    cfg_loader = ConfigLoader()
    config = cfg_loader.load('some/s3/path.yaml')
    assert config._config == {'VAR0': 'foo',
                              'VAR1': 'not bar'}
    assert config.source == 'some/s3/path.yaml'
