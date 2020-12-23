from behave import when, given, then
import json
import os
import websocket


@given(u'a connection to the websocket')
def step_impl(context):
    context.ws = websocket.WebSocket()
    context.ws.connect(f'ws://{context.api_host}:{context.api_port}/ws')
    assert context.ws


@when(u'I send a simple test message')
def step_impl(context):
    context.ws.send(json.dumps({
        'payload': 'coucou',
        'action': 'test',
    }))


@then(u'I receive a response')
def step_impl(context):
    result = json.loads(context.ws.recv())
    assert result['action'] == 'test'
    assert result['payload'] == 'coucou'


@when(u'I close the connection')
def step_impl(context):
    context.ws.close()


@then(u'the connection is closed')
def step_impl(context):
    assert context.ws.connected is False


@when(u'I send a test file')
def step_impl(context):
    fpath = os.path.join(os.getcwd(), 'resources/test_fr_7_img.pdf')
    context.ws.send(json.dumps({
        'action': 'upload',
        'filename': 'test_fr_7_img.pdf',
    }))
    result = json.loads(context.ws.recv())
    assert result['action'] == 'upload'

    i = 1
    with open(fpath, 'rb') as f:
        while chunk := f.read(4096):
            print(f'sending chunk {i}')
            context.ws.send_binary(chunk)
            i += 1
        context.ws.send_binary('')


@then(u'I can query the file status')
def step_impl(context):
    context.ws.send(json.dumps({
        'action': 'get_file_status',
    }))
    result = json.loads(context.ws.recv())
    print(result)
    assert result['action'] == 'get_file_status'
    assert result['payload'] == 'uploaded'
