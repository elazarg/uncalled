import re


class Flags:
    include_strings = True
    ignore_underscored_methods = True
    ignore_underscored = True
    track_classes = False
    track_variables = True


class Frameworks:
    ast = True
    pytest = True
    unittest = True
    flask = True


def get_matcher(method_prefix=r'\.'):
    def methods(*items):
        return [method_prefix + x for x in items]

    prefixes = methods('__.+')
    if Frameworks.ast:
        prefixes += methods('generic_visit', 'visit_.+')
    if Frameworks.unittest:
        prefixes += ['tearDown', 'setUp']
    if Frameworks.pytest:
        prefixes += ['test_.+', 'call', 'pytest_.*']
        prefixes += methods('test_.+', 'runtest', 'run_test', 'set_up', 'setup', 'teardown', 'cases')
    if Frameworks.flask:
        prefixes += ['before_request', 'after_request', 'put', 'get', 'post', 'delete', 'patch',
                     'head', 'options', 'trace', 'route', 'errorhandler']
    if Flags.ignore_underscored_methods:
        prefixes += methods('_.+')
    if Flags.ignore_underscored:
        prefixes.append('_.+')

    return re.compile('|'.join('({})'.format(p) for p in prefixes)).fullmatch
