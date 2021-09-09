#
# This file is part of LiteX.
#
# Copyright (c) 2019 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

import unittest
import random

from migen import *

from litex.soc.interconnect.stream import *
from litex.soc.interconnect.packet import *

from .test_stream import StreamPacket, stream_inserter, stream_collector, compare_packets

packet_header_length = 31
packet_header_fields = {
    "field_8b"  : HeaderField(0,  0,   8),
    "field_16b" : HeaderField(1,  0,  16),
    "field_32b" : HeaderField(3,  0,  32),
    "field_64b" : HeaderField(7,  0,  64),
    "field_128b": HeaderField(15, 0, 128),
}
packet_header = Header(
    fields           = packet_header_fields,
    length           = packet_header_length,
    swap_field_bytes = True)

def packet_description(dw):
    param_layout = packet_header.get_layout()
    payload_layout = [("data", dw)]
    return EndpointDescription(payload_layout, param_layout)

def raw_description(dw):
    payload_layout = [("data", dw)]
    return EndpointDescription(payload_layout)



class TestPacket(unittest.TestCase):
    def loopback_test(self, dw, seed=42):
        prng = random.Random(seed)
        # Prepare packets
        npackets = 8
        packets  = []
        for n in range(npackets):
            header               = {}
            header["field_8b"]   = prng.randrange(2**8)
            header["field_16b"]  = prng.randrange(2**16)
            header["field_32b"]  = prng.randrange(2**32)
            header["field_64b"]  = prng.randrange(2**64)
            header["field_128b"] = prng.randrange(2**128)
            datas = [prng.randrange(2**8) for _ in range(prng.randrange(dw - 1) + 1)]
            packets.append(StreamPacket(datas, header))

        class DUT(Module):
            def __init__(self):
                self.submodules.packetizer = \
                    Packetizer(packet_description(dw), raw_description(dw), packet_header)
                self.submodules.depacketizer = \
                    Depacketizer(raw_description(dw), packet_description(dw), packet_header)
                self.comb += self.packetizer.source.connect(self.depacketizer.sink)
                self.sink, self.source = self.packetizer.sink, self.depacketizer.source

        dut = DUT()
        recvd_packets = []
        run_simulation(
            dut,
            [
                stream_inserter(
                    dut.sink,
                    src=packets,
                    seed=seed,
                    valid_rand=50,
                ),
                stream_collector(
                    dut.source,
                    dest=recvd_packets,
                    expect_npackets=npackets,
                    seed=seed,
                    ready_rand=50,
                ),
            ],
        )
        self.assertTrue(compare_packets(packets, recvd_packets))

    def test_8bit_loopback(self):
        self.loopback_test(dw=8)

    # def test_32bit_loopback(self):
    #     self.loopback_test(dw=32)

    # def test_64bit_loopback(self):
    #     self.loopback_test(dw=64)

    # def test_128bit_loopback(self):
    #     self.loopback_test(dw=128)
