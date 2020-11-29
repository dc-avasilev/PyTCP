#!/usr/bin/env python3

############################################################################
#                                                                          #
#  PyTCP - Python TCP/IP stack                                             #
#  Copyright (C) 2020  Sebastian Majewski                                  #
#                                                                          #
#  This program is free software: you can redistribute it and/or modify    #
#  it under the terms of the GNU General Public License as published by    #
#  the Free Software Foundation, either version 3 of the License, or       #
#  (at your option) any later version.                                     #
#                                                                          #
#  This program is distributed in the hope that it will be useful,         #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of          #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the           #
#  GNU General Public License for more details.                            #
#                                                                          #
#  You should have received a copy of the GNU General Public License       #
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.  #
#                                                                          #
#  Author's email: ccie18643@gmail.com                                     #
#  Github repository: https://github.com/ccie18643/PyTCP                   #
#                                                                          #
############################################################################

##############################################################################################
#                                                                                            #
#  This program is a work in progress and it changes on daily basis due to new features      #
#  being implemented, changes being made to already implemented features, bug fixes, etc.    #
#  Therefore if the current version is not working as expected try to clone it again the     #
#  next day or shoot me an email describing the problem. Any input is appreciated. Also      #
#  keep in mind that some features may be implemented only partially (as needed for stack    #
#  operation) or they may be implemented in sub-optimal or not 100% RFC compliant way (due   #
#  to lack of time) or last but not least they may contain bug(s) that i didn't notice yet.  #
#                                                                                            #
##############################################################################################


#
# ps_icmpv4.py - protocol support libary for ICMPv4
#


import struct

import inet_cksum
from tracker import Tracker

# Echo reply message (0/0)

# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |     Type      |     Code      |           Checksum            |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |              Id               |              Seq              |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# ~                             Data                              ~
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+


# Destination Unreachable message (3/[0-3, 5-15])

# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |     Type      |     Code      |           Checksum            |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |              Id               |              Seq              |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |                           Reserved                            |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# ~                             Data                              ~
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+


# Destination Unreachable message (3/4)

# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |     Type      |     Code      |           Checksum            |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |              Id               |              Seq              |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |           Reserved            |          Link MTU / 0         |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# ~                             Data                              ~
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+


# Echo Request message (8/0)

# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |     Type      |     Code      |           Checksum            |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |              Id               |              Seq              |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# ~                             Data                              ~
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+


ICMP4_ECHOREPLY = 0
ICMP4_UNREACHABLE = 3
ICMP4_UNREACHABLE_NET = 0
ICMP4_UNREACHABLE_HOST = 1
ICMP4_UNREACHABLE_PROTOCOL = 2
ICMP4_UNREACHABLE_PORT = 3
ICMP4_UNREACHABLE_FAGMENTATION = 4
ICMP4_UNREACHABLE_SOURCE_ROUTE_FAILED = 5
ICMP4_ECHOREQUEST = 8


class Icmp4Packet:
    """ ICMPv4 packet support class """

    protocol = "ICMPv4"

    def __init__(
        self,
        parent_packet=None,
        icmpv4_type=None,
        icmpv4_code=0,
        icmpv4_ec_id=None,
        icmpv4_ec_seq=None,
        icmpv4_ec_raw_data=b"",
        icmpv4_un_raw_data=b"",
        echo_tracker=None,
    ):
        """ Class constructor """

        # Packet parsing
        if parent_packet:
            self.tracker = parent_packet.tracker

            raw_packet = parent_packet.raw_data

            self.icmpv4_type = raw_packet[0]
            self.icmpv4_code = raw_packet[1]
            self.icmpv4_cksum = struct.unpack("!H", raw_packet[2:4])[0]

            if self.icmpv4_type == ICMP4_ECHOREPLY:
                self.icmpv4_ec_id = struct.unpack("!H", raw_packet[4:6])[0]
                self.icmpv4_ec_seq = struct.unpack("!H", raw_packet[6:8])[0]
                self.icmpv4_ec_raw_data = raw_packet[8:]
                return

            if self.icmpv4_type == ICMP4_UNREACHABLE:
                self.icmpv4_un_reserved = struct.unpack("!L", raw_packet[4:6])[0]
                self.icmpv4_un_raw_data = raw_packet[8:]
                return

            if self.icmpv4_type == ICMP4_ECHOREQUEST:
                self.icmpv4_ec_id = struct.unpack("!H", raw_packet[4:6])[0]
                self.icmpv4_ec_seq = struct.unpack("!H", raw_packet[6:8])[0]
                self.icmpv4_ec_raw_data = raw_packet[8:]
                return

            self.unknown_message = raw_packet[4:]

        # Packet building
        else:
            self.tracker = Tracker("TX", echo_tracker)

            self.icmpv4_type = icmpv4_type
            self.icmpv4_code = icmpv4_code
            self.icmpv4_cksum = 0

            if self.icmpv4_type == ICMP4_ECHOREPLY and self.icmpv4_code == 0:
                self.icmpv4_ec_id = icmpv4_ec_id
                self.icmpv4_ec_seq = icmpv4_ec_seq
                self.icmpv4_ec_raw_data = icmpv4_ec_raw_data
                return

            if self.icmpv4_type == ICMP4_UNREACHABLE and self.icmpv4_code == ICMP4_UNREACHABLE_PORT:
                self.icmpv4_un_reserved = 0
                self.icmpv4_un_raw_data = icmpv4_un_raw_data[:520]
                return

            if self.icmpv4_type == ICMP4_ECHOREQUEST and self.icmpv4_code == 0:
                self.icmpv4_ec_id = icmpv4_ec_id
                self.icmpv4_ec_seq = icmpv4_ec_seq
                self.icmpv4_ec_raw_data = icmpv4_ec_raw_data
                return

    def __str__(self):
        """ Short packet log string """

        log = f"ICMPv4 type {self.icmpv4_type}, code {self.icmpv4_code}"

        if self.icmpv4_type == ICMP4_ECHOREPLY:
            log += f", id {self.icmpv4_ec_id}, seq {self.icmpv4_ec_seq}"

        if self.icmpv4_type == ICMP4_UNREACHABLE and self.icmpv4_code == ICMP4_UNREACHABLE_PORT:
            pass

        if self.icmpv4_type == ICMP4_ECHOREQUEST:
            log += f", id {self.icmpv4_ec_id}, seq {self.icmpv4_ec_seq}"

        return log

    def __len__(self):
        """ Length of the packet """

        return len(self.raw_packet)

    @property
    def raw_packet(self):
        """ Get packet in raw format """

        if self.icmpv4_type == ICMP4_ECHOREPLY:
            return (
                struct.pack("! BBH HH", self.icmpv4_type, self.icmpv4_code, self.icmpv4_cksum, self.icmpv4_ec_id, self.icmpv4_ec_seq) + self.icmpv4_ec_raw_data
            )

        if self.icmpv4_type == ICMP4_UNREACHABLE and self.icmpv4_code == ICMP4_UNREACHABLE_PORT:
            return struct.pack("! BBH L", self.icmpv4_type, self.icmpv4_code, self.icmpv4_cksum, self.icmpv4_un_reserved) + self.icmpv4_un_raw_data

        if self.icmpv4_type == ICMP4_ECHOREQUEST:
            return (
                struct.pack("! BBH HH", self.icmpv4_type, self.icmpv4_code, self.icmpv4_cksum, self.icmpv4_ec_id, self.icmpv4_ec_seq) + self.icmpv4_ec_raw_data
            )

        return struct.pack("! BBH", self.icmpv4_type, self.icmpv4_code, self.icmpv4_cksum) + self.unknown_message

    def get_raw_packet(self):
        """ Get packet in raw format ready to be processed by lower level protocol """

        self.icmpv4_cksum = inet_cksum.compute_cksum(self.raw_packet)

        return self.raw_packet

    def validate_cksum(self):
        """ Validate packet checksum """

        return not bool(inet_cksum.compute_cksum(self.raw_packet))
