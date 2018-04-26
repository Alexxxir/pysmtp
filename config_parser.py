import configparser
import re
import sys
import base64


class ConfigParser:
    def __init__(self):
        self._conf = configparser.RawConfigParser()
        self.recipients = []
        self._topic = ''
        self._letter = ''
        self._text = ''
        self._files = []

    def config_parser(self):
        try:
            self._conf.read('data/config.ini')
            self.recipients = self._get_options("recipients")
            self._topic = self._conf.get("topic", "topic")
            self._letter = open(self._conf.get("letter", "letter"))
            self._text = re.sub(r'(?<=\n)(\.+)(?=\n)', r'\1.',
                                self._letter.read())
            self._files = list(map(lambda x: open(x, 'rb'),
                                   self._get_options("files")))
        except configparser.Error as e:
            print("Файл config.ini, %s" % e, file=sys.stderr)
            sys.exit(2)
        except OSError as e:
            print("Неправильный файл в config.ini, %s" % e, file=sys.stderr)
            sys.exit(3)
        return self

    def get_letter(self, sender):
        def insert_file(file):
            return (b'--A4D921C2D10D7DB\n'
                    b'Content-Type: application/octet-stream; name="%s"\n'
                    b'Content-transfer-encoding: base64\n'
                    b'Content-Disposition: attachment; filename="%s"\n'
                    b'\n'
                    b'%s\n'
                    b'\n') % (file[1].encode(), file[1].encode(),
                              file[0])

        files = list(map(lambda x, : (base64.b64encode(x.read()), x.name),
                         self._files))
        answer = (b'From: %s\n'
                  b'Subject: %s\n'
                  b'MIME-Version: 1.0\n'
                  b'Content-Type: multipart/mixed; '
                  b'boundary="A4D921C2D10D7DB"\n\n'
                  b'%s'
                  b'--A4D921C2D10D7DB\n'
                  b'Content-type: text/plain; charset=utf-8\n'
                  b'Content-Transfer-Encoding: 8bit\n'
                  b'\n'
                  b'%s\n'
                  b'\n'
                  b'--A4D921C2D10D7DB--\n'
                  %(sender.encode(),
                    self._topic.encode(),
                    b"".join(map(insert_file, files)),
                    b"%s\n.\n" % self._text.encode()))
        return answer

    def _get_options(self, section):
        return list(map(lambda x: self._conf.get(section, x),
                        self._conf.options(section)))

    def close_files(self):
        self._letter.close()
        for file in self._files:
            if file:
                file.close()

