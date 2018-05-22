

# TODO: implement voice and html constructors
# TODO: Work out Flask and webbrowser interoperability
class PresentationParser(object):

    def __init__(self, fname):
        self.fname = fname
        self.META_FLAGS = ['-save_location']
        self.OPTIONS = {'<frame>': ['duration'],
                        '<voice>': ['kind'],
                        '<html>': ['kind']}
        self.metadata = []
        self.frames = []
        self.file_lines = open(self.fname, 'r').readlines()
        self.parse()

    def parse(self):
        for i, line in enumerate(self.file_lines):
            if line.startswith('<frame'):
                self.build_frame(i)

    def build_frame(self, line_number):
        duration = self.file_lines[line_number].replace('<', '').replace('>', '')
        duration = duration.split()
        if len(duration) > 1:
            duration = duration[1].split('=')[1]
        else:
            duration = None
        content = []
        for i, line in enumerate(self.file_lines[line_number+1:]):
            if line.startswith('<voice'):
                voice = self.build_voice(i+line_number+1)
                content.append(voice)
            elif line.startswith('<html'):
                html = self.build_html(i+line_number+1)
                content.append(html)
            elif line.startswith('</frame>'):
                break
        self.frames.append({'duration': duration, 'content': content})

    def build_voice(self, line_number):
        kind = self.file_lines[line_number].replace('<', '').replace('>', '')
        kind = kind.split()
        if len(kind) > 1:
            kind = kind[1].split('=')[1]
        else:
            kind = 'raw'

        if kind == 'raw':
            # read the lines and send to speech module for translation
            # this doesnt work yet
            voice_path = None
        elif kind == 'wav':
            # a wav path is already provided so grab it and return it
            voice_path = self.file_lines[line_number+1]
        elif kind == 'txt':
            # a path to a text file is provided so grab that, translate, then return
            # too lazy to implement right now
            voice_path = None
        else:
            voice_path = None

        return voice_path

    def build_html(self, line_number):
        kind = self.file_lines[line_number].replace('<', '').replace('>', '')
        kind = kind.split()
        if len(kind) > 1:
            kind = kind[1].split('=')[1]
        else:
            kind = 'raw'

        if kind == 'raw':
            # read the lines and save as .html file then return that path
            # too lazy
            html_path = None
        elif kind == 'path':
            # a path to a html file is provided so return that
            html_path = self.file_lines[line_number+1]
        else:
            html_path = None

        return html_path


if __name__ == "__main__":
    pp = PresentationParser('example.pypr')
    print(pp.frames)