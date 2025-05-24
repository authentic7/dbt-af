from datetime import timedelta

import attrs
import pytest

from dbt_af.conf import DefaultArgsConfig, RetryPolicy


@pytest.fixture
def custom_retry_policy():
    """Fixture for a custom RetryPolicy."""
    return RetryPolicy(retries=5, retry_delay=timedelta(seconds=10))


@pytest.fixture
def comprehensive_retry_policy():
    """Fixture for a comprehensive RetryPolicy with all fields."""
    return RetryPolicy(
        retries=3,
        retry_delay=timedelta(seconds=5),
        retry_exponential_backoff=True,
        max_retry_delay=timedelta(hours=1),
    )


def test_default_args_config_default():
    """Test DefaultArgsConfig with default values."""
    default_config = DefaultArgsConfig()
    # Check that owner is None by default
    assert default_config.owner == 'airflow'
    # Check default retry policy values
    assert default_config.retry_policy.retries == 1
    assert default_config.retry_policy.retry_delay == timedelta(minutes=1)
    assert default_config.retry_policy.retry_exponential_backoff is False
    # Check as_dict excludes None owner
    result = default_config.as_dict()
    expected = {
        'retries': 1,
        'retry_delay': timedelta(minutes=1),
        'retry_exponential_backoff': False,
    }
    assert result == expected


def test_default_args_config_with_owner():
    """Test DefaultArgsConfig with owner set."""
    config = DefaultArgsConfig(owner='data_team')
    assert config.owner == 'data_team'
    result = config.as_dict()
    expected = {
        'owner': 'data_team',
        'retries': 1,
        'retry_delay': timedelta(minutes=1),
        'retry_exponential_backoff': False,
    }
    assert result == expected


def test_default_args_config_with_custom_retry_policy(custom_retry_policy):
    """Test DefaultArgsConfig with custom retry policy."""
    config = DefaultArgsConfig(owner='team_a', retry_policy=custom_retry_policy)
    assert config.owner == 'team_a'
    assert config.retry_policy == custom_retry_policy

    result = config.as_dict()
    expected = {'owner': 'team_a', 'retries': 5, 'retry_delay': timedelta(seconds=10)}
    assert result == expected


def test_default_args_config_with_comprehensive_retry(comprehensive_retry_policy):
    """Test DefaultArgsConfig with comprehensive retry policy."""
    config = DefaultArgsConfig(owner='team_b', retry_policy=comprehensive_retry_policy)
    result = config.as_dict()
    expected = {
        'owner': 'team_b',
        'retries': 3,
        'retry_delay': timedelta(seconds=5),
        'retry_exponential_backoff': True,
        'max_retry_delay': timedelta(hours=1),
    }
    assert result == expected


def test_default_args_config_empty_retry_policy():
    """Test DefaultArgsConfig with empty RetryPolicy (all None)."""
    empty_retry = RetryPolicy()
    config = DefaultArgsConfig(owner='team_a', retry_policy=empty_retry)
    result = config.as_dict()
    expected = {'owner': 'team_a'}
    assert result == expected


def test_default_args_config_none_owner():
    """Test DefaultArgsConfig with explicit None owner."""
    config = DefaultArgsConfig(
        owner=None,
        retry_policy=RetryPolicy(retries=2, retry_delay=timedelta(minutes=2)),
    )
    result = config.as_dict()
    expected = {'retries': 2, 'retry_delay': timedelta(minutes=2)}
    assert result == expected
    assert 'owner' not in result


def test_default_args_config_factory_pattern():
    """Test DefaultArgsConfig used in factory pattern."""

    @attrs.define(frozen=True)
    class MockDagConfig:
        default_args: DefaultArgsConfig = attrs.field(factory=lambda: DefaultArgsConfig(owner='airflow'))

    dag_config = MockDagConfig()
    result = dag_config.default_args.as_dict()
    expected = {
        'owner': 'airflow',
        'retries': 1,
        'retry_delay': timedelta(minutes=1),
        'retry_exponential_backoff': False,
    }
    assert result == expected


def test_default_args_config_as_dict_structure():
    """Test that as_dict() follows the expected structure."""
    config = DefaultArgsConfig()
    # Test that all fields are dynamically handled
    for field in attrs.fields(DefaultArgsConfig):
        if field.name == 'retry_policy':
            continue  # Skip nested config object
        value = getattr(config, field.name)
        if value is not None:
            assert field.name in config.as_dict()


def test_default_args_config_retry_policy_not_in_dict():
    """Test that retry_policy object itself is not included in as_dict()."""
    config = DefaultArgsConfig(owner='airflow')
    result = config.as_dict()
    assert 'retry_policy' not in result


@pytest.mark.parametrize(
    'owner,retries,expected_keys',
    [
        ('team_a', 1, {'owner', 'retries', 'retry_delay', 'retry_exponential_backoff'}),
        (None, 2, {'retries', 'retry_delay', 'retry_exponential_backoff'}),
        ('team_b', 3, {'owner', 'retries', 'retry_delay', 'retry_exponential_backoff'}),
    ],
)
def test_default_args_config_parametrized(owner, retries, expected_keys):
    """Test DefaultArgsConfig with parametrized values."""
    config = DefaultArgsConfig(
        owner=owner,
        retry_policy=RetryPolicy(
            retries=retries,
            retry_delay=timedelta(minutes=1),
            retry_exponential_backoff=False,
        ),
    )
    result = config.as_dict()
    assert set(result.keys()) == expected_keys
    assert result['retries'] == retries


def test_default_args_config_immutability():
    """Test that DefaultArgsConfig is immutable."""
    config = DefaultArgsConfig(owner='airflow')
    with pytest.raises(attrs.exceptions.FrozenInstanceError):
        config.owner = 'modified'
