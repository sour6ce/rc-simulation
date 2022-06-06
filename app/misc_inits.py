from app.core.main import Application, PluginInit1


class Init(PluginInit1):
    def run(self, app: Application, *args, **kwargs):
        app.config['signal_time'] = '10'
        app.config['advanced.input_timeout'] = '-1'
        app.config['advanced.arp_skip_threshold'] = '1280'
        app.config['ping_delay'] = '100'

        app.script_pipe.append(lambda s: [l.replace(
            '\n', '').strip() for l in s if l.strip() and l.strip()[0] != '#'])
