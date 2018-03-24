# lines terminated with a single '#' are Copyright (c) 2018 Jeremy Lainé and 
# have the following copyright:
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#    * Neither the name of aiortc nor the names of its contributors may
#      be used to endorse or promote products derived from this software without
#      specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import argparse                                                 #
import asyncio                                                  #
import json                                                     #
import logging                                                  #

from aiortc import RTCPeerConnection, RTCSessionDescription     #


def channel_log(channel, t, message):                           #
    print('channel(%s) %s %s' % (channel.label, t, message))    #


def channel_watch(channel):                                     #
    @channel.on('message')                                      #
    def on_message(message):                                    #
        channel_log(channel, '<', message)                      #


def create_pc():                                                #
    pc = RTCPeerConnection()                                    #

    @pc.on('datachannel')                                       #
    def on_datachannel(channel):                                #
        channel_log(channel, '-', 'created by remote party')    #
        channel_watch(channel)                                  #

    return pc                                                   #


async def run_answer(pc):                                       #
    done = asyncio.Event()                                      #

    @pc.on('datachannel')                                       #
    def on_datachannel(channel):                                #
        @channel.on('message')                                  #
        def on_message(message):                                #
            # reply                                             #
            message = 'pong'                                    #
            channel_log(channel, '>', message)                  #
            channel.send(message)                               #

            # quit                                              #
            done.set()                                          #

    # receive offer                                             #
    print('-- Please enter remote offer --')                    #
    offer_json = json.loads(input())                            #
    await pc.setRemoteDescription(RTCSessionDescription(        #
        sdp=offer_json['sdp'],                                  #
        type=offer_json['type']))                               #
    print()                                                     #

    # send answer                                               #
    await pc.setLocalDescription(await pc.createAnswer())       #
    answer = pc.localDescription                                #
    print('-- Your answer --')                                  #
    print(json.dumps({                                          #
        'sdp': answer.sdp,                                      #
        'type': answer.type                                     #
    }))                                                         #
    print()                                                     #

    await done.wait()                                           #


async def run_offer(pc):                                        #
    done = asyncio.Event()                                      #

    channel = pc.createDataChannel('chat')                      #
    channel_log(channel, '-', 'created by local party')         #
    channel_watch(channel)                                      #

    @channel.on('message')                                      #
    def on_message(message):                                    #
        # quit                                                  #
        done.set()                                              #

    # send offer                                                #
    await pc.setLocalDescription(await pc.createOffer())        #
    offer = pc.localDescription                                 #
    print('-- Your offer --')                                   #
    print(json.dumps({                                          #
        'sdp': offer.sdp,                                       #
        'type': offer.type                                      #
    }))                                                         #
    print()                                                     #

    # receive answer                                            #
    print('-- Please enter remote answer --')                   #
    answer_json = json.loads(input())                           #
    await pc.setRemoteDescription(RTCSessionDescription(        #
        sdp=answer_json['sdp'],                                 #
        type=answer_json['type']))                              #
    print()                                                     #

    # send message                                              #
    message = 'ping'                                            #
    channel_log(channel, '>', message)                          #
    channel.send(message)                                       #

    await done.wait()                                           #

def doclient():
    d = 'command line chff client'
    p = argparse.ArgumentParser(description=d)
    p.add_argument('-i', action='store',
                    dest='urli',
                    help='URL of introduction server')
    p.add_argument('role', choices=['init', 'resp'])
    p.add_argument('--quiet', '-q')
    p.add_argument('--debug', '-d')
    a = p.parse_args()

    logging.basicConfig(level=logging.INFO)
    if a.quiet:
        logging.basicConfig(level=logging.ERROR)
    if a.debug:
        logging.basicConfig(level=logging.DEBUG)

    pc = create_pc()                                            #

    if a.urli !='None':
        print(a.urli)
    else:
        print('need a URL for introductions')
        a.role = 'abort'

    if a.role != 'abort':
      if a.role == 'init':
          coro = run_offer(pc)                                  #
      else: 
        coro = run_answer(pc)                                   #
    

      # run event loop                                            #
      loop = asyncio.get_event_loop()                             #
      try:                                                        #
          loop.run_until_complete(coro)                           #
      except KeyboardInterrupt:                                   #
          pass                                                    #
      finally:                                                    #
          loop.run_until_complete(pc.close())                     #
