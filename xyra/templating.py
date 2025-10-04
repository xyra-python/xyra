from jinja2 import Environment, FileSystemLoader

class Templating:
    def __init__(self, directory="templates"):
        self.env = Environment(loader=FileSystemLoader(directory))

    def render(self, template_name, **kwargs):
        template = self.env.get_template(template_name)
        return template.render(**kwargs)