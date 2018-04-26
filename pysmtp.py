#!/usr/bin/python3

from config_parser import ConfigParser
from socket import socket
import ssl
import base64
import argparse
import getpass
import sys
from enum import IntEnum


class ServerResponse(IntEnum):
    SuccessfulExecution = 250
    ServerAnswer = 334
    SuccessfulAuthentication = 235
    StartReceivingMessages = 354


class IncorrectAnswer(Exception):
    pass


def create_parser():
    parser = argparse.ArgumentParser(
        description="Клиент для отправки почты"
    )
    parser.add_argument("email", help="Логин", nargs='?')
    parser.add_argument("password", help="Пароль", nargs='?')
    return parser.parse_args()


def send(sock, command, expect_answer, to_base64=False, already_encode=False):
    if not already_encode:
        command = command.encode()
    if to_base64:
        command = base64.b64encode(command)
    sock.send(b'%s\n' % command)
    answer = sock.recv(1024).decode()
    print(answer)
    if (ServerResponse(int(answer.split()[0])) != expect_answer and
            expect_answer != 0):
        raise IncorrectAnswer(answer)


def main():
    parser = create_parser()
    config = ConfigParser().config_parser()
    if not parser.email:
        parser.email = input("Логин: ")

    if not parser.password:
        parser.password = getpass.getpass('Пароль: ')

    try:
        sock = socket()
        sock.settimeout(5)
        sock.connect(('smtp.yandex.ru', 465))
        sock = ssl.wrap_socket(sock, ssl_version=ssl.PROTOCOL_SSLv23)
        sock.recv(1024).decode()
        send(sock, 'HELO %s' % parser.email,
             ServerResponse.SuccessfulExecution)
        send(sock, 'AUTH LOGIN', ServerResponse.ServerAnswer)
        send(sock, parser.email, ServerResponse.ServerAnswer, to_base64=True)
        send(sock, parser.password,
             ServerResponse.SuccessfulAuthentication, to_base64=True)
        send(sock, 'MAIL FROM: %s' % parser.email,
             ServerResponse.SuccessfulExecution)
        for recipient in config.recipients:
            send(sock, 'RCPT TO: %s' % recipient, 0)
        send(sock, 'DATA', ServerResponse.StartReceivingMessages)
        send(sock, config.get_letter(parser.email),
             ServerResponse.SuccessfulExecution, already_encode=True)
    except OSError as e:
        print(e, file=sys.stderr)
        print("Сообщение(я) не отправленно(ы)")
        sys.exit(1)
    except IncorrectAnswer as e:
        print("Неправильный ответ сервера %s" % e, file=sys.stderr)
        print("Сообщение(я) не отправленно(ы)")
        sys.exit(4)
    finally:
        sock.close()
        config.close_files()
    print("Сообщение(я) отправленно(ы)")


if __name__ == '__main__':
    main()
