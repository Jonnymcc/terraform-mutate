import os
import yaml
import json
import subprocess

with open('mutate-config.yml') as f:
    config = yaml.load(f)

state = json.loads(subprocess.check_output(['terraform', 'state', 'pull']))


def get_module(module_name):
    module_path = ['root', module_name.split('.')[1]]
    return next((m for m in state['modules'] if m['path'] == module_path), {})


def get_resource_from_module(resource_name, module):
    return module['resources'].get(resource_name, {})


def extract_module_resource_names(resource_name):
    tokens = resource_name.split('.')
    if tokens[0] == 'module':
        module_name = '.'.join(tokens[0:2])
        resource_name = '.'.join(tokens[2:4])
    else:
        return
    return module_name, resource_name


def get_resource(resource_name):
    module_name, resource_name = extract_module_resource_names(resource_name)
    module = get_module(module_name)
    if not module:
        return
    resource = get_resource_from_module(resource_name, module)
    if not resource:
        return
    resource['id'] = resource['primary']['id']
    return resource


def import_by_config_mapping():
    for source_name, target_name in config.items():
        resource = get_resource(source_name)
        if not resource:
            print '\033[33msource "%s" not found, skipping...\033[0m' % source_name
            continue

        print 'Moving', source_name, 'to', target_name
        if get_resource(target_name):
            replace_it = raw_input('"%s" already exists, should we replace it? yes/no\n' % target_name)
            if replace_it == 'yes':
                os.system('terraform state rm %s' % target_name)
            else:
                continue
        os.system('terraform state mv %s %s' % (source_name, target_name))


import_by_config_mapping()
