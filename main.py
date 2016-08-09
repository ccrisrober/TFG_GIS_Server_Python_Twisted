'''
Copyright (c) 2015, maldicion069 (Cristian Rodríguez) <ccrisrober@gmail.con>
//
Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.
//
THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
'''
from twisted.internet.protocol import Protocol, Factory
from twisted.internet import *
from twisted.internet import reactor
import json
import threading

import key_object
import object_user
import map

def jdefault(o):
    return o.__dict__


class TCPServer(Protocol):
    def connectionMade(self):
        print "A Client Has Connected"
        self.factory.lock_sockets.acquire()
        self.factory.clients.append(self)
        self.factory.lock_sockets.release()

    def connectionLost(self, reason):
        self.factory.clients.remove(self)
        self.transport.write('somebody was disconnected from the server')

    def dataReceived(self, data):
        try:
            msg_ = json.loads(data)
            action = msg_["Action"]

            print action

            if action == "initWName":
                username = str(msg_["Name"])
                self.name = username
                self.id = self.factory.counter
                self.factory.counter = self.factory.counter + 1

                obj_user = object_user.ObjectUser(self.id, 5*64, 5*64)

                info = json.dumps({"Action": "sendMap", "Map": self.factory.maps[0],
                            "X": obj_user.PosX, "Y": obj_user.PosY, "Id": obj_user.Id,
                            "Users": self.factory.positions}, default=jdefault)+"\n"

                print(info)

                self.factory.lock_positions.acquire()
                self.factory.positions[self.id] = obj_user
                self.factory.lock_positions.release()

                self.transport.write(info)

                if self.factory.is_game:
                    data = json.dumps({
                        "Action": "new", "Id": obj_user.Id, "PosX": obj_user.PosX, "PosY": obj_user.PosY
                    }, default=jdefault).encode("utf-8")

            elif action == "move":
                self.factory.lock_positions.acquire()
                self.factory.positions[self.id].set_position(msg_["Pos"]["X"], msg_["Pos"]["Y"])
                self.factory.lock_positions.release()

                if not self.factory.is_game:
                    self.transport.write(data + '\n')
            elif action == "position":
                pass
            elif action == "fight":
                pass
            elif action == "finishBattle":
                pass
            elif action == "getObj":
                pass
            elif action == "freeObj":
                pass
            elif action == "exit":
                # Erase socket from positions!!
                self.factory.lock_positions.acquire()
                if self.id in self.factory.positions: del self.factory.positions[self.id]
                self.factory.lock_positions.release()
                # Erase socket!!
                if not is_game:
                    self.transport.write(json.dumps(({"Action": "exit", "Id": "Me"})).encode("utf-8") + '\n')

                if is_game:
                    data = json.dumps({"Action": "exit", "Id": self.id}, default=jdefault).encode("utf-8")

            for c in self.factory.clients:
                if c.name != self.name:
                    c.message(data)            #post message for all clients to see

        except Exception as e:
            print "Error({0}): ".format(e)
            pass

    def message(self, message): #helper method to send text to all clients
        self.transport.write(message + '\n')


if __name__ == '__main__':
    factory = Factory()
    factory.protocol = TCPServer
    factory.clients = []
    factory.counter = 0
    factory.positions = {}


    # Preguntamos si es juego o test
    mode = raw_input('[S/s] Server Mode / [] Test Mode:')
    is_game = False
    if mode == "s" or mode == "S":
        is_game = True

    print(is_game)

    factory.is_game = is_game
    factory.maps = []
    factory.users_port = {}
    factory.RealObjects = {}

    factory.lock_positions = threading.Lock()
    factory.lock_sockets = threading.Lock()

    factory.keys = {
       "Red": key_object.KeyObject(1, 5*64, 5*64, "Red"),
       "Blue": key_object.KeyObject(2, 6*64, 5*64, "Blue"),
       "Yellow": key_object.KeyObject(3, 7*64, 5*64, "Yellow"),
       "Green": key_object.KeyObject(4, 8*64, 5*64, "Green")
    }

    config = json.loads(open('data.json').read())

    map_0 = ""
    keys_0 = []

    for line in config["map"]:
        map_0 += line
    for key in config["keys"]:
        keys_0.append(factory.keys[key])

    factory.maps.append(map.Map(config["id"],
                map_0,
                config["width"],
                config["height"],
                keys_0))

    print (json.dumps(factory.maps[0], default=jdefault))

    reactor.listenTCP(8091, factory)                           
    print "Server started"
    reactor.run()
