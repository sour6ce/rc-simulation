from app.core.main import Application, PluginInit1


class Init(PluginInit1):
    def run(self, app: Application, *args, **kwargs):
        app.config['signal_time'] = '10'

        app.script_pipe.append(lambda s: [l.replace(
            '\n', '') for l in s if l.strip() and l.strip()[0] != '#'])
