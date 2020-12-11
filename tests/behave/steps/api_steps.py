import requests
import os
from behave import when, given, then


@given(u'the api is available')
def step_impl(context):
    r = requests.get(f'http://{context.api_host}:{context.api_port}/')
    data = r.json()
    assert r.status_code == 200
    assert 'all_systems' in data
    assert data['all_systems'] == 'nominal'


@when(u'I access the server root')
def step_impl(context):
    r = requests.get(f'http://{context.api_host}:{context.api_port}/')
    context.json = r.json()


@then(u'I receive some data')
def step_impl(context):
    assert 'all_systems' in context.json
    assert context.json['all_systems'] == 'nominal'
